import DataTable from "../../components/DataTable.jsx";

export default function PaiementsPage() {
  const columns = [
    { key: "recolteur", label: "Recolteur" },
    { key: "montant", label: "Montant" },
    { key: "statut", label: "Statut" },
  ];

  const rows = [
    { recolteur: "A. Konan", montant: "120 000 FCFA", statut: "Paye" },
    { recolteur: "J. Nguessan", montant: "95 000 FCFA", statut: "En attente" },
    { recolteur: "B. Ouattara", montant: "110 000 FCFA", statut: "Paye" },
  ];

  return (
    <div className="page">
      <h2>Paiements</h2>
      <DataTable columns={columns} rows={rows} pageSize={5} />
    </div>
  );
}
