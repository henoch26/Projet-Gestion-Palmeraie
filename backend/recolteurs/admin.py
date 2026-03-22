from django.contrib import admin
from .models import Recolteur


@admin.register(Recolteur)
class RecolteurAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "statut", "secteur", "contact", "created_at")
    search_fields = ("nom", "contact")
