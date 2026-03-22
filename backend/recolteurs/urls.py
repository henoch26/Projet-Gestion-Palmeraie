from rest_framework.routers import DefaultRouter
from .views import RecolteurViewSet

router = DefaultRouter()
router.register(r"recolteurs", RecolteurViewSet, basename="recolteur")

urlpatterns = router.urls
