# ICsearch

Catálogo de pesquisas e oportunidades de iniciação científica da Escola
Politécnica da USP. Trabalho da disciplina PMR3304.

O aluno busca pesquisas por área, palavra-chave ou departamento, vê o que cada
docente investiga agora e manifesta interesse nas vagas abertas. O docente
divulga seus projetos, define as vagas e seleciona os interessados.

## Stack

- **Back-end:** Python 3.11+, Django 5.2, Django REST Framework. SQLite no
  desenvolvimento, PostgreSQL em produção. Autenticação por token.
- **Front-end:** React + Vite, consumindo a API por HTTP.

## Como rodar

Back-end, em um terminal:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py popular_demo        # opcional: dados de exemplo
python manage.py runserver
```

Front-end, em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Site em http://localhost:5173. Testes: `python manage.py test catalogo`

O `migrate` já cadastra departamentos, cursos, grandes áreas, tipos de
oportunidade e agências. O `popular_demo` cria docentes, alunos e projetos de
exemplo; a senha de todos é `Demo-2026-icsearch`.

## Deploy no Render

O `render.yaml` cria o banco PostgreSQL, a API (`icsearch-api`) e o site
(`icsearch`). No Render: **New → Blueprint**, escolha este repositório e
preencha as variáveis pedidas:

- `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD`: o administrador.
- `CORS_ALLOWED_ORIGINS`: endereço do site, ex. `https://icsearch.onrender.com`.
- `VITE_API_URL`: endereço da API, ex. `https://icsearch-api.onrender.com`.

Se os endereços finais forem diferentes, corrija as duas últimas variáveis e
faça um novo deploy dos dois serviços.

**Chave primária com o nome do DER.** Cada modelo declara a sua
(`id_projeto = models.AutoField(primary_key=True)`) em vez de usar o `id`
implícito do Django. Nenhuma tabela tem chave composta.

**Chave estrangeira com `db_column`.** O campo Python se chama `docente`, para
escrever `projeto.docente.nome`, mas a coluna do banco se chama `id_docente`,
igual ao DER. Toda FK nova deve seguir isso.

**Restrições no banco, não só na view.** As regras de unicidade vivem em
`Meta.constraints`. Ao criar uma regra nova, escreva o teste junto, em
`catalogo/tests.py`.

## Decisões de modelagem

1. **O projeto não guarda departamento.** `Projeto.departamento` é uma
   *property* que navega `projeto.docente.departamento`. Guardar a coluna
   criaria dependência transitiva: mover um docente de departamento obrigaria a
   atualizar todas as linhas de projeto dele.

2. **`vagas_abertas` é derivado**, nunca digitado: quantidade ofertada menos
   manifestações aceitas. Se virar coluna materializada por desempenho, precisa
   de trava de concorrência.

3. **Docente e laboratório têm uma relação só**, o `Vinculo`, que carrega o
   booleano `responsavel`. Não existe `Laboratorio.docente_responsavel`:
   seriam duas relações concorrentes entre as mesmas tabelas.

4. **`Usuario` é o `AUTH_USER_MODEL`.** `Aluno` e `Docente` são especializações
   por `OneToOneField`, e é esse UNIQUE que mantém a relação em 1:1. Dois campos
   do DER vêm do Django: `senha_hash` é o `password` e `ultimo_acesso` é o
   `last_login`.

5. **`ManifestacaoInteresse` é a tabela-fato.** Não carrega dimensão alguma como
   coluna; o painel ADM003 agrega navegando até grande área, departamento,
   agência e período. Manifestação não se apaga nem se cancela.

6. **Agência de fomento nula tem significado:** em projeto, pesquisa sem
   fomento; em vaga, oportunidade sem bolsa. Não existe um valor "Sem bolsa".

## Observação

- O painel ADM003 deriva as dimensões ao vivo, então mover um docente de
  departamento reescreve totais históricos. Decisão consciente; se incomodar, a
  saída é gravar uma cópia das dimensões na manifestação.
