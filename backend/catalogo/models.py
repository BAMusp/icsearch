from django.db import models


class TabelaAuxiliar(models.Model):
    """Campos comuns às tabelas auxiliares. Abstrata: não gera tabela."""

    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Curso(TabelaAuxiliar):
    """Curso de graduação do aluno (ex.: Engenharia Mecatrônica)."""

    id_curso = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "curso"


class GrandeArea(TabelaAuxiliar):
    """Grande área do conhecimento de um projeto (ex.: Robótica)."""

    id_grande_area = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "grande_area"
        verbose_name = "grande área"
        verbose_name_plural = "grandes áreas"


class TipoOportunidade(TabelaAuxiliar):
    """Natureza da vaga (ex.: Iniciação Científica, TCC, Voluntário)."""

    id_tipo_oportunidade = models.AutoField(primary_key=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "tipo_oportunidade"
        verbose_name = "tipo de oportunidade"
        verbose_name_plural = "tipos de oportunidade"


class AgenciaFomento(TabelaAuxiliar):
    """Quem financia a pesquisa ou a bolsa (ex.: FAPESP, CNPq).

    A ausência de agência é representada por FK nula em Projeto e em Vaga,
    nunca por um valor "Sem bolsa" nesta tabela.
    """

    id_agencia_fomento = models.AutoField(primary_key=True)
    sigla = models.CharField(max_length=20, unique=True)

    class Meta(TabelaAuxiliar.Meta):
        db_table = "agencia_fomento"
        verbose_name = "agência de fomento"
        verbose_name_plural = "agências de fomento"
        ordering = ["sigla"]

    def __str__(self):
        return self.sigla

# Create your models here.
