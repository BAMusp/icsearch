import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Carregando, Vazio } from "../componentes/Basicos.jsx";
import CartaoProjeto from "../componentes/CartaoProjeto.jsx";
import { plural, useCarregar } from "../util.js";

const FILTROS = ["q", "grande_area", "departamento", "tipo_oportunidade", "agencia_fomento", "com_bolsa", "vaga_aberta", "page"];

function carregarOpcoes() {
  return Promise.all([
    api("/grandes-areas/"),
    api("/departamentos/"),
    api("/tipos-oportunidade/"),
    api("/agencias-fomento/"),
  ]).then(([areas, departamentos, tipos, agencias]) => ({ areas, departamentos, tipos, agencias }));
}

export default function Busca() {
  const [parametros, setParametros] = useSearchParams();
  const filtros = Object.fromEntries(FILTROS.map((nome) => [nome, parametros.get(nome) || ""]));
  const [texto, setTexto] = useState(filtros.q);
  const opcoes = useCarregar(carregarOpcoes, []);
  const chave = parametros.toString();
  const resultado = useCarregar(() => api("/busca/", { params: filtros }), [chave]);

  function alterar(novos) {
    const proximos = { ...filtros, page: "", ...novos };
    const limpos = Object.fromEntries(Object.entries(proximos).filter(([, valor]) => valor));
    setParametros(limpos);
  }

  function aoBuscar(evento) {
    evento.preventDefault();
    alterar({ q: texto.trim() });
  }

  function limpar() {
    setTexto("");
    setParametros({});
  }

  const pagina = Number(filtros.page || 1);
  const dados = resultado.dados;
  const totalPaginas = dados ? Math.max(1, Math.ceil(dados.count / 10)) : 1;
  const algumFiltro = FILTROS.some((nome) => nome !== "page" && filtros[nome]);

  return (
    <div className="busca">
      <section className="busca-topo">
        <h1>Encontre sua iniciação científica</h1>
        <p className="subtitulo">Pesquisas e vagas abertas dos docentes da Escola Politécnica.</p>
        <form className="busca-form" onSubmit={aoBuscar} role="search">
          <input
            type="search"
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            placeholder="Palavra-chave, título ou docente (ex.: visão computacional)"
            aria-label="Buscar pesquisas"
          />
          <button type="submit" className="botao">Buscar</button>
        </form>
      </section>

      <div className="busca-corpo">
        <aside className="filtros" aria-label="Filtros">
          <h2>Filtros</h2>
          {opcoes.erro && <Aviso>{opcoes.erro.message}</Aviso>}
          {opcoes.dados && (
            <>
              <FiltroSelecao
                rotulo="Grande área"
                valor={filtros.grande_area}
                opcoes={opcoes.dados.areas.map((a) => [a.id_grande_area, a.nome])}
                aoMudar={(valor) => alterar({ grande_area: valor })}
              />
              <FiltroSelecao
                rotulo="Departamento"
                valor={filtros.departamento}
                opcoes={opcoes.dados.departamentos.map((d) => [d.id_departamento, `${d.sigla} · ${d.nome}`])}
                aoMudar={(valor) => alterar({ departamento: valor })}
              />
              <FiltroSelecao
                rotulo="Tipo de oportunidade"
                valor={filtros.tipo_oportunidade}
                opcoes={opcoes.dados.tipos.map((t) => [t.id_tipo_oportunidade, t.nome])}
                aoMudar={(valor) => alterar({ tipo_oportunidade: valor })}
              />
              <FiltroSelecao
                rotulo="Agência da bolsa"
                valor={filtros.agencia_fomento}
                opcoes={opcoes.dados.agencias.map((a) => [a.id_agencia_fomento, a.sigla])}
                aoMudar={(valor) => alterar({ agencia_fomento: valor })}
              />
            </>
          )}
          <label className="caixa">
            <input
              type="checkbox"
              checked={filtros.vaga_aberta === "1"}
              onChange={(evento) => alterar({ vaga_aberta: evento.target.checked ? "1" : "" })}
            />
            Só com vaga aberta
          </label>
          <label className="caixa">
            <input
              type="checkbox"
              checked={filtros.com_bolsa === "1"}
              onChange={(evento) => alterar({ com_bolsa: evento.target.checked ? "1" : "" })}
            />
            Só com bolsa
          </label>
          {algumFiltro && (
            <button type="button" className="botao botao-discreto botao-largo" onClick={limpar}>
              Limpar filtros
            </button>
          )}
        </aside>

        <section className="resultados" aria-live="polite">
          {resultado.carregando && <Carregando texto="Buscando..." />}
          {resultado.erro && <Aviso>{resultado.erro.message}</Aviso>}
          {dados && !resultado.carregando && (
            <>
              <p className="contagem">{plural(dados.count, "pesquisa encontrada", "pesquisas encontradas")}</p>
              {dados.results.length === 0 ? (
                <Vazio titulo="Nenhuma pesquisa com esses critérios.">
                  Tente outra palavra ou remova algum filtro.
                </Vazio>
              ) : (
                <div className="lista">
                  {dados.results.map((projeto) => (
                    <CartaoProjeto key={projeto.id_projeto} projeto={projeto} />
                  ))}
                </div>
              )}
              {totalPaginas > 1 && (
                <nav className="paginacao" aria-label="Paginação">
                  <button
                    type="button"
                    className="botao botao-discreto"
                    disabled={!dados.previous}
                    onClick={() => alterar({ page: String(pagina - 1) })}
                  >
                    Anterior
                  </button>
                  <span>Página {pagina} de {totalPaginas}</span>
                  <button
                    type="button"
                    className="botao botao-discreto"
                    disabled={!dados.next}
                    onClick={() => alterar({ page: String(pagina + 1) })}
                  >
                    Próxima
                  </button>
                </nav>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function FiltroSelecao({ rotulo, valor, opcoes, aoMudar }) {
  const id = `filtro-${rotulo.toLowerCase().replace(/\W+/g, "-")}`;
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <select id={id} value={valor} onChange={(evento) => aoMudar(evento.target.value)}>
        <option value="">Todos</option>
        {opcoes.map(([id_opcao, nome]) => (
          <option key={id_opcao} value={id_opcao}>{nome}</option>
        ))}
      </select>
    </div>
  );
}
