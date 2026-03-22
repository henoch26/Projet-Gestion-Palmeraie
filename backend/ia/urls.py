from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    AnomalieViewSet,
    PredictionScenarioViewSet,
    ParametreIAViewSet,
    prediction_view,
)

router = DefaultRouter()
router.register(r"anomalies", AnomalieViewSet, basename="anomalie")
router.register(r"scenarios", PredictionScenarioViewSet, basename="scenario")
router.register(r"parametres-ia", ParametreIAViewSet, basename="parametre-ia")

urlpatterns = router.urls + [
    path("predictions/", prediction_view),
]
