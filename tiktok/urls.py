# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("tiktok/authorize/", views.tiktok_authorize, name="authorize"),
    path("tiktok/callback/", views.TikTokCallbackView, name="tiktok_callback"),
    path("tiktok/auth/shop",views.get_auth_shop), 
    path("tiktok/order/list",views.get_orders_list)
]
