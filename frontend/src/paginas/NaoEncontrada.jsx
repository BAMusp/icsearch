import { Link } from "react-router-dom";
import { Vazio } from "../componentes/Basicos.jsx";

export default function NaoEncontrada() {
  return (
    <Vazio titulo="Página não encontrada.">
      <Link to="/" className="botao">Voltar para a busca</Link>
    </Vazio>
  );
}
