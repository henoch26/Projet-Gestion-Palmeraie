from rest_framework.routers import DefaultRouter
from .views import SecteurViewSet

router = DefaultRouter()
router.register(r"secteurs", SecteurViewSet, basename="secteur")

urlpatterns = router.urls
