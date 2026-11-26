export function Carregando({ texto = "Carregando..." }) {
  return (
    <p className="carregando" role="status">
      {texto}
    </p>
  );
}

export function Aviso({ tipo = "erro", children }) {
  if (!children) return null;
  return (
    <div className={`aviso aviso-${tipo}`} role={tipo === "erro" ? "alert" : "status"}>
      {children}
    </div>
  );
}

export function Campo({ rotulo, erro, ajuda, children, id }) {
  return (
    <div className={`campo${erro ? " campo-com-erro" : ""}`}>
      <label htmlFor={id}>{rotulo}</label>
      {children}
      {ajuda && !erro && <small className="ajuda">{ajuda}</small>}
      {erro && <small className="erro-campo">{erro}</small>}
    </div>
  );
}

const ROTULOS_STATUS = { pendente: "Pendente", aceita: "Aceita", recusada: "Recusada" };

export function SeloStatus({ status }) {
  return <span className={`selo selo-${status}`}>{ROTULOS_STATUS[status] || status}</span>;
}

export function Vazio({ titulo, children }) {
  return (
    <div className="vazio">
      <p className="vazio-titulo">{titulo}</p>
      {children && <div>{children}</div>}
    </div>
  );
}
