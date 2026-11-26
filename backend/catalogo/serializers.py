from rest_framework import serializers

from .models import (
    AgenciaFomento, Curso, Departamento, GrandeArea, Laboratorio,
    TipoOportunidade,
)


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ["id_curso", "nome", "ativo"]


class GrandeAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrandeArea
        fields = ["id_grande_area", "nome", "ativo"]


class TipoOportunidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoOportunidade
        fields = ["id_tipo_oportunidade", "nome", "ativo"]


class AgenciaFomentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgenciaFomento
        fields = ["id_agencia_fomento", "sigla", "nome", "ativo"]


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ["id_departamento", "sigla", "nome", "ativo"]


class LaboratorioSerializer(serializers.ModelSerializer):
    departamento_sigla = serializers.CharField(source="departamento.sigla", read_only=True)

    class Meta:
        model = Laboratorio
        fields = ["id_laboratorio", "sigla", "nome", "departamento", "departamento_sigla", "ativo"]