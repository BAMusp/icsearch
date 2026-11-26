from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    AgenciaFomento, Aluno, Curso, Departamento, Docente, GrandeArea,
    Laboratorio, ManifestacaoInteresse, PalavraChave, Projeto,
    ProjetoGrandeArea, ProjetoPalavraChave, TipoOportunidade, Usuario, Vaga,
    Vinculo,
)


class BaseTeste(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pmr = Departamento.objects.create(sigla="PMR", nome="Engenharia Mecatronica")
        cls.pcs = Departamento.objects.create(sigla="PCS", nome="Engenharia de Computacao")
        cls.lab = Laboratorio.objects.create(departamento=cls.pmr, nome="Laboratorio de Robotica")
        cls.curso = Curso.objects.create(nome="Engenharia Mecatronica")
        cls.ic = TipoOportunidade.objects.create(nome="Iniciacao Cientifica")
        cls.robotica = GrandeArea.objects.create(nome="Robotica")
        cls.fapesp = AgenciaFomento.objects.create(sigla="FAPESP", nome="Fundacao de Amparo a Pesquisa do Estado de Sao Paulo")

    def criar_docente(self, email, nusp):
        usuario = Usuario.objects.create_user(email=email, nome=email, password="senha-forte-123")
        return Docente.objects.create(usuario=usuario, departamento=self.pmr, numero_usp=nusp)

    def criar_aluno(self, email, nusp):
        usuario = Usuario.objects.create_user(email=email, nome=email, password="senha-forte-123")
        return Aluno.objects.create(usuario=usuario, curso=self.curso, numero_usp=nusp, ano_ingresso=2024)

    def criar_projeto(self, docente, **extra):
        return Projeto.objects.create(
            docente=docente, titulo="Robo autonomo", resumo="Navegacao",
            data_inicio=date(2026, 3, 1), **extra,
        )


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


class ProjetoTeste(BaseTeste):
    def test_departamento_do_projeto_acompanha_o_docente(self):
        docente = self.criar_docente("d1@usp.br", "10")
        projeto = self.criar_projeto(docente)
        self.assertEqual(projeto.departamento, self.pmr)
        docente.departamento = self.pcs
        docente.save()
        projeto.refresh_from_db()
        self.assertEqual(projeto.departamento, self.pcs)
        self.assertEqual(Projeto.objects.filter(docente__departamento=self.pcs).count(), 1)

    def test_projeto_sem_agencia_e_permitido(self):
        projeto = self.criar_projeto(self.criar_docente("d1@usp.br", "10"))
        self.assertIsNone(projeto.agencia_fomento)

    def test_data_fim_nao_pode_ser_antes_do_inicio(self):
        docente = self.criar_docente("d1@usp.br", "10")
        with self.assertRaises(IntegrityError):
            self.criar_projeto(docente, data_fim=date(2026, 1, 1))

    def test_grande_area_nao_se_repete_no_projeto(self):
        projeto = self.criar_projeto(self.criar_docente("d1@usp.br", "10"))
        ProjetoGrandeArea.objects.create(projeto=projeto, grande_area=self.robotica)
        with self.assertRaises(IntegrityError):
            ProjetoGrandeArea.objects.create(projeto=projeto, grande_area=self.robotica)


class PalavraChaveTeste(BaseTeste):
    def test_termo_normalizado_sem_acento_e_minusculo(self):
        palavra = PalavraChave.objects.create(termo="  Visão   Computacional ")
        self.assertEqual(palavra.termo, "Visão Computacional")
        self.assertEqual(palavra.termo_normalizado, "visao computacional")

    def test_variacoes_do_mesmo_termo_sao_a_mesma_palavra(self):
        PalavraChave.objects.create(termo="Visão Computacional")
        with self.assertRaises(IntegrityError):
            PalavraChave.objects.create(termo="visao computacional")

    def test_palavra_nao_se_repete_no_projeto(self):
        projeto = self.criar_projeto(self.criar_docente("d1@usp.br", "10"))
        palavra = PalavraChave.objects.create(termo="ROS")
        ProjetoPalavraChave.objects.create(projeto=projeto, palavra_chave=palavra)
        with self.assertRaises(IntegrityError):
            ProjetoPalavraChave.objects.create(projeto=projeto, palavra_chave=palavra)


class VagaTeste(BaseTeste):
    def setUp(self):
        self.projeto = self.criar_projeto(self.criar_docente("d1@usp.br", "10"))

    def criar_vaga(self, quantidade=2, **extra):
        return Vaga.objects.create(
            projeto=self.projeto, tipo_oportunidade=self.ic, quantidade=quantidade, **extra,
        )

    def test_vaga_sem_agencia_e_oportunidade_sem_bolsa(self):
        self.assertIsNone(self.criar_vaga().agencia_fomento)
        self.assertEqual(self.criar_vaga(agencia_fomento=self.fapesp).agencia_fomento, self.fapesp)

    def test_quantidade_precisa_ser_positiva(self):
        with self.assertRaises(IntegrityError):
            self.criar_vaga(quantidade=0)

    def test_vagas_abertas_desconta_so_as_aceitas(self):
        vaga = self.criar_vaga(quantidade=2)
        a1 = self.criar_aluno("a1@usp.br", "1")
        a2 = self.criar_aluno("a2@usp.br", "2")
        a3 = self.criar_aluno("a3@usp.br", "3")
        ManifestacaoInteresse.objects.create(aluno=a1, vaga=vaga, status="aceita")
        ManifestacaoInteresse.objects.create(aluno=a2, vaga=vaga, status="pendente")
        ManifestacaoInteresse.objects.create(aluno=a3, vaga=vaga, status="recusada")
        self.assertEqual(vaga.vagas_abertas, 1)


class ManifestacaoTeste(BaseTeste):
    def test_aluno_manifesta_uma_vez_por_vaga(self):
        projeto = self.criar_projeto(self.criar_docente("d1@usp.br", "10"))
        vaga = Vaga.objects.create(projeto=projeto, tipo_oportunidade=self.ic, quantidade=1)
        aluno = self.criar_aluno("a1@usp.br", "1")
        manifestacao = ManifestacaoInteresse.objects.create(aluno=aluno, vaga=vaga)
        self.assertEqual(manifestacao.status, "pendente")
        with self.assertRaises(IntegrityError):
            ManifestacaoInteresse.objects.create(aluno=aluno, vaga=vaga)



class ApiTabelasAuxiliaresTeste(BaseTeste):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(email="admin@teste.com", nome="Admin", password="x")
        Curso.objects.create(nome="Curso Antigo", ativo=False)

    def test_qualquer_pessoa_le_e_so_ve_os_ativos(self):
        resposta = self.client.get("/api/cursos/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([c["nome"] for c in resposta.json()], ["Engenharia Mecatronica"])

    def test_admin_ve_tambem_os_inativos(self):
        self.client.force_login(self.admin)
        resposta = self.client.get("/api/cursos/")
        self.assertEqual(len(resposta.json()), 2)

    def test_so_admin_cria(self):
        resposta = self.client.post("/api/cursos/", {"nome": "Engenharia Civil"})
        self.assertEqual(resposta.status_code, 401)
        aluno = self.criar_aluno("a1@usp.br", "1")
        self.client.force_login(aluno.usuario)
        resposta = self.client.post("/api/cursos/", {"nome": "Engenharia Civil"})
        self.assertEqual(resposta.status_code, 403)
        self.client.force_login(self.admin)
        resposta = self.client.post("/api/cursos/", {"nome": "Engenharia Civil"})
        self.assertEqual(resposta.status_code, 201)

    def test_nada_se_apaga_pela_api(self):
        self.client.force_login(self.admin)
        curso = Curso.objects.get(nome="Engenharia Mecatronica")
        resposta = self.client.delete(f"/api/cursos/{curso.pk}/")
        self.assertEqual(resposta.status_code, 405)
        resposta = self.client.patch(f"/api/cursos/{curso.pk}/", {"ativo": False}, content_type="application/json")
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Curso.objects.get(pk=curso.pk).ativo)

    def test_laboratorios_filtrados_por_departamento(self):
        Laboratorio.objects.create(departamento=self.pcs, nome="Laboratorio de Software")
        resposta = self.client.get(f"/api/laboratorios/?departamento={self.pmr.pk}")
        dados = resposta.json()
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["departamento_sigla"], "PMR")
        
    def test_lista_do_admin_mostra_curso_criado_depois(self):
        self.client.force_login(self.admin)
        self.assertEqual(len(self.client.get("/api/cursos/").json()), 2)
        Curso.objects.create(nome="Engenharia Naval")
        self.assertEqual(len(self.client.get("/api/cursos/").json()), 3)



class ApiAutenticacaoTeste(BaseTeste):
    SENHA = "Poli-2026-segura"

    def dados_aluno(self, **extra):
        dados = {
            "nome": "Ana Souza", "email": "ana@usp.br", "senha": self.SENHA,
            "numero_usp": "12345678", "curso": self.curso.pk, "ano_ingresso": 2024,
        }
        dados.update(extra)
        return dados

    def dados_docente(self, **extra):
        dados = {
            "nome": "Prof. Carlos", "email": "carlos@usp.br", "senha": self.SENHA,
            "numero_usp": "87654321", "departamento": self.pmr.pk,
        }
        dados.update(extra)
        return dados

    def test_cadastro_de_aluno_devolve_token(self):
        resposta = self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.json()
        self.assertTrue(corpo["token"])
        self.assertEqual(corpo["usuario"]["perfil"], "aluno")
        self.assertEqual(corpo["usuario"]["aluno"]["ano_ingresso"], 2024)
        aluno = Aluno.objects.get(numero_usp="12345678")
        self.assertTrue(aluno.usuario.check_password(self.SENHA))

    def test_cadastro_de_docente(self):
        resposta = self.client.post("/api/auth/cadastro/docente/", self.dados_docente())
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["usuario"]["docente"]["departamento"]["sigla"], "PMR")

    def test_email_precisa_ser_usp(self):
        resposta = self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno(email="ana@gmail.com"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("email", resposta.json())

    def test_email_repetido_e_recusado_sem_criar_nada(self):
        self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        resposta = self.client.post("/api/auth/cadastro/docente/", self.dados_docente(email="ANA@usp.br"))
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_senha_fraca_e_recusada(self):
        resposta = self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno(senha="123"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("senha", resposta.json())
        self.assertFalse(Usuario.objects.exists())

    def test_ano_de_ingresso_no_futuro_e_recusado(self):
        resposta = self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno(ano_ingresso=2999))
        self.assertEqual(resposta.status_code, 400)

    def test_login_com_token_e_rota_eu(self):
        self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        resposta = self.client.post("/api/auth/login/", {"email": "Ana@usp.br", "senha": self.SENHA})
        self.assertEqual(resposta.status_code, 200)
        token = resposta.json()["token"]
        self.assertIsNotNone(Usuario.objects.get(email="ana@usp.br").last_login)
        eu = self.client.get("/api/auth/eu/", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(eu.status_code, 200)
        self.assertEqual(eu.json()["nome"], "Ana Souza")

    def test_login_com_senha_errada(self):
        self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        resposta = self.client.post("/api/auth/login/", {"email": "ana@usp.br", "senha": "errada"})
        self.assertEqual(resposta.status_code, 400)

    def test_usuario_suspenso_nao_entra(self):
        self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        Usuario.objects.filter(email="ana@usp.br").update(is_active=False)
        resposta = self.client.post("/api/auth/login/", {"email": "ana@usp.br", "senha": self.SENHA})
        self.assertEqual(resposta.status_code, 400)

    def test_logout_invalida_o_token(self):
        cadastro = self.client.post("/api/auth/cadastro/aluno/", self.dados_aluno())
        cabecalho = {"HTTP_AUTHORIZATION": f"Token {cadastro.json()['token']}"}
        self.assertEqual(self.client.post("/api/auth/logout/", **cabecalho).status_code, 204)
        self.assertEqual(self.client.get("/api/auth/eu/", **cabecalho).status_code, 401)