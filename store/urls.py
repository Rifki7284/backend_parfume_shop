from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductDetailBySlugView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename="products")

urlpatterns = [
    path('', include(router.urls)),
    path('products/<slug:slug>/', ProductDetailBySlugView.as_view(), name="product-detail-slug"),
]
