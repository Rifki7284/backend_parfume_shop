# urls.py
from django.urls import path
from . import views
from .views import TrackBinderbyteView

urlpatterns = [
    path("authorize/", views.tiktok_authorize, name="tiktok_authorize"),
    path("callback/", views.TikTokCallbackView, name="tiktok_callback"),
    path("auth/shop/", views.get_auth_shop),
    path("tracking/binderbyte/", TrackBinderbyteView.as_view(),
         name="tracking-binderbyte"),
    path("order/<str:cipher>/list", views.get_orders_list),
    path("return/<str:cipher>/list", views.get_orders_return),
    path("product/<str:cipher>/<str:id>/", views.get_product),
    path("shop/<str:cipher>/performance", views.get_shop_performance),
    path("shop/stats/<str:cipher>/performance",
         views.get_shop_performance_stats),
    path("shop/stats/<str:cipher>/performance/year",
         views.get_tiktok_orders_year),
    path("shop/<str:cipher>/top-product", views.get_top_products),
    path("shop/<str:cipher>/product/performance",
         views.get_shop_product_performance)
]
