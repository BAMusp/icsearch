import { Route, Routes } from "react-router-dom";
import Cabecalho from "./componentes/Cabecalho.jsx";
import RotaProtegida from "./componentes/RotaProtegida.jsx";
import Busca from "./paginas/Busca.jsx";
import Cadastro from "./paginas/Cadastro.jsx";
import Entrar from "./paginas/Entrar.jsx";
import FormularioProjeto from "./paginas/FormularioProjeto.jsx";
import Interessados from "./paginas/Interessados.jsx";
import MeusProjetos from "./paginas/MeusProjetos.jsx";
import MinhasManifestacoes from "./paginas/MinhasManifestacoes.jsx";
import NaoEncontrada from "./paginas/NaoEncontrada.jsx";
import Painel from "./paginas/Painel.jsx";
import Projeto from "./paginas/Projeto.jsx";

export default function App() {
  return (
    <>
      <Cabecalho />
      <main className="conteudo">
        <Routes>
          <Route path="/" element={<Busca />} />
          <Route path="/projetos/:id" element={<Projeto />} />
          <Route path="/entrar" element={<Entrar />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route
            path="/minhas-manifestacoes"
            element={<RotaProtegida perfil="aluno"><MinhasManifestacoes /></RotaProtegida>}
          />
          <Route
            path="/meus-projetos"
            element={<RotaProtegida perfil="docente"><MeusProjetos /></RotaProtegida>}
          />
          <Route
            path="/meus-projetos/novo"
            element={<RotaProtegida perfil="docente"><FormularioProjeto /></RotaProtegida>}
          />
          <Route
            path="/meus-projetos/:id"
            element={<RotaProtegida perfil="docente"><FormularioProjeto /></RotaProtegida>}
          />
          <Route
            path="/interessados"
            element={<RotaProtegida perfil="docente"><Interessados /></RotaProtegida>}
          />
          <Route
            path="/painel"
            element={<RotaProtegida perfil="admin"><Painel /></RotaProtegida>}
          />
          <Route path="*" element={<NaoEncontrada />} />
        </Routes>
      </main>
      <footer className="rodape">ICsearch · Escola Politécnica da USP · PMR3304</footer>
    </>
  );
}
