from django.utils import timezone
from rest_framework import serializers
from .models import (
    Product, ProductImage, ProductReview,
    ProductOptionType, ProductOption, ProductVariant,
)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class ProductOptionSerializer(serializers.ModelSerializer):
    option_type = serializers.CharField(source='option_type.name')
    class Meta:
        model = ProductOption
        fields = ['id', 'option_type', 'value']


class ProductVariantSerializer(serializers.ModelSerializer):
    options = ProductOptionSerializer(many=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'product_name', 'options', 'stock', 'price']



class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            'category', 'slug', 'average_rating',
            'images', 'options', 'variants', 'reviews'
        ]