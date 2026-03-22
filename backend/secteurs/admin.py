from django.contrib import admin
from .models import Secteur


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "nom", "superficie_ha", "responsable", "actif")
    search_fields = ("code", "nom", "responsable")
