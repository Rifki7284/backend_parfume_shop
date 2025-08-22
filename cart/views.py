from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer
from store.models import ProductVariant

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # List semua cart items
    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    # Tambah variant ke cart
    def create(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response({"error": "variant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response({"error": "Variant not found"}, status=status.HTTP_404_NOT_FOUND)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": quantity, "price_at_add": variant.price}
        )
        if not created:
            item.quantity += quantity
            item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Hapus item cart
    def destroy(self, request, pk=None):
        try:
            item = CartItem.objects.get(id=pk, cart__user=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
