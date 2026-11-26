import { useState } from "react";
import { api } from "../api.js";
import { Aviso, Carregando, Vazio } from "../componentes/Basicos.jsx";
import { useCarregar } from "../util.js";

const DIMENSOES = {
  grande_area: "Grande área",
  departamento: "Departamento",
  agencia_fomento: "Agência de fomento",
  tipo_oportunidade: "Tipo de oportunidade",
  periodo: "Período",
  status: "Status",
};

export default function Painel() {
  const [filtros, setFiltros] = useState({ linhas: "grande_area", colunas: "periodo", de: "", ate: "" });
  const painel = useCarregar(() => api("/painel/demanda/", { params: filtros }), [JSON.stringify(filtros)]);

  function mudar(campo) {
    return (evento) => {
      const valor = evento.target.value;
      setFiltros((atual) => {
        const proximo = { ...atual, [campo]: valor };
        if (campo === "linhas" && valor === atual.colunas) proximo.colunas = atual.linhas;
        if (campo === "colunas" && valor === atual.linhas) proximo.linhas = atual.colunas;
        return proximo;
      });
    };
  }

  const dados = painel.dados;

  return (
    <div>
      <h1>Painel de demanda</h1>
      <p className="subtitulo">Manifestações de interesse cruzadas por duas dimensões.</p>

      <div className="barra-filtros cartao">
        <label>
          Linhas
          <select value={filtros.linhas} onChange={mudar("linhas")}>
            {Object.entries(DIMENSOES).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
          </select>
        </label>
        <label>
          Colunas
          <select value={filtros.colunas} onChange={mudar("colunas")}>
            {Object.entries(DIMENSOES).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
          </select>
        </label>
        <label>
          De
          <input type="date" value={filtros.de} onChange={mudar("de")} />
        </label>
        <label>
          Até
          <input type="date" value={filtros.ate} onChange={mudar("ate")} />
        </label>
      </div>

      {painel.carregando && <Carregando />}
      <Aviso>{painel.erro?.message}</Aviso>
      {dados && dados.total_geral === 0 && <Vazio titulo="Nenhuma manifestação no período." />}
      {dados && dados.total_geral > 0 && (
        <div className="tabela-rolavel">
          <table className="tabela-cruzada">
            <thead>
              <tr>
                <th scope="col">{DIMENSOES[dados.linhas.dimensao]} \ {DIMENSOES[dados.colunas.dimensao]}</th>
                {dados.colunas.valores.map((coluna) => <th key={coluna} scope="col">{coluna}</th>)}
                <th scope="col" className="total">Total</th>
              </tr>
            </thead>
            <tbody>
              {dados.linhas.valores.map((linha) => (
                <tr key={linha}>
                  <th scope="row">{linha}</th>
                  {dados.colunas.valores.map((coluna) => {
                    const valor = dados.celulas[linha]?.[coluna];
                    return <td key={coluna} className={valor ? "" : "zero"}>{valor || 0}</td>;
                  })}
                  <td className="total">{dados.total_linha[linha]}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row">Total</th>
                {dados.colunas.valores.map((coluna) => <td key={coluna} className="total">{dados.total_coluna[coluna]}</td>)}
                <td className="total total-geral">{dados.total_geral}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
      {dados?.linhas.dimensao === "grande_area" || dados?.colunas.dimensao === "grande_area" ? (
        <p className="discreto nota">
          Projetos com mais de uma grande área contam em cada uma delas; o total geral conta cada manifestação uma vez.
        </p>
      ) : null}
    </div>
  );
}
