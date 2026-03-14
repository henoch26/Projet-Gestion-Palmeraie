import DataTable from "../../components/DataTable.jsx";

export default function HistoriqueRecoltes() {
  const columns = [
    { key: "date", label: "Date" },
    { key: "secteur", label: "Secteur" },
    { key: "tonnage", label: "Tonnage" },
  ];

  const rows = [
    { date: "2026-03-01", secteur: "Secteur A", tonnage: "42 t" },
    { date: "2026-03-03", secteur: "Secteur B", tonnage: "37 t" },
    { date: "2026-03-06", secteur: "Secteur C", tonnage: "50 t" },
  ];

  return (
    <div className="page">
      <h2>Historique recoltes</h2>
      <DataTable columns={columns} rows={rows} pageSize={5} />
    </div>
  );
}
