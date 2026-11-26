import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Cabecalho() {
  const { usuario, sair } = useAuth();
  const navegar = useNavigate();
  const perfil = usuario?.perfil;

  async function aoSair() {
    await sair();
    navegar("/");
  }

  return (
    <header className="cabecalho">
      <div className="cabecalho-interno">
        <NavLink to="/" className="marca">
          <span className="marca-icone" aria-hidden="true">IC</span>
          ICsearch
        </NavLink>
        <nav className="navegacao">
          <NavLink to="/" end>Buscar</NavLink>
          {perfil === "aluno" && <NavLink to="/minhas-manifestacoes">Minhas manifestações</NavLink>}
          {perfil === "docente" && <NavLink to="/meus-projetos">Meus projetos</NavLink>}
          {perfil === "docente" && <NavLink to="/interessados">Interessados</NavLink>}
          {perfil === "admin" && <NavLink to="/painel">Painel de demanda</NavLink>}
        </nav>
        <div className="sessao">
          {usuario ? (
            <>
              <span className="sessao-nome" title={usuario.email}>{usuario.nome}</span>
              <button type="button" className="botao botao-discreto" onClick={aoSair}>Sair</button>
            </>
          ) : (
            <>
              <NavLink to="/entrar" className="botao botao-discreto">Entrar</NavLink>
              <NavLink to="/cadastro" className="botao">Cadastrar</NavLink>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
