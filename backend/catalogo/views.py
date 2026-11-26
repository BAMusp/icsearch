from django.contrib.auth.models import update_last_login
from django.db.models import Exists, F, OuterRef, Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio, Projeto,
    ProjetoGrandeArea, ProjetoPalavraChave, TipoOportunidade, Vaga,
    normalizar_termo,
)
from .permissions import (
    LeituraLivreEscritaAdmin, LeituraLivreEscritaDocenteDono, docente_do_usuario,
)
from .serializers import (
    AgenciaFomentoSerializer, CadastroAlunoSerializer, CadastroDocenteSerializer,
    CursoSerializer, DepartamentoSerializer, GrandeAreaSerializer,
    LaboratorioSerializer, LoginSerializer, ProjetoSerializer,
    TipoOportunidadeSerializer, UsuarioSerializer, VagaSerializer,
)


class TabelaAuxiliarViewSet(viewsets.ModelViewSet):
    permission_classes = [LeituraLivreEscritaAdmin]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(ativo=True)
        return queryset


class CursoViewSet(TabelaAuxiliarViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer


class GrandeAreaViewSet(TabelaAuxiliarViewSet):
    queryset = GrandeArea.objects.all()
    serializer_class = GrandeAreaSerializer


class TipoOportunidadeViewSet(TabelaAuxiliarViewSet):
    queryset = TipoOportunidade.objects.all()
    serializer_class = TipoOportunidadeSerializer


class AgenciaFomentoViewSet(TabelaAuxiliarViewSet):
    queryset = AgenciaFomento.objects.all()
    serializer_class = AgenciaFomentoSerializer


class DepartamentoViewSet(TabelaAuxiliarViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer


class LaboratorioViewSet(TabelaAuxiliarViewSet):
    queryset = Laboratorio.objects.select_related("departamento")
    serializer_class = LaboratorioSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        departamento = self.request.query_params.get("departamento")
        if departamento:
            queryset = queryset.filter(departamento_id=departamento)
        return queryset


def resposta_com_token(usuario, status_http=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=usuario)
    return Response(
        {"token": token.key, "usuario": UsuarioSerializer(usuario).data},
        status=status_http,
    )


class CadastroAlunoView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CadastroAlunoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        aluno = serializer.save()
        return resposta_com_token(aluno.usuario, status.HTTP_201_CREATED)


class CadastroDocenteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CadastroDocenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        docente = serializer.save()
        return resposta_com_token(docente.usuario, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["usuario"]
        update_last_login(None, usuario)
        return resposta_com_token(usuario)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)



class DocenteDonoViewSet(viewsets.ModelViewSet):
    permission_classes = [LeituraLivreEscritaDocenteDono]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto["docente"] = docente_do_usuario(self.request.user)
        return contexto

    def somente_meus(self):
        return self.request.query_params.get("meus") == "1"


class ProjetoViewSet(DocenteDonoViewSet):
    serializer_class = ProjetoSerializer

    def docente_dono(self, projeto):
        return projeto.docente

    def get_queryset(self):
        queryset = Projeto.objects.select_related(
            "docente__usuario", "docente__departamento", "laboratorio", "agencia_fomento",
        ).prefetch_related(
            "grandes_areas", "palavras_chave",
            Prefetch("vagas", queryset=Vaga.objects.com_vagas_abertas().select_related(
                "tipo_oportunidade", "agencia_fomento",
            )),
        )
        docente = docente_do_usuario(self.request.user)
        if self.somente_meus():
            return queryset.filter(docente=docente) if docente else queryset.none()
        if docente is not None:
            return queryset.filter(Q(ativo=True) | Q(docente=docente))
        return queryset.filter(ativo=True)


class VagaViewSet(DocenteDonoViewSet):
    serializer_class = VagaSerializer

    def docente_dono(self, vaga):
        return vaga.projeto.docente

    def get_queryset(self):
        queryset = Vaga.objects.com_vagas_abertas().select_related(
            "projeto__docente", "tipo_oportunidade", "agencia_fomento",
        )
        docente = docente_do_usuario(self.request.user)
        if self.somente_meus():
            return queryset.filter(projeto__docente=docente) if docente else queryset.none()
        publicas = Q(ativa=True, projeto__ativo=True)
        if docente is not None:
            return queryset.filter(publicas | Q(projeto__docente=docente))
        return queryset.filter(publicas)



class PaginacaoBusca(PageNumberPagination):
    page_size = 10
    page_size_query_param = "tamanho"
    max_page_size = 50


def parametro_inteiro(params, nome):
    valor = params.get(nome)
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except ValueError:
        raise ValidationError({nome: "Informe um numero inteiro."})


class BuscaView(ListAPIView):
    serializer_class = ProjetoSerializer
    permission_classes = [AllowAny]
    pagination_class = PaginacaoBusca

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto["docente"] = docente_do_usuario(self.request.user)
        return contexto

    def get_queryset(self):
        params = self.request.query_params
        queryset = Projeto.objects.filter(ativo=True).select_related(
            "docente__usuario", "docente__departamento", "laboratorio", "agencia_fomento",
        ).prefetch_related(
            "grandes_areas", "palavras_chave",
            Prefetch("vagas", queryset=Vaga.objects.com_vagas_abertas().select_related(
                "tipo_oportunidade", "agencia_fomento",
            )),
        )

        grande_area = parametro_inteiro(params, "grande_area")
        if grande_area is not None:
            queryset = queryset.filter(
                Exists(ProjetoGrandeArea.objects.filter(projeto=OuterRef("pk"), grande_area_id=grande_area))
            )

        departamento = parametro_inteiro(params, "departamento")
        if departamento is not None:
            queryset = queryset.filter(docente__departamento_id=departamento)

        vagas = Vaga.objects.com_vagas_abertas().filter(projeto=OuterRef("pk"), ativa=True)
        filtra_vagas = False
        tipo = parametro_inteiro(params, "tipo_oportunidade")
        if tipo is not None:
            vagas = vagas.filter(tipo_oportunidade_id=tipo)
            filtra_vagas = True
        agencia = parametro_inteiro(params, "agencia_fomento")
        if agencia is not None:
            vagas = vagas.filter(agencia_fomento_id=agencia)
            filtra_vagas = True
        if params.get("com_bolsa") == "1":
            vagas = vagas.filter(agencia_fomento__isnull=False)
            filtra_vagas = True
        if params.get("vaga_aberta") == "1":
            vagas = vagas.filter(quantidade__gt=F("total_aceitas"))
            filtra_vagas = True
        if filtra_vagas:
            queryset = queryset.filter(Exists(vagas))

        for digitada in params.get("q", "").split():
            normalizada = normalizar_termo(digitada)
            condicao = Exists(ProjetoPalavraChave.objects.filter(
                projeto=OuterRef("pk"),
                palavra_chave__termo_normalizado__contains=normalizada,
            ))
            for forma in {digitada, normalizada}:
                condicao |= (
                    Q(titulo__icontains=forma)
                    | Q(resumo__icontains=forma)
                    | Q(docente__usuario__nome__icontains=forma)
                )
            queryset = queryset.filter(condicao)

        return queryset.order_by("-data_cadastro", "-id_projeto")