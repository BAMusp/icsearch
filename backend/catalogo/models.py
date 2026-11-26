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