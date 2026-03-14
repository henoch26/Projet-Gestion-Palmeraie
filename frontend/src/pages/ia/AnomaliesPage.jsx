import DataTable from "../../components/DataTable.jsx";

export default function AnomaliesPage() {
  const columns = [
    { key: "type", label: "Type" },
    { key: "zone", label: "Zone" },
    { key: "niveau", label: "Niveau" },
  ];

  const rows = [
    { type: "Baisse rendement", zone: "Secteur C", niveau: "Moyen" },
    { type: "Retard recolte", zone: "Secteur D", niveau: "Eleve" },
    { type: "Humidite anormale", zone: "Secteur A", niveau: "Faible" },
  ];

  return (
    <div className="page">
      <h2>Anomalies</h2>
      <DataTable columns={columns} rows={rows} pageSize={5} />
    </div>
  );
}
