from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication

from .models import Product
from .serializers import ProductSerializer

from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import AllowAny
# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductImageSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related("images").all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request, pk=None):
        product = self.get_object()
        file = request.FILES.get("image")
        if not file:
            return Response({"error": "No image uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        img = ProductImage.objects.create(product=product, image=file)
        serializer = ProductImageSerializer(img, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # DELETE /api/products/{product_id}/images/{image_id}/
    @action(detail=True, methods=["delete"], url_path=r'images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        try:
            image = product.images.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)

        # Hapus file dari storage (opsional tapi biasanya diinginkan)
        try:
            if image.image:
                image.image.delete(save=False)
        except Exception:
            # jangan crash kalau ada masalah dengan storage delete
            pass

        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        # class ProductListAPIView(generics.ListAPIView):
#     authentication_classes = [SessionAuthentication]  # pakai session
#     permission_classes = [IsAuthenticated]
#     queryset = Product.objects.all().prefetch_related("images")
#     serializer_class = ProductSerializer


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
