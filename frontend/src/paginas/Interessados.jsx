import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Carregando, SeloStatus, Vazio } from "../componentes/Basicos.jsx";
import { formatarData, useCarregar } from "../util.js";

const ABAS = [["pendente", "Pendentes"], ["aceita", "Aceitas"], ["recusada", "Recusadas"], ["", "Todas"]];

export default function Interessados() {
  const [parametros, setParametros] = useSearchParams();
  const projeto = parametros.get("projeto") || "";
  const status = parametros.has("status") ? parametros.get("status") : "pendente";
  const projetos = useCarregar(() => api("/projetos/", { params: { meus: 1 } }), []);
  const lista = useCarregar(() => api("/manifestacoes/", { params: { projeto, status } }), [projeto, status]);
  const [erro, setErro] = useState(null);

  function filtrar(novos) {
    const proximos = { projeto, status, ...novos };
    setParametros(Object.fromEntries(Object.entries(proximos).filter(([nome, valor]) => valor || nome === "status")));
  }

  async function responder(manifestacao, acao) {
    const verbo = acao === "aceitar" ? "Aceitar" : "Recusar";
    if (!window.confirm(`${verbo} ${manifestacao.aluno_nome}? A resposta é definitiva.`)) return;
    setErro(null);
    try {
      const atualizada = await api(`/manifestacoes/${manifestacao.id_manifestacao}/${acao}/`, { metodo: "POST" });
      lista.setDados((atual) =>
        atual
          .map((m) => (m.id_manifestacao === atualizada.id_manifestacao ? atualizada : m))
          .filter((m) => !status || m.status === status),
      );
    } catch (falha) {
      setErro(falha.message);
    }
  }

  return (
    <div>
      <h1>Interessados</h1>
      <p className="subtitulo">Alunos que manifestaram interesse nas suas vagas.</p>

      <div className="barra-filtros">
        <div className="abas" role="tablist">
          {ABAS.map(([valor, rotulo]) => (
            <button
              key={rotulo}
              type="button"
              role="tab"
              aria-selected={status === valor}
              className={`aba${status === valor ? " aba-ativa" : ""}`}
              onClick={() => filtrar({ status: valor })}
            >
              {rotulo}
            </button>
          ))}
        </div>
        <select aria-label="Projeto" value={projeto} onChange={(evento) => filtrar({ projeto: evento.target.value })}>
          <option value="">Todos os projetos</option>
          {projetos.dados?.map((p) => <option key={p.id_projeto} value={p.id_projeto}>{p.titulo}</option>)}
        </select>
      </div>

      <Aviso>{erro}</Aviso>
      <Aviso>{lista.erro?.message}</Aviso>
      {lista.carregando && <Carregando />}
      {lista.dados?.length === 0 && <Vazio titulo="Nenhuma manifestação aqui." />}

      <div className="lista">
        {lista.dados?.map((m) => (
          <article key={m.id_manifestacao} className="cartao">
            <div className="cartao-topo">
              <div>
                <h3>{m.aluno_nome}</h3>
                <p className="cartao-meta">
                  {m.aluno_curso} · ingresso em {m.aluno_ano_ingresso} · nº USP {m.aluno_numero_usp}
                </p>
              </div>
              <SeloStatus status={m.status} />
            </div>
            <p className="cartao-meta">
              <a href={`mailto:${m.aluno_email}`}>{m.aluno_email}</a>
            </p>
            <p className="cartao-meta">
              <Link to={`/projetos/${m.projeto}`}>{m.projeto_titulo}</Link> · {m.tipo_oportunidade_nome} · em {formatarData(m.data_manifestacao)}
            </p>
            {m.mensagem && <p className="citacao">{m.mensagem}</p>}
            {m.status === "pendente" && (
              <div className="acoes">
                <button type="button" className="botao botao-discreto" onClick={() => responder(m, "recusar")}>Recusar</button>
                <button type="button" className="botao" onClick={() => responder(m, "aceitar")}>Aceitar</button>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
