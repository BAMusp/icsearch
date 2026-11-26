import unicodedata
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q



class TabelaAuxiliar(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Curso(TabelaAuxiliar):
    id_curso = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "curso"


class GrandeArea(TabelaAuxiliar):
    id_grande_area = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "grande_area"
        verbose_name = "grande area"
        verbose_name_plural = "grandes areas"


class TipoOportunidade(TabelaAuxiliar):
    id_tipo_oportunidade = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "tipo_oportunidade"
        verbose_name = "tipo de oportunidade"
        verbose_name_plural = "tipos de oportunidade"


class AgenciaFomento(TabelaAuxiliar):
    id_agencia_fomento = models.AutoField(primary_key=True)
    sigla = models.CharField(max_length=20, unique=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "agencia_fomento"
        verbose_name = "agencia de fomento"
        verbose_name_plural = "agencias de fomento"
        ordering = ["sigla"]

    def __str__(self):
        return self.sigla




class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    sigla = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "departamento"
        ordering = ["sigla"]

    def __str__(self):
        return self.sigla


class Laboratorio(models.Model):
    id_laboratorio = models.AutoField(primary_key=True)
    departamento = models.ForeignKey(
        Departamento, on_delete=models.PROTECT, db_column="id_departamento",
        related_name="laboratorios",
    )
    sigla = models.CharField(max_length=20, blank=True)
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "laboratorio"
        verbose_name = "laboratorio"
        ordering = ["nome"]

    def __str__(self):
        return self.sigla or self.nome




class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra):
        if not email:
            raise ValueError("O email e obrigatorio.")
        usuario = self.model(email=self.normalize_email(email), nome=nome, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nome, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, nome, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=150)
    password = models.CharField(max_length=128, db_column="senha_hash")
    last_login = models.DateTimeField(blank=True, null=True, db_column="ultimo_acesso")
    is_active = models.BooleanField(default=True, db_column="ativo")
    is_staff = models.BooleanField(default=False, db_column="administrador")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        db_table = "usuario"
        ordering = ["nome"]

    def __str__(self):
        return self.nome



class Aluno(models.Model):
    id_aluno = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario, on_delete=models.PROTECT, db_column="id_usuario",
        related_name="aluno",
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, db_column="id_curso",
        related_name="alunos",
    )
    numero_usp = models.CharField(max_length=12, unique=True)
    ano_ingresso = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "aluno"

    def __str__(self):
        return self.usuario.nome


class Docente(models.Model):
    id_docente = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario, on_delete=models.PROTECT, db_column="id_usuario",
        related_name="docente",
    )
    departamento = models.ForeignKey(
        Departamento, on_delete=models.PROTECT, db_column="id_departamento",
        related_name="docentes",
    )
    numero_usp = models.CharField(max_length=12, unique=True)
    url_lattes = models.URLField(blank=True)
    laboratorios = models.ManyToManyField(
        Laboratorio, through="Vinculo", related_name="docentes",
    )

    class Meta:
        db_table = "docente"

    def __str__(self):
        return self.usuario.nome

    @property
    def nome(self):
        return self.usuario.nome



class Vinculo(models.Model):
    id_vinculo = models.AutoField(primary_key=True)
    docente = models.ForeignKey(
        Docente, on_delete=models.PROTECT, db_column="id_docente",
        related_name="vinculos",
    )
    laboratorio = models.ForeignKey(
        Laboratorio, on_delete=models.PROTECT, db_column="id_laboratorio",
        related_name="vinculos",
    )
    responsavel = models.BooleanField(default=False)

    class Meta:
        db_table = "vinculo"
        constraints = [
            models.UniqueConstraint(
                fields=["docente", "laboratorio"],
                name="vinculo_docente_laboratorio_unico",
            ),
            models.UniqueConstraint(
                fields=["laboratorio"],
                condition=Q(responsavel=True),
                name="vinculo_um_responsavel_por_laboratorio",
            ),
        ]

    def __str__(self):
        return f"{self.docente} - {self.laboratorio}"
    

def normalizar_termo(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.lower().split())


class PalavraChave(models.Model):
    id_palavra_chave = models.AutoField(primary_key=True)
    termo = models.CharField(max_length=80)
    termo_normalizado = models.CharField(max_length=80, unique=True, editable=False)

    class Meta:
        db_table = "palavra_chave"
        verbose_name = "palavra-chave"
        verbose_name_plural = "palavras-chave"
        ordering = ["termo_normalizado"]

    def save(self, *args, **kwargs):
        self.termo = " ".join(self.termo.split())
        self.termo_normalizado = normalizar_termo(self.termo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.termo


class Projeto(models.Model):
    id_projeto = models.AutoField(primary_key=True)
    docente = models.ForeignKey(
        Docente, on_delete=models.PROTECT, db_column="id_docente",
        related_name="projetos",
    )
    laboratorio = models.ForeignKey(
        Laboratorio, on_delete=models.PROTECT, db_column="id_laboratorio",
        related_name="projetos", null=True, blank=True,
    )
    agencia_fomento = models.ForeignKey(
        AgenciaFomento, on_delete=models.PROTECT, db_column="id_agencia_fomento",
        related_name="projetos", null=True, blank=True,
    )
    titulo = models.CharField(max_length=200)
    resumo = models.TextField()
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    grandes_areas = models.ManyToManyField(
        GrandeArea, through="ProjetoGrandeArea", related_name="projetos",
    )
    palavras_chave = models.ManyToManyField(
        PalavraChave, through="ProjetoPalavraChave", related_name="projetos",
    )

    class Meta:
        db_table = "projeto"
        ordering = ["-data_cadastro"]
        constraints = [
            models.CheckConstraint(
                condition=Q(data_fim__isnull=True) | Q(data_fim__gte=models.F("data_inicio")),
                name="projeto_data_fim_depois_do_inicio",
            ),
        ]

    def __str__(self):
        return self.titulo

    @property
    def departamento(self):
        return self.docente.departamento


class ProjetoGrandeArea(models.Model):
    id_projeto_grande_area = models.AutoField(primary_key=True)
    projeto = models.ForeignKey(
        Projeto, on_delete=models.PROTECT, db_column="id_projeto",
    )
    grande_area = models.ForeignKey(
        GrandeArea, on_delete=models.PROTECT, db_column="id_grande_area",
    )

    class Meta:
        db_table = "projeto_grande_area"
        verbose_name = "grande area do projeto"
        verbose_name_plural = "grandes areas do projeto"
        constraints = [
            models.UniqueConstraint(
                fields=["projeto", "grande_area"],
                name="projeto_grande_area_unico",
            ),
        ]

    def __str__(self):
        return f"{self.projeto} - {self.grande_area}"


class ProjetoPalavraChave(models.Model):
    id_projeto_palavra_chave = models.AutoField(primary_key=True)
    projeto = models.ForeignKey(
        Projeto, on_delete=models.PROTECT, db_column="id_projeto",
    )
    palavra_chave = models.ForeignKey(
        PalavraChave, on_delete=models.PROTECT, db_column="id_palavra_chave",
    )

    class Meta:
        db_table = "projeto_palavra_chave"
        verbose_name = "palavra-chave do projeto"
        verbose_name_plural = "palavras-chave do projeto"
        constraints = [
            models.UniqueConstraint(
                fields=["projeto", "palavra_chave"],
                name="projeto_palavra_chave_unico",
            ),
        ]

    def __str__(self):
        return f"{self.projeto} - {self.palavra_chave}"


class Vaga(models.Model):
    id_vaga = models.AutoField(primary_key=True)
    projeto = models.ForeignKey(
        Projeto, on_delete=models.PROTECT, db_column="id_projeto",
        related_name="vagas",
    )
    tipo_oportunidade = models.ForeignKey(
        TipoOportunidade, on_delete=models.PROTECT, db_column="id_tipo_oportunidade",
        related_name="vagas",
    )
    agencia_fomento = models.ForeignKey(
        AgenciaFomento, on_delete=models.PROTECT, db_column="id_agencia_fomento",
        related_name="vagas", null=True, blank=True,
    )
    quantidade = models.PositiveSmallIntegerField()
    descricao = models.TextField(blank=True)
    data_limite = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vaga"
        ordering = ["-data_cadastro"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gte=1),
                name="vaga_quantidade_positiva",
            ),
        ]

    def __str__(self):
        return f"{self.tipo_oportunidade} - {self.projeto}"

    @property
    def vagas_abertas(self):
        aceitas = self.manifestacoes.filter(status=ManifestacaoInteresse.Status.ACEITA).count()
        return max(self.quantidade - aceitas, 0)


class ManifestacaoInteresse(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ACEITA = "aceita", "Aceita"
        RECUSADA = "recusada", "Recusada"

    id_manifestacao = models.AutoField(primary_key=True)
    aluno = models.ForeignKey(
        Aluno, on_delete=models.PROTECT, db_column="id_aluno",
        related_name="manifestacoes",
    )
    vaga = models.ForeignKey(
        Vaga, on_delete=models.PROTECT, db_column="id_vaga",
        related_name="manifestacoes",
    )
    mensagem = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    data_manifestacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "manifestacao_interesse"
        verbose_name = "manifestacao de interesse"
        verbose_name_plural = "manifestacoes de interesse"
        ordering = ["-data_manifestacao"]
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "vaga"],
                name="manifestacao_uma_por_aluno_e_vaga",
            ),
        ]

    def __str__(self):
        return f"{self.aluno} -> {self.vaga}"