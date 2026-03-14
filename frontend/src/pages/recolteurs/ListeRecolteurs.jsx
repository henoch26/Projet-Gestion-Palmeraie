import DataTable from "../../components/DataTable.jsx";

export default function ListeRecolteurs() {
  const columns = [
    { key: "nom", label: "Nom" },
    { key: "secteur", label: "Secteur" },
    { key: "statut", label: "Statut" },
  ];

  const rows = [
    { nom: "A. Konan", secteur: "Secteur A", statut: "Actif" },
    { nom: "J. Nguessan", secteur: "Secteur B", statut: "Actif" },
    { nom: "B. Ouattara", secteur: "Secteur C", statut: "Inactif" },
  ];

  return (
    <div className="page">
      <h2>Liste recolteurs</h2>
      <DataTable columns={columns} rows={rows} pageSize={5} />
    </div>
  );
}
