const CHAVE_TOKEN = "icsearch_token";

export function lerToken() {
  try {
    return localStorage.getItem(CHAVE_TOKEN);
  } catch {
    return null;
  }
}

export function salvarToken(token) {
  try {
    if (token) {
      localStorage.setItem(CHAVE_TOKEN, token);
    } else {
      localStorage.removeItem(CHAVE_TOKEN);
    }
  } catch {
    return;
  }
}

function primeiraMensagem(dados) {
  if (!dados) return null;
  if (typeof dados === "string") return dados;
  if (Array.isArray(dados)) return primeiraMensagem(dados[0]);
  if (dados.detail) return dados.detail;
  if (dados.non_field_errors) return primeiraMensagem(dados.non_field_errors);
  const primeiroCampo = Object.keys(dados)[0];
  return primeiroCampo ? primeiraMensagem(dados[primeiroCampo]) : null;
}

export class ErroApi extends Error {
  constructor(status, dados) {
    super(primeiraMensagem(dados) || "Não foi possível falar com o servidor.");
    this.status = status;
    this.dados = dados && typeof dados === "object" && !Array.isArray(dados) ? dados : {};
  }

  doCampo(nome) {
    const valor = this.dados[nome];
    if (!valor) return null;
    return Array.isArray(valor) ? valor.join(" ") : String(valor);
  }

  geral() {
    const campos = Object.keys(this.dados).filter((nome) => nome !== "detail" && nome !== "non_field_errors");
    if (this.dados.detail || this.dados.non_field_errors || campos.length === 0) return this.message;
    return "Confira os campos destacados.";
  }
}

export async function api(caminho, { metodo = "GET", corpo, params } = {}) {
  const url = new URL(`/api${caminho}`, window.location.origin);
  Object.entries(params || {}).forEach(([nome, valor]) => {
    if (valor !== undefined && valor !== null && valor !== "") {
      url.searchParams.set(nome, valor);
    }
  });

  const cabecalhos = { Accept: "application/json" };
  if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
  const token = lerToken();
  if (token) cabecalhos.Authorization = `Token ${token}`;

  let resposta;
  try {
    resposta = await fetch(url, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroApi(0, { detail: "Servidor fora do ar. Confira se o Django está rodando." });
  }

  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) throw new ErroApi(resposta.status, dados);
  return dados;
}
