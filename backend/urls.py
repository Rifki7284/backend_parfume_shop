from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("api/account/", include("users.urls")),
    path("api/store/", include("store.urls")),
    path("drf-auth/", include("rest_framework.urls", namespace="drf")),
    path("",include("tiktok.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
