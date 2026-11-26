from rest_framework import viewsets

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio,
    TipoOportunidade,
)
from .permissions import LeituraLivreEscritaAdmin
from .serializers import (
    AgenciaFomentoSerializer, CursoSerializer, DepartamentoSerializer,
    GrandeAreaSerializer, LaboratorioSerializer, TipoOportunidadeSerializer,
)


class TabelaAuxiliarViewSet(viewsets.ModelViewSet):
    permission_classes = [LeituraLivreEscritaAdmin]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
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

# Create your views here.
