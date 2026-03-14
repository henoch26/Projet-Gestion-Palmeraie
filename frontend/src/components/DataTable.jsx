import { useMemo, useState } from "react";

export default function DataTable({ columns, rows, pageSize = 5 }) {
  // Texte recherché dans la barre de recherche
  const [query, setQuery] = useState("");

  // Colonne sur laquelle on trie
  const [sortKey, setSortKey] = useState(null);

  // Sens du tri (asc/desc)
  const [sortDir, setSortDir] = useState("asc");

  // Page actuelle
  const [page, setPage] = useState(1);

  // Filtrage des lignes selon la recherche
  const filtered = useMemo(() => {
    if (!query) return rows;
    const q = query.toLowerCase();
    return rows.filter((row) =>
      columns.some((col) => String(row[col.key]).toLowerCase().includes(q))
    );
  }, [rows, columns, query]);

  // Tri des lignes
  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (va === vb) return 0;
      return va > vb ? dir : -dir;
    });
  }, [filtered, sortKey, sortDir]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const start = (page - 1) * pageSize;
  const paged = sorted.slice(start, start + pageSize);

  // Gestion du tri au clic
  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
    setPage(1);
  };
// console.log(rows);
// console.log(filtered);



const test = columns.map((c)=>{
    return c.key,c.label
})
console.log(test)


    return(
        <div className="table-wrapper">
            {/* Barre de recherche */}
            <div className="table-tools">
                <input
                    className="table-search"
                    placeholder="Recharcher..."
                    value={query}
                    onChange={(e) => {
                    setQuery(e.target.value);
                    setPage(1);
                    }}   
                />
            </div>

            {/* Tableau */}
            <table className="data-table">
                <thead>
                    <tr>
                        {
                        columns.map((c)=>(
                        <th 
                        key={c.key} onClick={()=>toggleSort(c.key)}>
                            {c.label ?? c.key}
                            {sortKey=== c.key ? (sortDir === "asc" ? " ▲ " : " ▼ ") : ""}
                        </th>
                        ))
                        }
                    </tr>
                </thead>
                <tbody>
                    {paged.map((row, i) => (
                        <tr key={i}>
                        {columns.map((c) => (
                            <td key={c.key}>{row[c.key]}</td>
                        ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {/* Pagination */}
            <div className="table-pagination">
                <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                Precedent
                </button>
                <span>
                Page {page} / {totalPages}
                </span>
                <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                Suivant
                </button>
            </div>
        </div>
    )
}





// import { useMemo, useState } from "react";

// export default function DataTable({ columns, rows, pageSize = 5 }) {
//   const [query, setQuery] = useState("");
//   const [sortKey, setSortKey] = useState(null);
//   const [sortDir, setSortDir] = useState("asc");
//   const [page, setPage] = useState(1);

//   const filtered = useMemo(() => {
//     if (!query) return rows;
//     const q = query.toLowerCase();
//     return rows.filter((row) =>
//       columns.some((col) => String(row[col.key]).toLowerCase().includes(q))
//     );
//   }, [rows, columns, query]);

//   const sorted = useMemo(() => {
//     if (!sortKey) return filtered;
//     const dir = sortDir === "asc" ? 1 : -1;
//     return [...filtered].sort((a, b) => {
//       const va = a[sortKey];
//       const vb = b[sortKey];
//       if (va === vb) return 0;
//       return va > vb ? dir : -dir;
//     });
//   }, [filtered, sortKey, sortDir]);

//   const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
//   const start = (page - 1) * pageSize;
//   const paged = sorted.slice(start, start + pageSize);

//   const toggleSort = (key) => {
//     if (sortKey === key) {
//       setSortDir(sortDir === "asc" ? "desc" : "asc");
//     } else {
//       setSortKey(key);
//       setSortDir("asc");
//     }
//     setPage(1);
//   };

//   return (
//     <div className="table-wrapper">
//       <div className="table-tools">
//         <input
//           className="table-search"
//           placeholder="Rechercher..."
//           value={query}
//           onChange={(e) => {
//             setQuery(e.target.value);
//             setPage(1);
//           }}
//         />
//       </div>

//       <table className="data-table">
//         <thead>
//           <tr>
//             {columns.map((c) => (
//               <th key={c.key} onClick={() => toggleSort(c.key)}>
//                 {c.label ?? c.key}
//                 {sortKey === c.key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
//               </th>
//             ))}
//           </tr>
//         </thead>
//         <tbody>
//           {paged.map((row, i) => (
//             <tr key={i}>
//               {columns.map((c) => (
//                 <td key={c.key}>{row[c.key]}</td>
//               ))}
//             </tr>
//           ))}
//         </tbody>
//       </table>

//       <div className="table-pagination">
//         <button disabled={page === 1} onClick={() => setPage(page - 1)}>
//           Precedent
//         </button>
//         <span>
//           Page {page} / {totalPages}
//         </span>
//         <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
//           Suivant
//         </button>
//       </div>
//     </div>
//   );
// }
