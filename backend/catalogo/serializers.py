from datetime import date

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import (
    AgenciaFomento, Aluno, Curso, Departamento, Docente, GrandeArea,
    Laboratorio, PalavraChave, Projeto, TipoOportunidade, Usuario, Vaga,
    normalizar_termo,
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



class VagaSerializer(serializers.ModelSerializer):
    tipo_oportunidade_nome = serializers.CharField(source="tipo_oportunidade.nome", read_only=True)
    agencia_fomento_sigla = serializers.CharField(source="agencia_fomento.sigla", read_only=True, default=None)
    vagas_abertas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vaga
        fields = [
            "id_vaga", "projeto", "tipo_oportunidade", "tipo_oportunidade_nome",
            "agencia_fomento", "agencia_fomento_sigla", "quantidade", "vagas_abertas",
            "descricao", "data_limite", "ativa", "data_cadastro",
        ]
        read_only_fields = ["data_cadastro"]
        extra_kwargs = {
            "tipo_oportunidade": {"queryset": TipoOportunidade.objects.filter(ativo=True)},
            "agencia_fomento": {"queryset": AgenciaFomento.objects.filter(ativo=True)},
        }

    def get_fields(self):
        campos = super().get_fields()
        docente = self.context.get("docente")
        if docente is not None:
            campos["projeto"].queryset = Projeto.objects.filter(docente=docente)
        if self.instance is not None and not isinstance(self.instance, list):
            campos["projeto"].read_only = True
        return campos

    def validate_quantidade(self, valor):
        if valor < 1:
            raise serializers.ValidationError("A quantidade deve ser pelo menos 1.")
        if self.instance is not None:
            aceitas = self.instance.quantidade - self.instance.vagas_abertas
            if valor < aceitas:
                raise serializers.ValidationError(
                    f"Ja ha {aceitas} aluno(s) aceito(s); a quantidade nao pode ser menor."
                )
        return valor

    def validate_data_limite(self, valor):
        if valor is not None and valor < date.today():
            raise serializers.ValidationError("A data limite nao pode estar no passado.")
        return valor


class ProjetoSerializer(serializers.ModelSerializer):
    docente_nome = serializers.CharField(source="docente.nome", read_only=True)
    departamento = DepartamentoSerializer(read_only=True)
    laboratorio_nome = serializers.CharField(source="laboratorio.nome", read_only=True, default=None)
    agencia_fomento_sigla = serializers.CharField(source="agencia_fomento.sigla", read_only=True, default=None)
    grandes_areas = serializers.PrimaryKeyRelatedField(
        many=True, queryset=GrandeArea.objects.filter(ativo=True),
    )
    grandes_areas_nomes = serializers.SlugRelatedField(
        source="grandes_areas", slug_field="nome", many=True, read_only=True,
    )
    palavras_chave = serializers.ListField(
        child=serializers.CharField(max_length=80), required=False, write_only=True,
    )
    vagas = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = [
            "id_projeto", "titulo", "resumo", "data_inicio", "data_fim", "ativo",
            "docente", "docente_nome", "departamento",
            "laboratorio", "laboratorio_nome",
            "agencia_fomento", "agencia_fomento_sigla",
            "grandes_areas", "grandes_areas_nomes", "palavras_chave",
            "vagas", "data_cadastro",
        ]
        read_only_fields = ["docente", "data_cadastro"]
        extra_kwargs = {
            "agencia_fomento": {"queryset": AgenciaFomento.objects.filter(ativo=True)},
            "laboratorio": {"queryset": Laboratorio.objects.filter(ativo=True)},
        }

    def to_representation(self, projeto):
        dados = super().to_representation(projeto)
        dados["palavras_chave"] = [p.termo for p in projeto.palavras_chave.all()]
        return dados

    def get_vagas(self, projeto):
        vagas = projeto.vagas.all()
        if projeto.docente != self.context.get("docente"):
            vagas = [vaga for vaga in vagas if vaga.ativa]
        return VagaSerializer(vagas, many=True).data

    def validate_grandes_areas(self, valor):
        if not valor:
            raise serializers.ValidationError("Informe pelo menos uma grande area.")
        return valor

    def validate(self, dados):
        docente = self.context["docente"]
        laboratorio = dados.get("laboratorio")
        if laboratorio is not None and not docente.vinculos.filter(laboratorio=laboratorio).exists():
            raise serializers.ValidationError(
                {"laboratorio": "Voce nao tem vinculo com este laboratorio."}
            )
        inicio = dados.get("data_inicio", getattr(self.instance, "data_inicio", None))
        fim = dados.get("data_fim", getattr(self.instance, "data_fim", None))
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError(
                {"data_fim": "A data de fim nao pode ser anterior a data de inicio."}
            )
        return dados

    def salvar_relacoes(self, projeto, areas, termos):
        if areas is not None:
            projeto.grandes_areas.set(areas)
        if termos is not None:
            palavras = []
            for termo in termos:
                if not termo.strip():
                    continue
                palavra = PalavraChave.objects.filter(termo_normalizado=normalizar_termo(termo)).first()
                if palavra is None:
                    palavra = PalavraChave.objects.create(termo=termo)
                palavras.append(palavra)
            projeto.palavras_chave.set(palavras)

    @transaction.atomic
    def create(self, dados):
        areas = dados.pop("grandes_areas")
        termos = dados.pop("palavras_chave", [])
        projeto = Projeto.objects.create(docente=self.context["docente"], **dados)
        self.salvar_relacoes(projeto, areas, termos)
        return projeto

    @transaction.atomic
    def update(self, projeto, dados):
        areas = dados.pop("grandes_areas", None)
        termos = dados.pop("palavras_chave", None)
        projeto = super().update(projeto, dados)
        self.salvar_relacoes(projeto, areas, termos)
        return projeto