from django.urls import path
from .views import CustomLoginView,account_me
urlpatterns = [
    # path("protected/", ProtectedView.as_view(), name="protected"),
    path("login/", CustomLoginView.as_view(), name="custom_login"),
    path("me/", account_me),
]
