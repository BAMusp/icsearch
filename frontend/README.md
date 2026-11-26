# ICsearch · frontend

React + Vite. Consome a API do Django em `backend/`.

## Como rodar

Com o Django rodando em `http://127.0.0.1:8000` (veja o README da raiz):

```bash
cd frontend
npm install
npm run dev
```

Abra http://localhost:5173. O Vite repassa tudo o que começa com `/api` para o
Django, então não é preciso configurar CORS no desenvolvimento.

## Estrutura

- `src/api.js` — chamadas HTTP, token e mensagens de erro da API
- `src/auth.jsx` — sessão do usuário (login, cadastro, logout)
- `src/componentes/` — peças reaproveitadas entre as telas
- `src/paginas/` — uma tela por arquivo
- `src/estilos.css` — todo o visual

## Telas

| Rota | Tela | Caso de uso |
|---|---|---|
| `/` | Busca com filtros | ALU002 |
| `/projetos/:id` | Detalhe do projeto e manifestação de interesse | ALU003 |
| `/cadastro`, `/entrar` | Cadastro de aluno e docente, login | ALU001, DOC001, AUT001 |
| `/minhas-manifestacoes` | Manifestações do aluno | ALU003 |
| `/meus-projetos`, `/meus-projetos/:id` | Projetos e vagas do docente | DOC002, DOC003 |
| `/interessados` | Seleção dos interessados | DOC004 |
| `/painel` | Painel de demanda (administrador) | ADM003 |
