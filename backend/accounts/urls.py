from django.urls import path
from .views import login_view, me_view, health_view

urlpatterns = [
    path("auth/login/", login_view),
    path("auth/me/", me_view),
    # Healthcheck public (utile pour diagnostiquer l'acces DB)
    path("health/", health_view),
]
