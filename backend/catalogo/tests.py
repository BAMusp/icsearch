from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Curso, Departamento, Docente, Laboratorio, Usuario, Vinculo, Aluno


class BaseTeste(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pmr = Departamento.objects.create(sigla="PMR", nome="Engenharia Mecatronica")
        cls.lab = Laboratorio.objects.create(departamento=cls.pmr, nome="Laboratorio de Robotica")
        cls.curso = Curso.objects.create(nome="Engenharia Mecatronica")

    def criar_docente(self, email, nusp):
        usuario = Usuario.objects.create_user(email=email, nome=email, password="senha-forte-123")
        return Docente.objects.create(usuario=usuario, departamento=self.pmr, numero_usp=nusp)


class UsuarioTeste(BaseTeste):
    def test_login_por_email_com_senha_hash(self):
        usuario = Usuario.objects.create_user(email="a@usp.br", nome="Ana", password="senha-forte-123")
        self.assertTrue(usuario.check_password("senha-forte-123"))
        self.assertNotEqual(usuario.password, "senha-forte-123")

    def test_usuario_tem_no_maximo_um_perfil_de_aluno(self):
        usuario = Usuario.objects.create_user(email="a@usp.br", nome="Ana", password="x")
        Aluno.objects.create(usuario=usuario, curso=self.curso, numero_usp="1", ano_ingresso=2024)
        with self.assertRaises(IntegrityError):
            Aluno.objects.create(usuario=usuario, curso=self.curso, numero_usp="2", ano_ingresso=2024)


class VinculoTeste(BaseTeste):
    def test_docente_nao_se_vincula_duas_vezes_ao_mesmo_laboratorio(self):
        docente = self.criar_docente("d1@usp.br", "10")
        Vinculo.objects.create(docente=docente, laboratorio=self.lab)
        with self.assertRaises(IntegrityError):
            Vinculo.objects.create(docente=docente, laboratorio=self.lab)

    def test_laboratorio_tem_no_maximo_um_responsavel(self):
        d1 = self.criar_docente("d1@usp.br", "10")
        d2 = self.criar_docente("d2@usp.br", "20")
        Vinculo.objects.create(docente=d1, laboratorio=self.lab, responsavel=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vinculo.objects.create(docente=d2, laboratorio=self.lab, responsavel=True)
        Vinculo.objects.create(docente=d2, laboratorio=self.lab, responsavel=False)
        self.assertEqual(self.lab.docentes.count(), 2)
