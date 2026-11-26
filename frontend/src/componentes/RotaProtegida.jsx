import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Aviso, Carregando } from "./Basicos.jsx";

export default function RotaProtegida({ perfil, children }) {
  const { usuario, carregando } = useAuth();
  const local = useLocation();

  if (carregando) return <Carregando />;
  if (!usuario) return <Navigate to="/entrar" replace state={{ de: local.pathname + local.search }} />;
  if (perfil && usuario.perfil !== perfil) {
    return <Aviso>Esta página é restrita ao perfil {perfil}.</Aviso>;
  }
  return children;
}
