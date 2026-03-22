from django.contrib import admin
from .models import Anomalie


@admin.register(Anomalie)
class AnomalieAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "type", "zone", "niveau")
    list_filter = ("niveau",)
