import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, lerToken, salvarToken } from "./api.js";

const AuthContexto = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(Boolean(lerToken()));

  useEffect(() => {
    if (!lerToken()) return;
    api("/auth/eu/")
      .then(setUsuario)
      .catch(() => salvarToken(null))
      .finally(() => setCarregando(false));
  }, []);

  const iniciarSessao = useCallback((resposta) => {
    salvarToken(resposta.token);
    setUsuario(resposta.usuario);
    return resposta.usuario;
  }, []);

  const entrar = useCallback(
    async (email, senha) => iniciarSessao(await api("/auth/login/", { metodo: "POST", corpo: { email, senha } })),
    [iniciarSessao],
  );

  const cadastrar = useCallback(
    async (perfil, dados) => iniciarSessao(await api(`/auth/cadastro/${perfil}/`, { metodo: "POST", corpo: dados })),
    [iniciarSessao],
  );

  const sair = useCallback(async () => {
    try {
      await api("/auth/logout/", { metodo: "POST" });
    } finally {
      salvarToken(null);
      setUsuario(null);
    }
  }, []);

  const valor = useMemo(
    () => ({ usuario, carregando, entrar, cadastrar, sair }),
    [usuario, carregando, entrar, cadastrar, sair],
  );

  return <AuthContexto.Provider value={valor}>{children}</AuthContexto.Provider>;
}

export function useAuth() {
  return useContext(AuthContexto);
}
