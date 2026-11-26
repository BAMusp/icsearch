import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Carregando, Vazio } from "../componentes/Basicos.jsx";
import { plural, useCarregar } from "../util.js";

export default function MeusProjetos() {
  const lista = useCarregar(() => api("/projetos/", { params: { meus: 1 } }), []);

  return (
    <div>
      <div className="titulo-com-acao">
        <div>
          <h1>Meus projetos</h1>
          <p className="subtitulo">Divulgue suas pesquisas e abra vagas para os alunos.</p>
        </div>
        <Link to="/meus-projetos/novo" className="botao">Novo projeto</Link>
      </div>
      {lista.carregando && <Carregando />}
      <Aviso>{lista.erro?.message}</Aviso>
      {lista.dados?.length === 0 && (
        <Vazio titulo="Você ainda não cadastrou projetos.">
          <Link to="/meus-projetos/novo" className="botao">Cadastrar o primeiro</Link>
        </Vazio>
      )}
      <div className="lista">
        {lista.dados?.map((projeto) => {
          const abertas = projeto.vagas.filter((v) => v.ativa).reduce((soma, v) => soma + v.vagas_abertas, 0);
          return (
            <article key={projeto.id_projeto} className={`cartao${projeto.ativo ? "" : " cartao-inativo"}`}>
              <div className="cartao-topo">
                <h3><Link to={`/projetos/${projeto.id_projeto}`}>{projeto.titulo}</Link></h3>
                {!projeto.ativo && <span className="selo selo-neutro">Desativado</span>}
              </div>
              <p className="cartao-meta">
                {plural(projeto.vagas.length, "vaga cadastrada", "vagas cadastradas")} · {plural(abertas, "aberta", "abertas")}
              </p>
              <div className="acoes">
                <Link to={`/meus-projetos/${projeto.id_projeto}`} className="botao botao-discreto">Editar e gerenciar vagas</Link>
                <Link to={`/interessados?projeto=${projeto.id_projeto}`} className="botao botao-discreto">Interessados</Link>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
