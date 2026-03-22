from django.core.management.base import BaseCommand

from ia.ml_engine import train_model


class Command(BaseCommand):
    help = "Entraine le modele IA a partir des ParametreIA + recoltes"

    def handle(self, *args, **options):
        # Lance l'entrainement et affiche les metriques
        try:
            meta = train_model()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Echec entrainement: {exc}"))
            return

        self.stdout.write(self.style.SUCCESS("Modele IA entrainne."))
        self.stdout.write(f"Nombre d'exemples: {meta.get('rows')}")
        metrics = meta.get("metrics", {})
        self.stdout.write(f"MAE: {metrics.get('mae')}")
        self.stdout.write(f"RMSE: {metrics.get('rmse')}")
        self.stdout.write(f"R2: {metrics.get('r2')}")
