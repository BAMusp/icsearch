import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Aviso, Carregando, SeloStatus } from "../componentes/Basicos.jsx";
import { formatarData, useCarregar } from "../util.js";

export default function Projeto() {
  const { id } = useParams();
  const { hash } = useLocation();
  const { usuario } = useAuth();
  const ehAluno = usuario?.perfil === "aluno";
  const projeto = useCarregar(() => api(`/projetos/${id}/`), [id]);
  const minhas = useCarregar(
    () => (ehAluno ? api("/manifestacoes/", { params: { projeto: id } }) : Promise.resolve([])),
    [id, ehAluno],
  );

  useEffect(() => {
    if (hash === "#oportunidades" && projeto.dados) {
      document.getElementById("oportunidades")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [hash, projeto.dados]);

  if (projeto.carregando) return <Carregando />;
  if (projeto.erro) {
    return <Aviso>{projeto.erro.status === 404 ? "Projeto não encontrado." : projeto.erro.message}</Aviso>;
  }

  const dados = projeto.dados;
  const ehDono = usuario?.perfil === "docente" && usuario.docente?.id_docente === dados.docente;
  const manifestacaoPorVaga = Object.fromEntries((minhas.dados || []).map((m) => [m.vaga, m]));
  const abertas = dados.vagas.filter((vaga) => vaga.ativa).reduce((soma, vaga) => soma + vaga.vagas_abertas, 0);

  function registrarManifestacao(manifestacao) {
    minhas.setDados((atual) => [...(atual || []), manifestacao]);
  }

  return (
    <article className="projeto">
      <Link to="/" className="voltar">← Voltar para a busca</Link>
      <header className="projeto-cabecalho">
        <div>
          <h1>{dados.titulo}</h1>
          <p className="cartao-meta">
            {dados.docente_nome} · {dados.departamento?.sigla} – {dados.departamento?.nome}
          </p>
        </div>
        {!ehDono && abertas > 0 && (!usuario || ehAluno) && (
          <a href="#oportunidades" className="botao">Manifestar interesse</a>
        )}
        {ehDono && (
          <div className="acoes">
            <Link to={`/meus-projetos/${dados.id_projeto}`} className="botao botao-discreto">Editar</Link>
            <Link to={`/interessados?projeto=${dados.id_projeto}`} className="botao">Ver interessados</Link>
          </div>
        )}
      </header>

      {!dados.ativo && <Aviso tipo="info">Este projeto está desativado e não aparece na busca.</Aviso>}

      <dl className="ficha">
        {dados.laboratorio_nome && (<><dt>Laboratório</dt><dd>{dados.laboratorio_nome}</dd></>)}
        <dt>Período</dt>
        <dd>{formatarData(dados.data_inicio)}{dados.data_fim ? ` a ${formatarData(dados.data_fim)}` : " · em andamento"}</dd>
        <dt>Fomento</dt>
        <dd>{dados.agencia_fomento_sigla || "Pesquisa sem fomento"}</dd>
      </dl>

      <div className="etiquetas">
        {dados.grandes_areas_nomes.map((area) => (
          <span key={area} className="etiqueta etiqueta-area">{area}</span>
        ))}
        {dados.palavras_chave.map((palavra) => (
          <span key={palavra} className="etiqueta">{palavra}</span>
        ))}
      </div>

      <section className="secao">
        <h2>Sobre a pesquisa</h2>
        <p className="texto-longo">{dados.resumo}</p>
      </section>

      <section className="secao" id="oportunidades">
        <h2>Oportunidades</h2>
        {dados.vagas.length === 0 && (
          <Aviso tipo="info">
            {ehDono ? (
              <>Este projeto ainda não tem vagas. <Link to={`/meus-projetos/${dados.id_projeto}`}>Abra uma vaga</Link> para receber interessados.</>
            ) : (
              <>O docente ainda não abriu vagas neste projeto, por isso não é possível manifestar interesse agora. Veja <Link to="/?vaga_aberta=1">projetos com vaga aberta</Link>.</>
            )}
          </Aviso>
        )}
        {!usuario && dados.vagas.length > 0 && (
          <Aviso tipo="info">
            <Link to="/entrar" state={{ de: `/projetos/${id}` }}>Entre</Link> ou{" "}
            <Link to="/cadastro">cadastre-se como aluno</Link> para manifestar interesse.
          </Aviso>
        )}
        <div className="lista">
          {dados.vagas.map((vaga) => (
            <CartaoVaga
              key={vaga.id_vaga}
              vaga={vaga}
              podeManifestar={ehAluno}
              manifestacao={manifestacaoPorVaga[vaga.id_vaga]}
              aoManifestar={registrarManifestacao}
            />
          ))}
        </div>
      </section>
    </article>
  );
}

function CartaoVaga({ vaga, podeManifestar, manifestacao, aoManifestar }) {
  const [aberto, setAberto] = useState(false);
  const [mensagem, setMensagem] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const prazoVencido = vaga.data_limite && new Date(`${vaga.data_limite}T23:59:59`) < new Date();
  const disponivel = vaga.ativa && vaga.vagas_abertas > 0 && !prazoVencido;

  async function enviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      aoManifestar(await api("/manifestacoes/", { metodo: "POST", corpo: { vaga: vaga.id_vaga, mensagem } }));
      setAberto(false);
    } catch (falha) {
      setErro(falha.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className={`cartao cartao-vaga${vaga.ativa ? "" : " cartao-inativo"}`}>
      <div className="cartao-topo">
        <h3>{vaga.tipo_oportunidade_nome}</h3>
        <span className={`selo ${vaga.vagas_abertas > 0 ? "selo-aceita" : "selo-neutro"}`}>
          {vaga.vagas_abertas} de {vaga.quantidade} {vaga.quantidade === 1 ? "vaga aberta" : "vagas abertas"}
        </span>
      </div>
      <p className="cartao-meta">
        {vaga.agencia_fomento_sigla ? `Bolsa ${vaga.agencia_fomento_sigla}` : "Sem bolsa"}
        {vaga.data_limite && ` · Inscrições até ${formatarData(vaga.data_limite)}`}
        {!vaga.ativa && " · Vaga fechada"}
      </p>
      {vaga.descricao && <p className="texto-longo">{vaga.descricao}</p>}

      {podeManifestar && manifestacao && (
        <p className="manifestado">
          Você manifestou interesse em {formatarData(manifestacao.data_manifestacao)} · <SeloStatus status={manifestacao.status} />
        </p>
      )}
      {podeManifestar && !manifestacao && disponivel && !aberto && (
        <button type="button" className="botao" onClick={() => setAberto(true)}>Tenho interesse</button>
      )}
      {podeManifestar && !manifestacao && !disponivel && (
        <p className="discreto">{prazoVencido ? "O prazo de inscrição terminou." : "Vaga indisponível no momento."}</p>
      )}
      {aberto && (
        <form className="form-manifestacao" onSubmit={enviar}>
          <label htmlFor={`mensagem-${vaga.id_vaga}`}>Mensagem para o docente (opcional)</label>
          <textarea
            id={`mensagem-${vaga.id_vaga}`}
            rows={4}
            value={mensagem}
            onChange={(evento) => setMensagem(evento.target.value)}
            placeholder="Conte por que você se interessa e o que já estudou sobre o tema."
          />
          <Aviso>{erro}</Aviso>
          <div className="acoes">
            <button type="button" className="botao botao-discreto" onClick={() => setAberto(false)}>Cancelar</button>
            <button type="submit" className="botao" disabled={enviando}>
              {enviando ? "Enviando..." : "Enviar manifestação"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
