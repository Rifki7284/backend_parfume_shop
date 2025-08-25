from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication

from .models import Product
from .serializers import ProductSerializer


# API untuk menampilkan semua produk
class ProductListAPIView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]  # pakai session
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.all().prefetch_related("images")
    serializer_class = ProductSerializer


# API untuk detail produk by ID (pk)
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all().prefetch_related("images")
    serializer_class = ProductSerializer


# API untuk detail produk by slug
class ProductDetailBySlugView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.prefetch_related("images")
    serializer_class = ProductSerializer
    lookup_field = "slug"


# API hanya untuk list slug produk
class ProductSlugListAPIView(APIView):
    def get(self, request):
        slugs = Product.objects.values_list("slug", flat=True)
        return Response([{"slug": s} for s in slugs])
