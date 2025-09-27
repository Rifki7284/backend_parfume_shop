from django.urls import path
from .views import Check_token,StaffLoginView
urlpatterns = [
    # path("login/", CustomLoginView.as_view(), name="custom_login"),
    # path("me/", account_me),
    path("check/token",Check_token),
    path("login/staff",StaffLoginView.as_view())
]
