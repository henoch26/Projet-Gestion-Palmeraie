import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from secteurs.models import Secteur
from recolteurs.models import Recolteur
from ia.models import Anomalie
from paiements.models import Paiement
from recoltes.models import (
    FicheRecolte,
    SuperviseurAdjoint,
    FicheRecolteLigne,
    FicheRecolteDetail,
    FicheRecuVente,
)
from ia.models import ParametreIA


class Command(BaseCommand):
    help = "Insere des donnees de depart (secteurs, recolteurs, paiements, anomalies, fiches)"

    def handle(self, *args, **options):
        # Seed deterministe pour obtenir les memes donnees a chaque execution
        random.seed(42)

        # 1) Secteurs (codes fixes)
        secteurs_data = [
            {"code": "GP_1", "nom": "GP 1"},
            {"code": "GP_2", "nom": "GP 2"},
            {"code": "RTE_BOUB", "nom": "Rte Boub"},
            {"code": "PM_1", "nom": "PM 1"},
            {"code": "PM_2", "nom": "PM 2"},
            {"code": "JC_1", "nom": "JC 1"},
            {"code": "JC_2", "nom": "JC 2"},
            {"code": "CO", "nom": "CO"},
            {"code": "AA", "nom": "AA"},
        ]

        for s in secteurs_data:
            Secteur.objects.get_or_create(
                code=s["code"], defaults={"nom": s["nom"], "responsable": "", "actif": True}
            )

        secteurs = list(Secteur.objects.all())
        self.stdout.write(self.style.SUCCESS("Secteurs: OK"))

        # 2) Recolteurs (on garantit un minimum)
        recolteurs_base = [
            {"nom": "A. Konan", "statut": "Actif"},
            {"nom": "J. Nguessan", "statut": "Actif"},
            {"nom": "B. Ouattara", "statut": "Inactif"},
            {"nom": "K. Kouadio", "statut": "Actif"},
            {"nom": "S. Traore", "statut": "Actif"},
            {"nom": "P. Yao", "statut": "Actif"},
        ]

        for r in recolteurs_base:
            Recolteur.objects.get_or_create(
                nom=r["nom"],
                defaults={
                    "secteur": random.choice(secteurs),
                    "statut": r["statut"],
                    "contact": "07 11 22 33 44",
                },
            )

        # Si besoin, on complete jusqu'a un minimum de recolteurs
        target_recolteurs = 12
        recolteurs = list(Recolteur.objects.all())
        if len(recolteurs) < target_recolteurs:
            missing = target_recolteurs - len(recolteurs)
            for i in range(missing):
                Recolteur.objects.create(
                    nom=f"Recolteur {len(recolteurs) + i + 1}",
                    secteur=random.choice(secteurs),
                    statut="Actif",
                    contact=f"07 {random.randint(10,99)} {random.randint(10,99)} "
                            f"{random.randint(10,99)} {random.randint(10,99)}",
                )

        recolteurs = list(Recolteur.objects.all())
        self.stdout.write(self.style.SUCCESS("Recolteurs: OK"))

        # 3) Anomalies (on ajoute un petit stock si besoin)
        target_anomalies = 10
        if Anomalie.objects.count() < target_anomalies:
            types = ["Baisse rendement", "Retard recolte", "Panne machine", "Pluie forte"]
            niveaux = ["Faible", "Moyen", "Eleve"]
            for i in range(target_anomalies - Anomalie.objects.count()):
                Anomalie.objects.create(
                    date=timezone.now().date() - timedelta(days=random.randint(0, 60)),
                    type=random.choice(types),
                    zone=f"Secteur {random.choice(['A', 'B', 'C', 'D'])}",
                    niveau=random.choice(niveaux),
                    description=f"Anomalie detectee #{i+1}",
                )
        self.stdout.write(self.style.SUCCESS("Anomalies: OK"))

        # 4) Paiements (avec periodes mois / trimestre / semestre / annee)
        target_paiements = 100
        existing_paiements = Paiement.objects.count()
        if existing_paiements < target_paiements:
            # Liste de periodes variees
            months = [
                "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
                "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
            ]
            years = [2024, 2025, 2026]
            periodes = []
            for y in years:
                periodes.extend([f"{m} {y}" for m in months])
                periodes.extend([f"T{t} {y}" for t in range(1, 5)])
                periodes.extend([f"S{s} {y}" for s in range(1, 3)])
                periodes.append(f"Annee {y}")

            statuts = ["Paye", "En attente", "En retard", "Annule"]

            for i in range(target_paiements - existing_paiements):
                rec = random.choice(recolteurs)
                date = timezone.now().date() - timedelta(days=random.randint(1, 420))
                brut = random.randint(60000, 220000)
                bonus = random.choice([0, 2000, 5000, 10000])
                penalite = random.choice([0, 0, 2000, 5000])
                net = brut + bonus - penalite

                Paiement.objects.create(
                    date=date,
                    recolteur=rec,
                    secteur=rec.secteur,
                    periode=random.choice(periodes),
                    brut=brut,
                    bonus=bonus,
                    penalite=penalite,
                    net=net,
                    statut=random.choice(statuts),
                    reference=f"TX-{date.year}-{existing_paiements + i + 1:05d}",
                    commentaire="Generation automatique",
                )
        self.stdout.write(self.style.SUCCESS("Paiements: OK"))

        # 5) Fiches de recolte (100 fiches)
        target_fiches = 100
        existing_fiches = FicheRecolte.objects.count()
        if existing_fiches < target_fiches:
            today = timezone.now().date()
            superviseurs = ["S. Traore", "K. Kouassi", "A. Bamba", "I. Kouadio"]
            adjoints = ["P. Yao", "M. N'Guessan", "L. Koffi", "D. Konan"]

            # Helper: cree une ligne + details et calcule PAYE
            def create_line(fiche, rec, regime_type, details):
                rates = {
                    "grands": fiche.bareme_grands,
                    "moyens": fiche.bareme_moyens,
                    "petits": fiche.bareme_petits,
                }
                total = sum(d["quantite"] for d in details)
                paye_amount = total * rates.get(regime_type, 0)

                line = FicheRecolteLigne.objects.create(
                    fiche=fiche,
                    recolteur=rec,
                    recolteur_nom=rec.nom,
                    regime_type=regime_type,
                    paye_amount=paye_amount,
                )

                for det in details:
                    FicheRecolteDetail.objects.create(
                        ligne=line,
                        secteur=det["secteur"],
                        secteur_code=det["secteur"].code,
                        quantite=det["quantite"],
                    )

                return line

            for i in range(target_fiches - existing_fiches):
                # Date et en-tete de fiche
                fiche = FicheRecolte.objects.create(
                    date=today - timedelta(days=existing_fiches + i),
                    superviseur_general=random.choice(superviseurs),
                    bareme_grands=60,
                    bareme_moyens=50,
                    bareme_petits=25,
                    depense_nourriture=random.randint(8000, 25000),
                    depense_transport=random.randint(4000, 12000),
                    observations="RAS",
                )

                # Superviseurs adjoints (1 a 2)
                for _ in range(random.randint(1, 2)):
                    SuperviseurAdjoint.objects.create(
                        fiche=fiche,
                        nom=random.choice(adjoints),
                        secteur_ou_recolteur=random.choice(secteurs).code,
                    )

                # Lignes recolteurs (3 a 5 recolteurs par fiche)
                reco_sample = random.sample(recolteurs, k=min(len(recolteurs), random.randint(3, 5)))
                for rec in reco_sample:
                    for regime_type in ["grands", "moyens", "petits"]:
                        # 3 secteurs par ligne pour garder un volume raisonnable
                        secteur_sample = random.sample(secteurs, k=min(len(secteurs), 3))
                        details = [
                            {"secteur": s, "quantite": random.randint(5, 40)}
                            for s in secteur_sample
                        ]
                        create_line(fiche, rec, regime_type, details)

                # Recu de vente (1 par fiche)
                FicheRecuVente.objects.create(
                    fiche=fiche,
                    date=fiche.date,
                    client=random.choice(["SAPH", "PALMCI", "OILPALM"]),
                    pesee_kg=random.randint(1800, 3200),
                    non_conformes_pct=random.randint(0, 5),
                    montant=random.randint(800000, 1800000),
                )

            self.stdout.write(self.style.SUCCESS("Fiches recolte: OK"))

        # 6) Parametres IA (historique de base)
        if ParametreIA.objects.count() < 12:
            today = timezone.now().date().replace(day=1)
            for i in range(12):
                ParametreIA.objects.create(
                    date=today - timedelta(days=30 * i),
                    frequency="month",
                    secteur=None,
                    rainfall_mm=random.randint(150, 280),
                    temperature_c=random.randint(24, 30),
                    workforce_count=random.randint(80, 140),
                    fertilizer_kg_ha=random.randint(60, 110),
                    maintenance_index=random.randint(60, 90),
                    nonconformity_pct=random.randint(1, 6),
                    active_area_ha=100,
                    note="Parametres generes",
                )
            self.stdout.write(self.style.SUCCESS("Parametres IA: OK"))

        self.stdout.write(self.style.SUCCESS("Seed termine."))
