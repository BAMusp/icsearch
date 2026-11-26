from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cursos", views.CursoViewSet)
router.register("grandes-areas", views.GrandeAreaViewSet)
router.register("tipos-oportunidade", views.TipoOportunidadeViewSet)
router.register("agencias-fomento", views.AgenciaFomentoViewSet)
router.register("departamentos", views.DepartamentoViewSet)
router.register("laboratorios", views.LaboratorioViewSet)
router.register("projetos", views.ProjetoViewSet, basename="projeto")
router.register("vagas", views.VagaViewSet, basename="vaga")

urlpatterns = [
    path("auth/cadastro/aluno/", views.CadastroAlunoView.as_view(), name="cadastro-aluno"),
    path("auth/cadastro/docente/", views.CadastroDocenteView.as_view(), name="cadastro-docente"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/eu/", views.EuView.as_view(), name="eu"),
] + router.urls