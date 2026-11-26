import { useCallback, useEffect, useState } from "react";

export function useCarregar(buscar, dependencias) {
  const [estado, setEstado] = useState({ dados: null, erro: null, carregando: true });

  const carregar = useCallback(() => {
    let ativo = true;
    setEstado((atual) => ({ ...atual, carregando: true, erro: null }));
    buscar()
      .then((dados) => ativo && setEstado({ dados, erro: null, carregando: false }))
      .catch((erro) => ativo && setEstado({ dados: null, erro, carregando: false }));
    return () => {
      ativo = false;
    };
  }, dependencias);

  useEffect(carregar, [carregar]);

  const setDados = useCallback((atualizar) => {
    setEstado((atual) => ({
      ...atual,
      dados: typeof atualizar === "function" ? atualizar(atual.dados) : atualizar,
    }));
  }, []);

  return { ...estado, recarregar: carregar, setDados };
}

export function formatarData(valor) {
  if (!valor) return "";
  const data = valor.length === 10 ? new Date(`${valor}T12:00:00`) : new Date(valor);
  return data.toLocaleDateString("pt-BR");
}

export function plural(quantidade, singular, plural) {
  return `${quantidade} ${quantidade === 1 ? singular : plural}`;
}
