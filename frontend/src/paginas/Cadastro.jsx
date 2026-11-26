import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Aviso, Campo } from "../componentes/Basicos.jsx";
import { useCarregar } from "../util.js";

const ANO_ATUAL = new Date().getFullYear();

const INICIAL = {
  nome: "", email: "", senha: "", numero_usp: "",
  curso: "", ano_ingresso: String(ANO_ATUAL), departamento: "", url_lattes: "",
};

export default function Cadastro() {
  const { usuario, cadastrar } = useAuth();
  const navegar = useNavigate();
  const [perfil, setPerfil] = useState("aluno");
  const [dados, setDados] = useState(INICIAL);
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const opcoes = useCarregar(
    () => Promise.all([api("/cursos/"), api("/departamentos/")]).then(([cursos, departamentos]) => ({ cursos, departamentos })),
    [],
  );

  if (usuario) return <Navigate to="/" replace />;

  function mudar(campo) {
    return (evento) => setDados((atual) => ({ ...atual, [campo]: evento.target.value }));
  }

  async function aoEnviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    const comuns = { nome: dados.nome, email: dados.email, senha: dados.senha, numero_usp: dados.numero_usp };
    const corpo = perfil === "aluno"
      ? { ...comuns, curso: Number(dados.curso) || null, ano_ingresso: Number(dados.ano_ingresso) }
      : { ...comuns, departamento: Number(dados.departamento) || null, url_lattes: dados.url_lattes };
    try {
      const novo = await cadastrar(perfil, corpo);
      navegar(novo.perfil === "docente" ? "/meus-projetos" : "/", { replace: true });
    } catch (falha) {
      setErro(falha);
    } finally {
      setEnviando(false);
    }
  }

  const erroDe = (campo) => erro?.doCampo?.(campo);

  return (
    <div className="painel-estreito">
      <h1>Criar conta</h1>
      <div className="abas" role="tablist">
        {[["aluno", "Sou aluno"], ["docente", "Sou docente"]].map(([valor, rotulo]) => (
          <button
            key={valor}
            type="button"
            role="tab"
            aria-selected={perfil === valor}
            className={`aba${perfil === valor ? " aba-ativa" : ""}`}
            onClick={() => { setPerfil(valor); setErro(null); }}
          >
            {rotulo}
          </button>
        ))}
      </div>
      <form className="formulario" onSubmit={aoEnviar} noValidate>
        <Campo rotulo="Nome completo" id="nome" erro={erroDe("nome")}>
          <input id="nome" autoComplete="name" value={dados.nome} onChange={mudar("nome")} />
        </Campo>
        <Campo rotulo="Email USP" id="email" erro={erroDe("email")} ajuda="Use o seu email @usp.br.">
          <input id="email" type="email" autoComplete="email" value={dados.email} onChange={mudar("email")} />
        </Campo>
        <Campo rotulo="Senha" id="senha" erro={erroDe("senha")} ajuda="Pelo menos 8 caracteres, sem ser só números.">
          <input id="senha" type="password" autoComplete="new-password" value={dados.senha} onChange={mudar("senha")} />
        </Campo>
        <Campo rotulo="Número USP" id="numero_usp" erro={erroDe("numero_usp")}>
          <input id="numero_usp" inputMode="numeric" value={dados.numero_usp} onChange={mudar("numero_usp")} />
        </Campo>

        {perfil === "aluno" ? (
          <div className="linha-campos">
            <Campo rotulo="Curso" id="curso" erro={erroDe("curso") && "Selecione um curso."}>
              <select id="curso" value={dados.curso} onChange={mudar("curso")}>
                <option value="">Selecione...</option>
                {opcoes.dados?.cursos.map((curso) => (
                  <option key={curso.id_curso} value={curso.id_curso}>{curso.nome}</option>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Ano de ingresso" id="ano_ingresso" erro={erroDe("ano_ingresso")}>
              <input id="ano_ingresso" type="number" min="1950" max={ANO_ATUAL} value={dados.ano_ingresso} onChange={mudar("ano_ingresso")} />
            </Campo>
          </div>
        ) : (
          <>
            <Campo rotulo="Departamento" id="departamento" erro={erroDe("departamento") && "Selecione um departamento."}>
              <select id="departamento" value={dados.departamento} onChange={mudar("departamento")}>
                <option value="">Selecione...</option>
                {opcoes.dados?.departamentos.map((d) => (
                  <option key={d.id_departamento} value={d.id_departamento}>{d.sigla} · {d.nome}</option>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Currículo Lattes (opcional)" id="url_lattes" erro={erroDe("url_lattes")}>
              <input id="url_lattes" type="url" placeholder="http://lattes.cnpq.br/..." value={dados.url_lattes} onChange={mudar("url_lattes")} />
            </Campo>
          </>
        )}

        <Aviso>{opcoes.erro?.message}</Aviso>
        <Aviso>{erro?.geral?.() || erro?.message}</Aviso>
        <button type="submit" className="botao botao-largo" disabled={enviando}>
          {enviando ? "Criando conta..." : "Criar conta"}
        </button>
      </form>
      <p className="rodape-form">
        Já tem conta? <Link to="/entrar">Entrar</Link>
      </p>
    </div>
  );
}
