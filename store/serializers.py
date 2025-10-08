from rest_framework import serializers
from .models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            return request.build_absolute_uri(obj.image.url)
        return None


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "description",
            "price",
            "quantity",
            "fragrance_notes_top",
            "fragrance_notes_middle",
            "fragrance_notes_base",
            "gender",
            "volume_ml",
            "tokopedia_link",
            "shopee_link",
            "tiktok_link",
            "slug",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "slug"
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        images_data = self.initial_data.get("images")
        product = Product.objects.create(**validated_data)

        if images_data:
            for image_dict in images_data:
                ProductImage.objects.create(product=product, **image_dict)
        return product

    def update(self, instance, validated_data):
        images_data = self.initial_data.get("images", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Jika ingin update gambar juga
        if images_data is not None:
            instance.images.all().delete()
            for image_dict in images_data:
                ProductImage.objects.create(product=instance, **image_dict)

        return instance
