from django.urls import path
from .views import midtrans_notification

urlpatterns = [
    path("notification/", midtrans_notification, name="midtrans-notification"),
]
