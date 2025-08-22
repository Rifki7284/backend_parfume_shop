from django.urls import path
from .views import pay_order, order_detail, order_list,checkout

urlpatterns = [
    path("", order_list, name="order-list"),              # GET /api/orders/
    path("<int:pk>/", order_detail, name="order-detail"), # GET /api/orders/2/
    path("<int:pk>/pay/", pay_order, name="pay-order"),   # POST /api/orders/2/pay/
    path("checkout/",checkout,name="checkout")
]
