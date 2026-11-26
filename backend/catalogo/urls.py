from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cursos", views.CursoViewSet)
router.register("grandes-areas", views.GrandeAreaViewSet)
router.register("tipos-oportunidade", views.TipoOportunidadeViewSet)
router.register("agencias-fomento", views.AgenciaFomentoViewSet)
router.register("departamentos", views.DepartamentoViewSet)
router.register("laboratorios", views.LaboratorioViewSet)

urlpatterns = router.urls