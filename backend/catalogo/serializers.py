from datetime import date

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import (
    AgenciaFomento, Aluno, Curso, Departamento, Docente, GrandeArea,
    Laboratorio, TipoOportunidade, Usuario,
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


DOMINIO_USP = "@usp.br"


class CadastroBaseSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, style={"input_type": "password"})
    numero_usp = serializers.RegexField(r"^\d{1,12}$", max_length=12)

    perfil_model = None

    def validate_email(self, valor):
        valor = valor.strip().lower()
        if not valor.endswith(DOMINIO_USP):
            raise serializers.ValidationError("Use o email institucional (@usp.br).")
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError("Ja existe um cadastro com este email.")
        return valor

    def validate_numero_usp(self, valor):
        if self.perfil_model.objects.filter(numero_usp=valor).exists():
            raise serializers.ValidationError("Ja existe um cadastro com este numero USP.")
        return valor

    def validate(self, dados):
        usuario = Usuario(email=dados["email"], nome=dados["nome"])
        try:
            validate_password(dados["senha"], usuario)
        except Exception as erro:
            raise serializers.ValidationError({"senha": list(erro.messages)})
        return dados

    def criar_usuario(self, dados):
        return Usuario.objects.create_user(
            email=dados.pop("email"), nome=dados.pop("nome"), password=dados.pop("senha"),
        )


class CadastroAlunoSerializer(CadastroBaseSerializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.filter(ativo=True))
    ano_ingresso = serializers.IntegerField()

    perfil_model = Aluno

    def validate_ano_ingresso(self, valor):
        if not 1950 <= valor <= date.today().year:
            raise serializers.ValidationError("Ano de ingresso invalido.")
        return valor

    @transaction.atomic
    def create(self, dados):
        usuario = self.criar_usuario(dados)
        return Aluno.objects.create(usuario=usuario, **dados)


class CadastroDocenteSerializer(CadastroBaseSerializer):
    departamento = serializers.PrimaryKeyRelatedField(queryset=Departamento.objects.filter(ativo=True))
    url_lattes = serializers.URLField(required=False, allow_blank=True)

    perfil_model = Docente

    @transaction.atomic
    def create(self, dados):
        usuario = self.criar_usuario(dados)
        return Docente.objects.create(usuario=usuario, **dados)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, dados):
        usuario = authenticate(
            self.context.get("request"),
            email=dados["email"].strip().lower(),
            password=dados["senha"],
        )
        if usuario is None:
            raise serializers.ValidationError("Email ou senha incorretos.")
        dados["usuario"] = usuario
        return dados


class AlunoPerfilSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)

    class Meta:
        model = Aluno
        fields = ["id_aluno", "numero_usp", "curso", "ano_ingresso"]


class DocentePerfilSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer(read_only=True)

    class Meta:
        model = Docente
        fields = ["id_docente", "numero_usp", "departamento", "url_lattes"]


class UsuarioSerializer(serializers.ModelSerializer):
    perfil = serializers.SerializerMethodField()
    aluno = serializers.SerializerMethodField()
    docente = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id_usuario", "email", "nome", "perfil", "aluno", "docente"]

    def get_perfil(self, usuario):
        if hasattr(usuario, "aluno"):
            return "aluno"
        if hasattr(usuario, "docente"):
            return "docente"
        if usuario.is_staff:
            return "admin"
        return None

    def get_aluno(self, usuario):
        if hasattr(usuario, "aluno"):
            return AlunoPerfilSerializer(usuario.aluno).data
        return None

    def get_docente(self, usuario):
        if hasattr(usuario, "docente"):
            return DocentePerfilSerializer(usuario.docente).data
        return None