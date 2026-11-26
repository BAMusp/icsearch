# ICsearch

Catálogo de pesquisas e oportunidades de iniciação científica da Escola
Politécnica da USP. Trabalho da disciplina PMR3304.

O aluno busca pesquisas por área, palavra-chave ou departamento, vê o que cada
docente investiga agora e manifesta interesse nas vagas abertas. O docente
divulga seus projetos, define as vagas e seleciona os interessados.

## Estado atual

| Camada | Situação |
|---|---|
| Documentação (casos de uso, DER) | a trazer para `docs/` |
| Modelos Django | **em construção** — app `catalogo` criado, vazio |
| API REST | não existe |
| Frontend | não existe |

## Stack

- **Back-end:** Python 3.11+, Django 5.2, Django REST Framework. SQLite no
  desenvolvimento, PostgreSQL em produção. Autenticação por token.
- **Front-end:** React + Vite, consumindo a API por HTTP. Ainda por criar.

## Como rodar

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Testes: `python manage.py test catalogo`

## Convenções deste repositório

**Tudo em português.** Nomes de modelo, campo, tabela, rota e variável seguem a
documentação: `Projeto`, `ManifestacaoInteresse`, `vagas_abertas`. Não traduza
para inglês — o professor compara o código com o DER.

**Chave primária com o nome do DER.** Cada modelo declara a sua
(`id_projeto = models.AutoField(primary_key=True)`) em vez de usar o `id`
implícito do Django. Nenhuma tabela tem chave composta.

**Chave estrangeira com `db_column`.** O campo Python se chama `docente`, para
escrever `projeto.docente.nome`, mas a coluna do banco se chama `id_docente`,
igual ao DER. Toda FK nova deve seguir isso.

**Restrições no banco, não só na view.** As regras de unicidade vivem em
`Meta.constraints`. Ao criar uma regra nova, escreva o teste junto, em
`catalogo/tests.py`.

**Nada se apaga.** Valor de tabela auxiliar referenciado é desativado pelo campo
`ativo`. Usuário suspenso mantém as manifestações. As FKs usam `PROTECT` de
propósito; não troque para `CASCADE` sem pensar no painel ADM003.

## Decisões de modelagem

Estas vieram de discussão com o professor e não devem ser revertidas sem
conversa:

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

## Roteiro

| # | Passo | Casos de uso |
|---|---|---|
| 1 | Tabelas auxiliares (`Curso`, `GrandeArea`, `TipoOportunidade`, `AgenciaFomento`) | — |
| 2 | `Usuario`, `Aluno`, `Docente`, `Departamento`, `Laboratorio`, `Vinculo` | — |
| 3 | `Projeto`, `Vaga`, palavras-chave, `ManifestacaoInteresse` + testes | — |
| 4 | API das tabelas auxiliares | — |
| 5 | Cadastro e autenticação por token | ALU001, DOC001, AUT001 |
| 6 | Cadastro de projeto e vagas | DOC002, DOC003 |
| 7 | Busca | ALU002 |
| 8 | Manifestação e seleção | ALU003, DOC004 |
| 9 | Frontend React | — |
| 10 | Painel de demanda | ADM003 |

## Pendências conhecidas

- O caso de uso ALU001 não coleta `ano_ingresso` no formulário, mas o DOC004
  exibe esse dado. O campo deve existir no modelo e entrar na tela.
- O painel ADM003 deriva as dimensões ao vivo, então mover um docente de
  departamento reescreve totais históricos. Decisão consciente; se incomodar, a
  saída é gravar uma cópia das dimensões na manifestação.