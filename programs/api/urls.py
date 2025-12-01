from rest_framework.routers import DefaultRouter

from ..api.views import (
    AlertViewSet,
    ChannelViewSet,
    ProgramInstanceViewSet,
    ProgramViewSet,
    ScheduleViewSet,
)

router = DefaultRouter()
router.register(r"channels", ChannelViewSet)
router.register(r"programs", ProgramViewSet)
router.register(r"instances", ProgramInstanceViewSet)
router.register(r"schedules", ScheduleViewSet)
router.register(r"alerts", AlertViewSet)

urlpatterns = router.urls
