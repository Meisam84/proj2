from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("programs.api.urls")),
    path("channels/<int:channel_id>/schedule/<str:date_str>/", include("programs.urls.timeline_urls")),
]
