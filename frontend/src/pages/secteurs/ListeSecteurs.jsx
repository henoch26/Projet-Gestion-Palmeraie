import DataTable from "../../components/DataTable.jsx";

export default function ListeSecteurs() {
  const columns = [
    { key: "nom", label: "Nom" },
    { key: "superficie", label: "Superficie" },
    { key: "responsable", label: "Responsable" },
  ];

  const rows = [
    { nom: "Secteur A", superficie: "120 ha", responsable: "K. Kouassi" },
    { nom: "Secteur B", superficie: "95 ha", responsable: "M. Yao" },
    { nom: "Secteur C", superficie: "130 ha", responsable: "S. Traore" },
  ];

  return (
    <div className="page">
      <h2>Liste secteurs</h2>
      <DataTable columns={columns} rows={rows} pageSize={5} />
    </div>
  );
}
