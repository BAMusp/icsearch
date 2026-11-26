from django.contrib.auth.models import update_last_login
from django.db.models import Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio, Projeto,
    TipoOportunidade, Vaga,
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