from datetime import date

from django.contrib.auth.models import update_last_login
from django.db import transaction
from django.db.models import (
    Case, CharField, Count, Exists, F, OuterRef, Prefetch, Q, Value, When,
)
from django.db.models.functions import Cast, Concat, ExtractYear
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio,
    ManifestacaoInteresse, Projeto, ProjetoGrandeArea, ProjetoPalavraChave,
    TipoOportunidade, Vaga, normalizar_termo,
)
from .permissions import (
    LeituraLivreEscritaAdmin, LeituraLivreEscritaDocenteDono, aluno_do_usuario,
    docente_do_usuario,
)
from .serializers import (
    AgenciaFomentoSerializer, CadastroAlunoSerializer, CadastroDocenteSerializer,
    CursoSerializer, DepartamentoSerializer, GrandeAreaSerializer,
    LaboratorioSerializer, LoginSerializer, ManifestacaoSerializer,
    ProjetoSerializer, TipoOportunidadeSerializer, UsuarioSerializer,
    VagaSerializer,
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



class ManifestacaoViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ManifestacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ManifestacaoInteresse.objects.select_related(
            "aluno__usuario", "aluno__curso",
            "vaga__projeto__docente__usuario", "vaga__tipo_oportunidade",
        )
        usuario = self.request.user
        aluno = aluno_do_usuario(usuario)
        docente = docente_do_usuario(usuario)
        if aluno is not None:
            queryset = queryset.filter(aluno=aluno)
        elif docente is not None:
            queryset = queryset.filter(vaga__projeto__docente=docente)
        elif not usuario.is_staff:
            return queryset.none()

        params = self.request.query_params
        vaga = parametro_inteiro(params, "vaga")
        if vaga is not None:
            queryset = queryset.filter(vaga_id=vaga)
        projeto = parametro_inteiro(params, "projeto")
        if projeto is not None:
            queryset = queryset.filter(vaga__projeto_id=projeto)
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        return queryset

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto["aluno"] = aluno_do_usuario(self.request.user)
        return contexto

    def create(self, request, *args, **kwargs):
        if aluno_do_usuario(request.user) is None:
            raise PermissionDenied("Apenas alunos podem manifestar interesse.")
        return super().create(request, *args, **kwargs)

    def responder(self, novo_status):
        manifestacao = self.get_object()
        if manifestacao.vaga.projeto.docente != docente_do_usuario(self.request.user):
            raise PermissionDenied("Apenas o docente responsavel pela vaga pode responder.")
        with transaction.atomic():
            vaga = Vaga.objects.select_for_update().get(pk=manifestacao.vaga_id)
            manifestacao = ManifestacaoInteresse.objects.select_for_update().get(pk=manifestacao.pk)
            if manifestacao.status != ManifestacaoInteresse.Status.PENDENTE:
                raise ValidationError({"status": "Esta manifestacao ja foi respondida."})
            if novo_status == ManifestacaoInteresse.Status.ACEITA and vaga.vagas_abertas <= 0:
                raise ValidationError({"vaga": "Nao ha mais vagas abertas."})
            manifestacao.status = novo_status
            manifestacao.data_resposta = timezone.now()
            manifestacao.save(update_fields=["status", "data_resposta"])
        manifestacao = self.get_queryset().get(pk=manifestacao.pk)
        return Response(self.get_serializer(manifestacao).data)

    @action(detail=True, methods=["post"])
    def aceitar(self, request, pk=None):
        return self.responder(ManifestacaoInteresse.Status.ACEITA)

    @action(detail=True, methods=["post"])
    def recusar(self, request, pk=None):
        return self.responder(ManifestacaoInteresse.Status.RECUSADA)



SEMESTRE = Concat(
    Cast(ExtractYear("data_manifestacao"), CharField()),
    Value("/"),
    Case(When(data_manifestacao__month__lte=6, then=Value("1")), default=Value("2")),
    output_field=CharField(),
)

DIMENSOES_PAINEL = {
    "grande_area": ("Grande area", F("vaga__projeto__grandes_areas__nome"), "Sem area"),
    "departamento": ("Departamento", F("vaga__projeto__docente__departamento__sigla"), "Sem departamento"),
    "agencia_fomento": ("Agencia de fomento", F("vaga__agencia_fomento__sigla"), "Sem bolsa"),
    "tipo_oportunidade": ("Tipo de oportunidade", F("vaga__tipo_oportunidade__nome"), "Sem tipo"),
    "periodo": ("Periodo", SEMESTRE, "Sem periodo"),
    "status": ("Status", F("status"), "Sem status"),
}


def data_do_parametro(params, nome):
    valor = params.get(nome)
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ValidationError({nome: "Use o formato AAAA-MM-DD."})


class PainelDemandaView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        params = request.query_params
        linhas = params.get("linhas", "grande_area")
        colunas = params.get("colunas", "periodo")
        for nome, valor in (("linhas", linhas), ("colunas", colunas)):
            if valor not in DIMENSOES_PAINEL:
                raise ValidationError({nome: f"Use uma destas: {', '.join(DIMENSOES_PAINEL)}."})
        if linhas == colunas:
            raise ValidationError({"colunas": "Escolha uma dimensao diferente das linhas."})

        manifestacoes = ManifestacaoInteresse.objects.all()
        inicio = data_do_parametro(params, "de")
        if inicio is not None:
            manifestacoes = manifestacoes.filter(data_manifestacao__date__gte=inicio)
        fim = data_do_parametro(params, "ate")
        if fim is not None:
            manifestacoes = manifestacoes.filter(data_manifestacao__date__lte=fim)

        _, expr_linha, vazio_linha = DIMENSOES_PAINEL[linhas]
        _, expr_coluna, vazio_coluna = DIMENSOES_PAINEL[colunas]
        anotadas = manifestacoes.annotate(linha=expr_linha, coluna=expr_coluna)

        def contar(*campos):
            return anotadas.values(*campos).annotate(
                total=Count("id_manifestacao", distinct=True),
            ).order_by()

        def rotulo(valor, vazio):
            return vazio if valor is None else valor

        celulas = {}
        for item in contar("linha", "coluna"):
            linha = rotulo(item["linha"], vazio_linha)
            coluna = rotulo(item["coluna"], vazio_coluna)
            celulas.setdefault(linha, {})[coluna] = item["total"]
        total_linha = {rotulo(i["linha"], vazio_linha): i["total"] for i in contar("linha")}
        total_coluna = {rotulo(i["coluna"], vazio_coluna): i["total"] for i in contar("coluna")}

        return Response({
            "linhas": {"dimensao": linhas, "titulo": DIMENSOES_PAINEL[linhas][0], "valores": sorted(total_linha)},
            "colunas": {"dimensao": colunas, "titulo": DIMENSOES_PAINEL[colunas][0], "valores": sorted(total_coluna)},
            "celulas": celulas,
            "total_linha": total_linha,
            "total_coluna": total_coluna,
            "total_geral": manifestacoes.count(),
            "dimensoes": {chave: valor[0] for chave, valor in DIMENSOES_PAINEL.items()},
        })