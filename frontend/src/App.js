import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Avisolegal from "./pages/AvisoLegal"
import AcercaDe from "./pages/AcercaDe";
import Contacto from "./pages/Contacto";
import Login from "./pages/Login"
import Signin from "./pages/Singin"
import Bienvenida from "./pages/Bienvenida"
import GestionarPeril from "./pages/GestionarPerfil"
import AsesoriaIA from "./pages/AsesoriaIA";
import ScrollTop from "./components/ScrollTop"
import ConsultarAgenteTransito from "./pages/ConsultarAgenteTransito"
import GuiaArticulo from "./pages/GuiaArticulo"
import GuiaCategoria from "./pages/GuiaCategoria"
import RutaProtegida from "./services/rutaProtegida";
import RutaAdmin from "./admin/RutaAdmin";
import AdminLayout from "./admin/AdminLayout";
import Resumen from "./admin/pages/Resumen";
import Calidad from "./admin/pages/Calidad";
import Usuarios from "./admin/pages/Usuarios";
import Fuentes from "./admin/pages/Fuentes";
import Actividad from "./admin/pages/Actividad";

function App() {
  return (
    <Router>
      <div className="d-flex flex-column min-vh-100">
        <main className="flex-grow-1 d-flex flex-column">
        <ScrollTop />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/Aviso-legal" element={<Avisolegal/>} />
            <Route path="/Acerca-de" element={<AcercaDe/>} />            
            <Route path="/Contacto" element={<Contacto/>} />
            <Route path="/Login" element={<Login/>} />      
            <Route path="/Sing-in" element={<Signin/>} />
            <Route path="/Bienvenida" element={<RutaProtegida> <Bienvenida/> </RutaProtegida>} />
            <Route path="/Gestionar-perfil" element={<RutaProtegida> <GestionarPeril/> </RutaProtegida>} />
            <Route path="/asesoria-ia" element={<RutaProtegida> <AsesoriaIA /> </RutaProtegida>} />
            <Route path="/admin" element={<RutaProtegida> <RutaAdmin> <AdminLayout /> </RutaAdmin> </RutaProtegida>}>
              <Route index element={<Resumen />} />
              <Route path="calidad" element={<Calidad />} />
              <Route path="usuarios" element={<Usuarios />} />
              <Route path="fuentes" element={<Fuentes />} />
              <Route path="actividad" element={<Actividad />} />
            </Route>
            <Route path="/BienvenidaAdmin" element={<Navigate to="/admin" replace />} />
            <Route path="/AdministrarUsuario" element={<Navigate to="/admin" replace />} />
            <Route path="/Estadisticas" element={<Navigate to="/admin" replace />} />
            <Route path="/ConsultarAgenteTransito" element={<ConsultarAgenteTransito />} />
            <Route path="/guia/calculadoras" element={<Navigate to="/Bienvenida#calculadoras" replace />} />
            <Route path="/guia/calculadoras/:herramientaSlug" element={<Navigate to="/Bienvenida#calculadoras" replace />} />
            <Route path="/guia/:categoriaSlug/:articuloSlug" element={<RutaProtegida> <GuiaArticulo /> </RutaProtegida>} />
            <Route path="/guia/:categoriaSlug" element={<RutaProtegida> <GuiaCategoria /> </RutaProtegida>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;