from django.urls import path
from .views import ProductListAPIView, ProductDetailAPIView, ProductDetailBySlugView

urlpatterns = [
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
    path(
        "product/<slug:slug>/",
        ProductDetailBySlugView.as_view(),
        name="product-detail-slug",
    ),
]
