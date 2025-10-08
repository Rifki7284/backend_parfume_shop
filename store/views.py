from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductImageSerializer
from users.permissions import IsStaffUser
from .pagination import ProductCursorPagination
from django.db.models import Q
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related("images").all()
    serializer_class = ProductSerializer
    lookup_field = "pk"
    pagination_class = ProductCursorPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # Bisa cari nama/deskripsi
    search_fields = ["name", "description"]
    # Bisa sort berdasarkan harga/nama
    ordering_fields = ["price", "name"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Ambil parameter dari URL
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        gender = self.request.query_params.get(
            "gender")  # Tambahan filter gender

        # Filter harga minimal
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        # Filter harga maksimal
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        # Filter berdasarkan gender (male, female, unisex)
        if gender and gender.lower() in ["male", "female", "unisex"]:
            queryset = queryset.filter(gender=gender.lower())

        return queryset

    def get_permissions(self):
        if self.action in ["list", "retrieve", "get_by_slug", "exclude_slug","search_products"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsStaffUser()]

    @action(detail=False, methods=["get"], url_path=r"exclude-slug/(?P<slug>[^/.]+)")
    def exclude_slug(self, request, slug=None):
        """
        Ambil semua produk kecuali yang slug-nya sama dengan parameter.
        Bisa diakses oleh semua pengguna (tanpa login).
        """
        queryset = Product.objects.prefetch_related(
            "images").exclude(slug=slug)

        # Pagination tetap jalan
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"], url_path="search")
    def search_products(self, request):
        """
        Fitur pencarian produk berdasarkan nama, deskripsi, atau brand (tanpa pagination).
        Contoh: /api/products/search/?q=chanel
        """
        query = request.query_params.get("q", "").strip()
        queryset = Product.objects.prefetch_related("images")

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(brand__icontains=query)
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path=r"by-slug/(?P<slug>[^/.]+)")
    def get_by_slug(self, request, slug=None):
        try:
            product = Product.objects.prefetch_related("images").get(slug=slug)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request, pk=None):
        product = self.get_object()
        file = request.FILES.get("image")
        if not file:
            return Response({"error": "No image uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        img = ProductImage.objects.create(product=product, image=file)
        serializer = ProductImageSerializer(img, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        try:
            image = product.images.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)

        if image.image:
            image.image.delete(save=False)
        image.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
