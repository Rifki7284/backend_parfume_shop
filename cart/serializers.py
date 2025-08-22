from rest_framework import serializers
from .models import Cart, CartItem
from store.models import ProductVariant, Product, ProductImage, ProductReview, ProductOption

# Product serializer khusus untuk Cart (tanpa options/variants)
class ProductForCartSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'slug', 'average_rating', 'images', 'reviews']

    def get_images(self, obj):
        return [{'id': img.id, 'image': img.image.url} for img in obj.images.all()]

    def get_reviews(self, obj):
        return [{'id': rev.id, 'user': rev.user.username, 'rating': rev.rating, 'comment': rev.comment, 'created_at': rev.created_at} for rev in obj.reviews.all()]


# Serializer untuk opsi variant yang dibeli
class ProductVariantOptionSerializer(serializers.ModelSerializer):
    option_type = serializers.CharField(source='option_type.name')
    class Meta:
        model = ProductOption
        fields = ['id', 'option_type', 'value']


# Variant serializer untuk Cart (hanya opsi yang dipilih + product)
class ProductVariantForCartSerializer(serializers.ModelSerializer):
    product = ProductForCartSerializer(read_only=True)
    options = ProductVariantOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'price', 'stock', 'options', 'product']


# CartItem serializer
class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantForCartSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'quantity', 'price_at_add', 'subtotal']


# Cart serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']
