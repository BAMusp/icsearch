from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import (
    AgenciaFomento, Aluno, Curso, Departamento, Docente, GrandeArea, Laboratorio,
    ManifestacaoInteresse, PalavraChave, Projeto, TipoOportunidade, Usuario, Vaga,
    Vinculo, normalizar_termo,
)

FUSO = ZoneInfo("America/Sao_Paulo")

DOCENTES = [
    ("Carlos Mendes", "demo.carlos@usp.br", "9000001", "PMR"),
    ("Maria Conceição", "demo.maria@usp.br", "9000002", "PCS"),
    ("Roberto Andrade", "demo.roberto@usp.br", "9000003", "PEA"),
    ("Helena Prado", "demo.helena@usp.br", "9000004", "PHA"),
]

LABORATORIOS = [
    ("PMR", "LabRob", "Laboratório de Robótica", "demo.carlos@usp.br"),
    ("PCS", "LIA", "Laboratório de Inteligência Artificial", "demo.maria@usp.br"),
    ("PEA", "LEN", "Laboratório de Energias Renováveis", "demo.roberto@usp.br"),
]

PROJETOS = [
    {
        "docente": "demo.carlos@usp.br", "laboratorio": "LabRob", "agencia": "FAPESP",
        "titulo": "Robô autônomo para inspeção de dutos",
        "resumo": "Desenvolvimento de um robô que percorre dutos industriais e detecta corrosão usando visão computacional e fusão de sensores.",
        "inicio": date(2026, 3, 1), "areas": ["Mecânica", "Elétrica"],
        "palavras": ["Visão Computacional", "ROS", "Robótica móvel"],
        "vagas": [("Iniciação Científica", 2, "FAPESP"), ("Trabalho de Conclusão de Curso", 1, None)],
    },
    {
        "docente": "demo.carlos@usp.br", "laboratorio": "LabRob", "agencia": None,
        "titulo": "Controle de exoesqueleto para reabilitação",
        "resumo": "Estratégias de controle robusto para exoesqueletos de membros inferiores usados em fisioterapia.",
        "inicio": date(2026, 8, 1), "areas": ["Mecânica"],
        "palavras": ["Controle", "Biomecânica"],
        "vagas": [("Iniciação Tecnológica", 1, "USP")],
    },
    {
        "docente": "demo.maria@usp.br", "laboratorio": "LIA", "agencia": "CNPq",
        "titulo": "Assistente conversacional para alunos de engenharia",
        "resumo": "Modelos de linguagem adaptados às disciplinas do ciclo básico para responder dúvidas de alunos.",
        "inicio": date(2026, 2, 1), "areas": ["Elétrica"],
        "palavras": ["Processamento de Linguagem Natural", "Aprendizado de Máquina"],
        "vagas": [("Iniciação Científica", 1, "CNPq"), ("Iniciação Científica", 2, None)],
    },
    {
        "docente": "demo.roberto@usp.br", "laboratorio": "LEN", "agencia": "CAPES",
        "titulo": "Previsão de geração solar em microrredes",
        "resumo": "Previsão de curto prazo da geração fotovoltaica para operar microrredes com armazenamento em baterias.",
        "inicio": date(2026, 4, 1), "areas": ["Elétrica"],
        "palavras": ["Energia Solar", "Microrredes", "Séries Temporais"],
        "vagas": [("Iniciação Científica", 1, "CAPES")],
    },
    {
        "docente": "demo.helena@usp.br", "laboratorio": None, "agencia": None,
        "titulo": "Qualidade da água em reservatórios urbanos",
        "resumo": "Monitoramento de parâmetros de qualidade da água com sensores de baixo custo em reservatórios da Grande São Paulo.",
        "inicio": date(2026, 3, 15), "areas": ["Civil", "Química"],
        "palavras": ["Saneamento", "Sensores", "Recursos Hídricos"],
        "vagas": [("Estágio em laboratório", 3, None)],
    },
]

ALUNOS = [
    ("Ana Souza", "demo.ana@usp.br", "8000001", "Mecatrônica", 2023),
    ("Bruno Lima", "demo.bruno@usp.br", "8000002", "Computação", 2024),
    ("Camila Rocha", "demo.camila@usp.br", "8000003", "Elétrica", 2022),
    ("Diego Alves", "demo.diego@usp.br", "8000004", "Mecânica", 2024),
    ("Elisa Martins", "demo.elisa@usp.br", "8000005", "Ambiental", 2023),
    ("Felipe Costa", "demo.felipe@usp.br", "8000006", "Computação", 2025),
]

MANIFESTACOES = [
    ("demo.ana@usp.br", 0, 0, "aceita", "2026-03-10"),
    ("demo.diego@usp.br", 0, 0, "pendente", "2026-08-20"),
    ("demo.bruno@usp.br", 2, 0, "aceita", "2026-02-20"),
    ("demo.felipe@usp.br", 2, 1, "pendente", "2026-09-02"),
    ("demo.camila@usp.br", 2, 1, "recusada", "2026-03-05"),
    ("demo.camila@usp.br", 3, 0, "pendente", "2026-09-15"),
    ("demo.elisa@usp.br", 4, 0, "aceita", "2026-04-01"),
    ("demo.ana@usp.br", 1, 0, "pendente", "2026-10-01"),
]


class Command(BaseCommand):
    help = "Cria docentes, alunos, projetos, vagas e manifestacoes de demonstracao."

    def add_arguments(self, parser):
        parser.add_argument("--senha", default="Demo-2026-icsearch")

    @transaction.atomic
    def handle(self, *args, senha, **opcoes):
        if Usuario.objects.filter(email=DOCENTES[0][1]).exists():
            self.stdout.write("Dados de demonstracao ja existem; nada foi alterado.")
            return

        docentes = {}
        for nome, email, nusp, sigla in DOCENTES:
            usuario = Usuario.objects.create_user(email=email, nome=nome, password=senha)
            docentes[email] = Docente.objects.create(
                usuario=usuario, departamento=Departamento.objects.get(sigla=sigla), numero_usp=nusp,
            )

        laboratorios = {}
        for sigla_dep, sigla, nome, email in LABORATORIOS:
            laboratorio, _ = Laboratorio.objects.get_or_create(
                nome=nome, defaults={"sigla": sigla, "departamento": Departamento.objects.get(sigla=sigla_dep)},
            )
            Vinculo.objects.create(docente=docentes[email], laboratorio=laboratorio, responsavel=True)
            laboratorios[sigla] = laboratorio

        projetos = []
        for dados in PROJETOS:
            projeto = Projeto.objects.create(
                docente=docentes[dados["docente"]],
                laboratorio=laboratorios.get(dados["laboratorio"]),
                agencia_fomento=AgenciaFomento.objects.filter(sigla=dados["agencia"]).first(),
                titulo=dados["titulo"], resumo=dados["resumo"], data_inicio=dados["inicio"],
            )
            projeto.grandes_areas.set(GrandeArea.objects.filter(nome__in=dados["areas"]))
            for termo in dados["palavras"]:
                palavra = PalavraChave.objects.filter(termo_normalizado=normalizar_termo(termo)).first()
                projeto.palavras_chave.add(palavra or PalavraChave.objects.create(termo=termo))
            vagas = [
                Vaga.objects.create(
                    projeto=projeto, tipo_oportunidade=TipoOportunidade.objects.get(nome=tipo),
                    quantidade=quantidade, agencia_fomento=AgenciaFomento.objects.filter(sigla=agencia).first(),
                )
                for tipo, quantidade, agencia in dados["vagas"]
            ]
            projetos.append(vagas)

        alunos = {}
        for nome, email, nusp, curso, ano in ALUNOS:
            usuario = Usuario.objects.create_user(email=email, nome=nome, password=senha)
            alunos[email] = Aluno.objects.create(
                usuario=usuario, curso=Curso.objects.get(nome=curso), numero_usp=nusp, ano_ingresso=ano,
            )

        for email, indice_projeto, indice_vaga, status, dia in MANIFESTACOES:
            quando = datetime.fromisoformat(f"{dia}T10:00:00").replace(tzinfo=FUSO)
            manifestacao = ManifestacaoInteresse.objects.create(
                aluno=alunos[email], vaga=projetos[indice_projeto][indice_vaga], status=status,
                mensagem="Tenho interesse na pesquisa e disponibilidade de 20 horas semanais.",
                data_resposta=None if status == "pendente" else quando,
            )
            ManifestacaoInteresse.objects.filter(pk=manifestacao.pk).update(data_manifestacao=quando)

        self.stdout.write(self.style.SUCCESS(
            f"Criados {len(DOCENTES)} docentes, {len(ALUNOS)} alunos, {len(PROJETOS)} projetos "
            f"e {len(MANIFESTACOES)} manifestacoes. Senha de todos: {senha}"
        ))
