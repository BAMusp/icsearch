from django.contrib import admin

from .models import AgenciaFomento, Curso, GrandeArea, TipoOportunidade


@admin.register(Curso, GrandeArea, TipoOportunidade)
class TabelaAuxiliarAdmin(admin.ModelAdmin):
    list_display = ["nome", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]


@admin.register(AgenciaFomento)
class AgenciaFomentoAdmin(admin.ModelAdmin):
    list_display = ["sigla", "nome", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["sigla", "nome"]