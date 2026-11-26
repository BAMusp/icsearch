import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Carregando, SeloStatus, Vazio } from "../componentes/Basicos.jsx";
import { formatarData, useCarregar } from "../util.js";

export default function MinhasManifestacoes() {
  const lista = useCarregar(() => api("/manifestacoes/"), []);

  return (
    <div>
      <h1>Minhas manifestações</h1>
      <p className="subtitulo">Acompanhe as vagas em que você demonstrou interesse.</p>
      {lista.carregando && <Carregando />}
      <Aviso>{lista.erro?.message}</Aviso>
      {lista.dados?.length === 0 && (
        <Vazio titulo="Você ainda não manifestou interesse em nenhuma vaga.">
          <Link to="/?vaga_aberta=1" className="botao">Ver vagas abertas</Link>
        </Vazio>
      )}
      <div className="lista">
        {lista.dados?.map((m) => (
          <article key={m.id_manifestacao} className="cartao">
            <div className="cartao-topo">
              <h3><Link to={`/projetos/${m.projeto}`}>{m.projeto_titulo}</Link></h3>
              <SeloStatus status={m.status} />
            </div>
            <p className="cartao-meta">
              {m.tipo_oportunidade_nome} · {m.docente_nome} · enviada em {formatarData(m.data_manifestacao)}
              {m.data_resposta && ` · respondida em ${formatarData(m.data_resposta)}`}
            </p>
            {m.mensagem && <p className="citacao">{m.mensagem}</p>}
          </article>
        ))}
      </div>
    </div>
  );
}
