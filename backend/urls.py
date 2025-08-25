from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("accounts/", include("allauth.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/account/", include("users.urls")),
    path("api/store/", include("store.urls")),
    path("api/", include("cart.urls")),
    path("api/orders/", include("order.urls")),
    path("api/payments/", include("payment.urls")),
    path("",include("tiktok.urls")),
    # path("api-auth/", include("rest_framework.urls", namespace="drf"))

    path("auth/", include("drf_social_oauth2.urls", namespace="drf")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
