# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from store.models import ProductVariant, ProductOption
from store.serializers import ProductSerializer


# Opsi variant
class ProductVariantOptionSerializer(serializers.ModelSerializer):
    option_type = serializers.CharField(source="option_type.name")

    class Meta:
        model = ProductOption
        fields = ["id", "option_type", "value"]


# Variant untuk order
class ProductVariantForOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    options = ProductVariantOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "product_name", "price", "options"]


# Item order
class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantForOrderSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "variant", "quantity", "subtotal"]


# Order utama
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "total_price", "status", "items", "created_at"]
        read_only_fields = ["user", "status", "created_at"]
