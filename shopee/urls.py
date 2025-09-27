# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("shop/info", views.Shop_info, name="shop_info"),
    path("products", views.get_product_info, name="product_list"),
    path("products/best/seller", views.get_top_products,
         name="product_best_seller"),
    path("products/sold", views.get_total_orders_and_buyers, name="total_sold"),
    
    path("orders", views.get_order_list, name="order_list"),
    path("orders/detail", views.get_order_detail, name="order_detail"),
    path("orders/tracking_number", views.get_tracking_number,
         name="get_tracking_number"),
    path("orders/get_tracking_info",
         views.get_tracking_info, name="get_tracking_info"),
    path("returns", views.get_return_list, name="return_list"),
    path("returns/detail", views.get_order_detail, name="return_detail"),
    path("products/best_seller", views.get_top_5_products)
]
