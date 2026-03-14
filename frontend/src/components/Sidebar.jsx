import { NavLink } from "react-router-dom";
// import { useUI } from "../context/UIContext";

export default function Sidebar(){
    // const { sidebarCollapsed } = useUI();

    return(
        <aside className="sidebar">
            <nav className="sidebar-nav">
                <NavLink to="/dashboard">Dashboard</NavLink>
                <NavLink to="/secteurs">Secteurs</NavLink>
                <NavLink to="/recolteurs">Récolteurs</NavLink>
                <NavLink to="/recoltes">Récoltes</NavLink>
                <NavLink to="/paiements">Paiements</NavLink>
                <NavLink to="/predictions">Prédictions IA</NavLink>
                <NavLink to="/anomalies">Anomalies</NavLink>
            </nav>
        </aside>
    )
}