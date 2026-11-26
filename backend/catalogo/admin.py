from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AgenciaFomento, Aluno, Curso, Departamento, Docente, GrandeArea,
    Laboratorio, TipoOportunidade, Usuario, Vinculo,
)


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


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ["sigla", "nome", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["sigla", "nome"]


class VinculoInline(admin.TabularInline):
    model = Vinculo
    extra = 0


@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ["nome", "sigla", "departamento", "ativo"]
    list_filter = ["departamento", "ativo"]
    search_fields = ["nome", "sigla"]
    inlines = [VinculoInline]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["nome"]
    list_display = ["email", "nome", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["email", "nome"]
    readonly_fields = ["last_login", "data_cadastro"]
    fieldsets = [
        (None, {"fields": ["email", "nome", "password"]}),
        ("Permissoes", {"fields": ["is_active", "is_staff", "is_superuser"]}),
        ("Datas", {"fields": ["last_login", "data_cadastro"]}),
    ]
    add_fieldsets = [
        (None, {
            "classes": ["wide"],
            "fields": ["email", "nome", "password1", "password2"],
        }),
    ]


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "numero_usp", "curso", "ano_ingresso"]
    list_filter = ["curso", "ano_ingresso"]
    search_fields = ["usuario__nome", "numero_usp"]


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ["usuario", "numero_usp", "departamento"]
    list_filter = ["departamento"]
    search_fields = ["usuario__nome", "numero_usp"]
    inlines = [VinculoInline]