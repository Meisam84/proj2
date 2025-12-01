from django.urls import path

from ..views_timeline import daily_timeline, timeline_reorder

urlpatterns = [
    path("", daily_timeline, name="timeline-day"),
    path("reorder/", timeline_reorder, name="timeline-reorder"),
]
