from django.contrib.auth.models import update_last_login
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio,
    TipoOportunidade,
)
from .permissions import LeituraLivreEscritaAdmin
from .serializers import (
    AgenciaFomentoSerializer, CadastroAlunoSerializer, CadastroDocenteSerializer,
    CursoSerializer, DepartamentoSerializer, GrandeAreaSerializer,
    LaboratorioSerializer, LoginSerializer, TipoOportunidadeSerializer,
    UsuarioSerializer,
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