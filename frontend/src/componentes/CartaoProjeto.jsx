import { Link } from "react-router-dom";
import { plural } from "../util.js";

export default function CartaoProjeto({ projeto }) {
  const vagasAtivas = projeto.vagas.filter((vaga) => vaga.ativa);
  const abertas = vagasAtivas.reduce((soma, vaga) => soma + vaga.vagas_abertas, 0);
  const tipos = [...new Set(vagasAtivas.map((vaga) => vaga.tipo_oportunidade_nome))];
  const temBolsa = vagasAtivas.some((vaga) => vaga.agencia_fomento_sigla);

  return (
    <article className="cartao cartao-projeto">
      <div className="cartao-topo">
        <h3>
          <Link to={`/projetos/${projeto.id_projeto}`}>{projeto.titulo}</Link>
        </h3>
        {abertas > 0 ? (
          <span className="selo selo-aceita">{plural(abertas, "vaga aberta", "vagas abertas")}</span>
        ) : (
          <span className="selo selo-neutro">Sem vagas abertas</span>
        )}
      </div>
      <p className="cartao-meta">
        {projeto.docente_nome} · {projeto.departamento?.sigla}
        {projeto.laboratorio_nome && ` · ${projeto.laboratorio_nome}`}
      </p>
      <p className="cartao-resumo">{projeto.resumo}</p>
      <div className="etiquetas">
        {projeto.grandes_areas_nomes.map((area) => (
          <span key={area} className="etiqueta etiqueta-area">{area}</span>
        ))}
        {tipos.map((tipo) => (
          <span key={tipo} className="etiqueta">{tipo}</span>
        ))}
        {temBolsa && <span className="etiqueta etiqueta-bolsa">Com bolsa</span>}
      </div>
    </article>
  );
}
