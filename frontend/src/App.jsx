import "./App.css"
import { BrowserRouter,Routes,Route,Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import DashboardPage from "./pages/dashboard/DashboardPage.jsx";
import ListeSecteurs from "./pages/secteurs/ListeSecteurs.jsx";
import ListeRecolteurs from "./pages/recolteurs/ListeRecolteurs.jsx";
import HistoriqueRecoltes from "./pages/recoltes/HistoriqueRecoltes.jsx";
import PredictionPage from "./pages/ia/PredictionPage.jsx";
import AnomaliesPage from "./pages/ia/AnomaliesPage.jsx";

export default function App(){
  return(
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />}/>
          <Route path="/dashboard" element={<DashboardPage />}/>
          <Route path="/secteurs" element={<ListeSecteurs  />}/>
          <Route path="/recolteurs" element={<ListeRecolteurs  />}/>
          <Route path="/recoltes" element={<HistoriqueRecoltes  />}/>
          <Route path="/predictions" element={<PredictionPage  />}/>
          <Route path="/anomalies" element={<AnomaliesPage  />}/>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

