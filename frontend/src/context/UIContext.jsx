// import { createContext,useContext,useState } from "react";

// const UIcontext = createContext(null);

// export function UIProvider({children}){
//     const [sidebarCollapsed,setSidebarCollapsed]=useState(false);
//     const toggleSidebar = () => setSidebarCollapsed((v) => !v);

//     return(
//         <UIcontext.Provider value={{sidebarCollapsed,toggleSidebar}}>
//             {children}
//         </UIcontext.Provider>
//     )
// }

// export function useUI(){
//     const ctx = useContext(UIcontext)
//     if (!ctx) throw new Error("useUI dois etre utilise a l'interieur de UIProvider")
//         return ctx;
// }