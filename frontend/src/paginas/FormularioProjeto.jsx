import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Aviso, Campo, Carregando } from "../componentes/Basicos.jsx";
import { formatarData, useCarregar } from "../util.js";

const VAZIO = {
  titulo: "", resumo: "", data_inicio: "", data_fim: "", laboratorio: "",
  agencia_fomento: "", grandes_areas: [], palavras_chave: "", ativo: true,
};

function paraFormulario(projeto) {
  return {
    titulo: projeto.titulo,
    resumo: projeto.resumo,
    data_inicio: projeto.data_inicio,
    data_fim: projeto.data_fim || "",
    laboratorio: projeto.laboratorio ? String(projeto.laboratorio) : "",
    agencia_fomento: projeto.agencia_fomento ? String(projeto.agencia_fomento) : "",
    grandes_areas: projeto.grandes_areas,
    palavras_chave: projeto.palavras_chave.join(", "),
    ativo: projeto.ativo,
  };
}

export default function FormularioProjeto() {
  const { id } = useParams();
  const editando = Boolean(id);
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const departamento = usuario.docente.departamento.id_departamento;
  const [dados, setDados] = useState(VAZIO);
  const [erro, setErro] = useState(null);
  const [salvo, setSalvo] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const opcoes = useCarregar(
    () => Promise.all([
      api("/grandes-areas/"),
      api("/agencias-fomento/"),
      api("/laboratorios/", { params: { departamento } }),
      api("/tipos-oportunidade/"),
    ]).then(([areas, agencias, laboratorios, tipos]) => ({ areas, agencias, laboratorios, tipos })),
    [departamento],
  );
  const projeto = useCarregar(() => (editando ? api(`/projetos/${id}/`) : Promise.resolve(null)), [id]);

  useEffect(() => {
    if (projeto.dados) setDados(paraFormulario(projeto.dados));
  }, [projeto.dados]);

  function mudar(campo) {
    return (evento) => {
      const alvo = evento.target;
      setDados((atual) => ({ ...atual, [campo]: alvo.type === "checkbox" ? alvo.checked : alvo.value }));
      setSalvo(false);
    };
  }

  function alternarArea(idArea) {
    setDados((atual) => ({
      ...atual,
      grandes_areas: atual.grandes_areas.includes(idArea)
        ? atual.grandes_areas.filter((a) => a !== idArea)
        : [...atual.grandes_areas, idArea],
    }));
    setSalvo(false);
  }

  async function aoEnviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    const corpo = {
      titulo: dados.titulo,
      resumo: dados.resumo,
      data_inicio: dados.data_inicio || null,
      data_fim: dados.data_fim || null,
      laboratorio: dados.laboratorio ? Number(dados.laboratorio) : null,
      agencia_fomento: dados.agencia_fomento ? Number(dados.agencia_fomento) : null,
      grandes_areas: dados.grandes_areas,
      palavras_chave: dados.palavras_chave.split(",").map((p) => p.trim()).filter(Boolean),
      ativo: dados.ativo,
    };
    try {
      if (editando) {
        projeto.setDados(await api(`/projetos/${id}/`, { metodo: "PATCH", corpo }));
        setSalvo(true);
      } else {
        const novo = await api("/projetos/", { metodo: "POST", corpo });
        navegar(`/meus-projetos/${novo.id_projeto}`, { replace: true, state: { criado: true } });
      }
    } catch (falha) {
      setErro(falha);
    } finally {
      setEnviando(false);
    }
  }

  if (opcoes.carregando || projeto.carregando) return <Carregando />;
  if (projeto.erro) return <Aviso>{projeto.erro.status === 404 ? "Projeto não encontrado." : projeto.erro.message}</Aviso>;

  const erroDe = (campo) => erro?.doCampo?.(campo);

  return (
    <div className="painel-medio">
      <Link to="/meus-projetos" className="voltar">← Meus projetos</Link>
      <h1>{editando ? "Editar projeto" : "Novo projeto"}</h1>
      <Aviso>{opcoes.erro?.message}</Aviso>

      <form className="formulario" onSubmit={aoEnviar} noValidate>
        <Campo rotulo="Título" id="titulo" erro={erroDe("titulo")}>
          <input id="titulo" value={dados.titulo} onChange={mudar("titulo")} />
        </Campo>
        <Campo rotulo="Resumo" id="resumo" erro={erroDe("resumo")} ajuda="Explique a pesquisa para um aluno de graduação.">
          <textarea id="resumo" rows={6} value={dados.resumo} onChange={mudar("resumo")} />
        </Campo>
        <div className="linha-campos">
          <Campo rotulo="Início" id="data_inicio" erro={erroDe("data_inicio")}>
            <input id="data_inicio" type="date" value={dados.data_inicio} onChange={mudar("data_inicio")} />
          </Campo>
          <Campo rotulo="Fim (opcional)" id="data_fim" erro={erroDe("data_fim")}>
            <input id="data_fim" type="date" value={dados.data_fim} onChange={mudar("data_fim")} />
          </Campo>
        </div>
        <div className="linha-campos">
          <Campo rotulo="Laboratório (opcional)" id="laboratorio" erro={erroDe("laboratorio")}>
            <select id="laboratorio" value={dados.laboratorio} onChange={mudar("laboratorio")}>
              <option value="">Nenhum</option>
              {opcoes.dados?.laboratorios.map((lab) => (
                <option key={lab.id_laboratorio} value={lab.id_laboratorio}>{lab.nome}</option>
              ))}
            </select>
          </Campo>
          <Campo rotulo="Agência de fomento" id="agencia_fomento" erro={erroDe("agencia_fomento")}>
            <select id="agencia_fomento" value={dados.agencia_fomento} onChange={mudar("agencia_fomento")}>
              <option value="">Pesquisa sem fomento</option>
              {opcoes.dados?.agencias.map((a) => (
                <option key={a.id_agencia_fomento} value={a.id_agencia_fomento}>{a.sigla}</option>
              ))}
            </select>
          </Campo>
        </div>
        <fieldset className={`campo grupo-caixas${erroDe("grandes_areas") ? " campo-com-erro" : ""}`}>
          <legend>Grandes áreas</legend>
          <div className="caixas">
            {opcoes.dados?.areas.map((area) => (
              <label key={area.id_grande_area} className="caixa">
                <input
                  type="checkbox"
                  checked={dados.grandes_areas.includes(area.id_grande_area)}
                  onChange={() => alternarArea(area.id_grande_area)}
                />
                {area.nome}
              </label>
            ))}
          </div>
          {erroDe("grandes_areas") && <small className="erro-campo">Escolha pelo menos uma grande área.</small>}
        </fieldset>
        <Campo rotulo="Palavras-chave" id="palavras_chave" erro={erroDe("palavras_chave")} ajuda="Separe por vírgula. Ex.: visão computacional, ROS, robótica móvel">
          <input id="palavras_chave" value={dados.palavras_chave} onChange={mudar("palavras_chave")} />
        </Campo>
        {editando && (
          <label className="caixa">
            <input type="checkbox" checked={dados.ativo} onChange={mudar("ativo")} />
            Projeto ativo (aparece na busca)
          </label>
        )}
        <Aviso>{erro?.geral?.() || erro?.message}</Aviso>
        <Aviso tipo="sucesso">{salvo && "Alterações salvas."}</Aviso>
        <div className="acoes">
          {editando && <Link to={`/projetos/${id}`} className="botao botao-discreto">Ver como aluno</Link>}
          <button type="submit" className="botao" disabled={enviando}>
            {enviando ? "Salvando..." : editando ? "Salvar alterações" : "Criar projeto"}
          </button>
        </div>
      </form>

      {editando && projeto.dados && (
        <GerenciarVagas
          projeto={projeto.dados}
          tipos={opcoes.dados?.tipos || []}
          agencias={opcoes.dados?.agencias || []}
          aoMudar={projeto.recarregar}
        />
      )}
    </div>
  );
}

const VAGA_VAZIA = { tipo_oportunidade: "", agencia_fomento: "", quantidade: "1", data_limite: "", descricao: "" };

function GerenciarVagas({ projeto, tipos, agencias, aoMudar }) {
  const [nova, setNova] = useState(VAGA_VAZIA);
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  function mudar(campo) {
    return (evento) => setNova((atual) => ({ ...atual, [campo]: evento.target.value }));
  }

  async function criar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api("/vagas/", {
        metodo: "POST",
        corpo: {
          projeto: projeto.id_projeto,
          tipo_oportunidade: Number(nova.tipo_oportunidade) || null,
          agencia_fomento: nova.agencia_fomento ? Number(nova.agencia_fomento) : null,
          quantidade: Number(nova.quantidade),
          data_limite: nova.data_limite || null,
          descricao: nova.descricao,
        },
      });
      setNova(VAGA_VAZIA);
      aoMudar();
    } catch (falha) {
      setErro(falha);
    } finally {
      setEnviando(false);
    }
  }

  async function alternar(vaga) {
    try {
      await api(`/vagas/${vaga.id_vaga}/`, { metodo: "PATCH", corpo: { ativa: !vaga.ativa } });
      aoMudar();
    } catch (falha) {
      setErro(falha);
    }
  }

  const erroDe = (campo) => erro?.doCampo?.(campo);

  return (
    <section className="secao">
      <h2>Vagas</h2>
      {projeto.vagas.length === 0 && <p className="discreto">Nenhuma vaga ainda. Abra a primeira abaixo.</p>}
      <div className="lista">
        {projeto.vagas.map((vaga) => (
          <div key={vaga.id_vaga} className={`cartao cartao-vaga${vaga.ativa ? "" : " cartao-inativo"}`}>
            <div className="cartao-topo">
              <h3>{vaga.tipo_oportunidade_nome}</h3>
              <span className={`selo ${vaga.ativa ? "selo-aceita" : "selo-neutro"}`}>{vaga.ativa ? "Aberta" : "Fechada"}</span>
            </div>
            <p className="cartao-meta">
              {vaga.vagas_abertas} de {vaga.quantidade} disponíveis · {vaga.agencia_fomento_sigla ? `Bolsa ${vaga.agencia_fomento_sigla}` : "Sem bolsa"}
              {vaga.data_limite && ` · até ${formatarData(vaga.data_limite)}`}
            </p>
            <div className="acoes">
              <Link to={`/interessados?projeto=${projeto.id_projeto}`} className="botao botao-discreto">Interessados</Link>
              <button type="button" className="botao botao-discreto" onClick={() => alternar(vaga)}>
                {vaga.ativa ? "Fechar vaga" : "Reabrir vaga"}
              </button>
            </div>
          </div>
        ))}
      </div>

      <form className="formulario cartao" onSubmit={criar} noValidate>
        <h3>Abrir nova vaga</h3>
        <div className="linha-campos">
          <Campo rotulo="Tipo de oportunidade" id="tipo_oportunidade" erro={erroDe("tipo_oportunidade") && "Selecione o tipo."}>
            <select id="tipo_oportunidade" value={nova.tipo_oportunidade} onChange={mudar("tipo_oportunidade")}>
              <option value="">Selecione...</option>
              {tipos.map((t) => <option key={t.id_tipo_oportunidade} value={t.id_tipo_oportunidade}>{t.nome}</option>)}
            </select>
          </Campo>
          <Campo rotulo="Bolsa" id="agencia_vaga" erro={erroDe("agencia_fomento")}>
            <select id="agencia_vaga" value={nova.agencia_fomento} onChange={mudar("agencia_fomento")}>
              <option value="">Sem bolsa</option>
              {agencias.map((a) => <option key={a.id_agencia_fomento} value={a.id_agencia_fomento}>{a.sigla}</option>)}
            </select>
          </Campo>
        </div>
        <div className="linha-campos">
          <Campo rotulo="Quantidade" id="quantidade" erro={erroDe("quantidade")}>
            <input id="quantidade" type="number" min="1" value={nova.quantidade} onChange={mudar("quantidade")} />
          </Campo>
          <Campo rotulo="Inscrições até (opcional)" id="data_limite" erro={erroDe("data_limite")}>
            <input id="data_limite" type="date" value={nova.data_limite} onChange={mudar("data_limite")} />
          </Campo>
        </div>
        <Campo rotulo="Descrição (opcional)" id="descricao" erro={erroDe("descricao")} ajuda="Pré-requisitos, carga horária, o que o aluno vai fazer.">
          <textarea id="descricao" rows={3} value={nova.descricao} onChange={mudar("descricao")} />
        </Campo>
        <Aviso>{erro?.geral?.() || erro?.message}</Aviso>
        <div className="acoes">
          <button type="submit" className="botao" disabled={enviando}>{enviando ? "Abrindo..." : "Abrir vaga"}</button>
        </div>
      </form>
    </section>
  );
}
