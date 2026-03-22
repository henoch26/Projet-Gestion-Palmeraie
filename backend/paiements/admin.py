from django.contrib import admin
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "recolteur", "secteur", "net", "statut")
    list_filter = ("statut", "secteur")
    search_fields = ("reference", "recolteur__nom")
