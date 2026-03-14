// import { useUI } from "../context/UIContext"

export default function Navbar(){
    // const { toggleSidebar } = useUI();

    return (
        <header className="topbar">
            <div className="topbar-left">
                <div className="topbar-title">Dashboard principal</div>
            </div>
            <div className="topbar-actions">
                <button className="btn-ghost">FR</button>
                <button className="btn-ghost">EN</button>
            </div>
        </header>
    )
}

