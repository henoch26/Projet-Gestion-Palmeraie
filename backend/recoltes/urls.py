from rest_framework.routers import DefaultRouter
from .views import FicheRecolteViewSet

router = DefaultRouter()
router.register(r"recoltes", FicheRecolteViewSet, basename="fiche-recolte")

urlpatterns = router.urls
