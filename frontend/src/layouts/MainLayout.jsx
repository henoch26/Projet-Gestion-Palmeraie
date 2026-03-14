import {Outlet} from "react-router-dom"
import Sidebar from "../components/Sidebar.jsx"
import Navbar from "../components/Navbar.jsx"

export default function MainLayout(){
    return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-shell">
        <Navbar />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
    )
}

