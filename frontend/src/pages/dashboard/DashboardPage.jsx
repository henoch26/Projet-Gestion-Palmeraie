import ChartCard from "../../components/ChartCard.jsx";
import { dashboardCharts } from "../../data/dashboardCharts.js";

console.log(dashboardCharts);

export default function Dashboard(){

//Cartes statistiques principales du dashboard
const stats = [
    { title: "Production totale", value: "12 450 t" },
    { title: "Production par secteur", value: "8 secteurs" },
    { title: "Récolteurs actifs", value: "126" },
    { title: "Rendement moyen", value: "3.8 t/ha" },
  ];


//Donnees des tableaux
 const secteurs = [
    { nom: "Secteur A", superficie: "120 ha", responsable: "K. Kouassi" },
    { nom: "Secteur B", superficie: "95 ha", responsable: "M. Yao" },
  ];

  const recoltes = [
    { date: "2026-03-01", secteur: "Secteur A", tonnage: "42 t" },
    { date: "2026-03-03", secteur: "Secteur B", tonnage: "37 t" },
  ];

  const paiements = [
    { recolteur: "A. Konan", montant: "120 000 FCFA", statut: "Payé" },
    { recolteur: "J. N'Guessan", montant: "95 000 FCFA", statut: "En attente" },
  ];

  const anomalies = [
    { type: "Baisse rendement", zone: "Secteur C", niveau: "Moyen" },
    { type: "Retard récolte", zone: "Secteur D", niveau: "Élevé" },
  ];


  return (
    <div className="page">
      <section className="stats-grid">
        {stats.map((s) => (
          <article key={s.title} className="stat-card">
            <h3>{s.title}</h3>
            <p>{s.value}</p>
          </article>
        ))}
      </section>

{/* Section des graphiques */}
      <section className="charts-grid">
        {
          dashboardCharts.map((cfg)=>(
            <ChartCard key={cfg.title} title={cfg.title} type={cfg.type} data={cfg.data}/>
          ))
        }
      </section>
{/* Fin section graphiques */}

      <section className="tables-grid">
        <article className="table-card">
          <h3>Liste secteurs</h3>
          <ul>
            {secteurs.map((s) => (
              <li key={s.nom}>{s.nom} - {s.superficie} - {s.responsable}</li>
            ))}
          </ul>
        </article>

        <article className="table-card">
          <h3>Historique récoltes</h3>
          <ul>
            {recoltes.map((r, i) => (
              <li key={i}>{r.date} - {r.secteur} - {r.tonnage}</li>
            ))}
          </ul>
        </article>

        <article className="table-card">
          <h3>Paiements</h3>
          <ul>
            {paiements.map((p, i) => (
              <li key={i}>{p.recolteur} - {p.montant} - {p.statut}</li>
            ))}
          </ul>
        </article>

        <article className="table-card">
          <h3>Anomalies</h3>
          <ul>
            {anomalies.map((a, i) => (
              <li key={i}>{a.type} - {a.zone} - {a.niveau}</li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}