from django.db import migrations

DEPARTAMENTOS = [
    ("PCC", "Construção Civil"),
    ("PCS", "Computação e Sistemas Digitais"),
    ("PEA", "Energia e Automação Elétricas"),
    ("PEF", "Estruturas e Geotécnica"),
    ("PHA", "Hidráulica e Ambiental"),
    ("PME", "Mecânica"),
    ("PMI", "de Minas e de Petróleo"),
    ("PMR", "Mecatrônica e Sist. Mecânicos"),
    ("PMT", "Metalúrgica e de Materiais"),
    ("PNV", "Naval e Oceânica"),
    ("PQI", "Química"),
    ("PRO", "Produção"),
    ("PSI", "Sistemas Eletrônicos"),
    ("PTC", "Telecomunicações e Controle"),
    ("PTR", "Transportes"),
]

CURSOS = [
    "Ambiental", "Civil", "Computação", "Elétrica", "Materiais", "Mecatrônica",
    "Mecânica", "Minas e Petróleo", "Naval", "Produção", "Química",
]

GRANDES_AREAS = ["Civil", "Elétrica", "Mecânica", "Química"]

TIPOS_OPORTUNIDADE = [
    "Iniciação Científica", "Iniciação Tecnológica",
    "Trabalho de Conclusão de Curso", "Estágio em laboratório",
]

AGENCIAS = [
    ("FAPESP", "Fundação de Amparo à Pesquisa do Estado de São Paulo"),
    ("CNPq", "Conselho Nacional de Desenvolvimento Científico e Tecnológico"),
    ("CAPES", "Coordenação de Aperfeiçoamento de Pessoal de Nível Superior"),
    ("USP", "Universidade de São Paulo"),
]


def criar(apps, schema_editor):
    Departamento = apps.get_model("catalogo", "Departamento")
    Curso = apps.get_model("catalogo", "Curso")
    GrandeArea = apps.get_model("catalogo", "GrandeArea")
    TipoOportunidade = apps.get_model("catalogo", "TipoOportunidade")
    AgenciaFomento = apps.get_model("catalogo", "AgenciaFomento")

    for sigla, nome in DEPARTAMENTOS:
        Departamento.objects.get_or_create(sigla=sigla, defaults={"nome": nome})
    for nome in CURSOS:
        Curso.objects.get_or_create(nome=nome)
    for nome in GRANDES_AREAS:
        GrandeArea.objects.get_or_create(nome=nome)
    for nome in TIPOS_OPORTUNIDADE:
        TipoOportunidade.objects.get_or_create(nome=nome)
    for sigla, nome in AGENCIAS:
        if not AgenciaFomento.objects.filter(sigla=sigla).exists():
            AgenciaFomento.objects.get_or_create(nome=nome, defaults={"sigla": sigla})


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0002_palavrachave_projeto_projetograndearea_and_more"),
    ]

    operations = [
        migrations.RunPython(criar, migrations.RunPython.noop),
    ]
