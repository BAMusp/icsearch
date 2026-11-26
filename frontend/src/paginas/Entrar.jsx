import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Aviso, Campo } from "../componentes/Basicos.jsx";

export default function Entrar() {
  const { usuario, entrar } = useAuth();
  const navegar = useNavigate();
  const destino = useLocation().state?.de || "/";
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  if (usuario) return <Navigate to={destino} replace />;

  async function aoEnviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await entrar(email, senha);
      navegar(destino, { replace: true });
    } catch (falha) {
      setErro(falha.status === 400 ? "Email ou senha incorretos." : falha.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="painel-estreito">
      <h1>Entrar</h1>
      <form className="formulario" onSubmit={aoEnviar}>
        <Campo rotulo="Email USP" id="email">
          <input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </Campo>
        <Campo rotulo="Senha" id="senha">
          <input id="senha" type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
        </Campo>
        <Aviso>{erro}</Aviso>
        <button type="submit" className="botao botao-largo" disabled={enviando}>
          {enviando ? "Entrando..." : "Entrar"}
        </button>
      </form>
      <p className="rodape-form">
        Ainda não tem conta? <Link to="/cadastro">Cadastre-se</Link>
      </p>
    </div>
  );
}
