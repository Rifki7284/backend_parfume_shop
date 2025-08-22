from django.contrib import admin
from .models import (
    Product,
    ProductImage,
    ProductReview,
    ProductOptionType,
    ProductOption,
    ProductVariant,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # jumlah form kosong tambahan
    max_num = 10  # optional, batasi max gambar


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    autocomplete_fields = ['option_type']  # jika banyak option_type


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    filter_horizontal = ("options",)  # pilih multiple options dengan UI


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')  # jika admin tidak boleh edit review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'get_average_rating')
    list_display_links = ('id', 'name')  # Pastikan nama jadi link ke halaman edit
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [
        ProductImageInline,
        ProductOptionInline,
        ProductVariantInline,
        ProductReviewInline,
    ]

    def get_average_rating(self, obj):
        return obj.average_rating
    get_average_rating.short_description = 'Average Rating'



@admin.register(ProductOptionType)
class ProductOptionTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'price', 'stock', 'display_options')
    list_filter = ('product',)
    search_fields = ('product__name',)

    def display_options(self, obj):
        return ", ".join([f"{o.option_type.name}: {o.value}" for o in obj.options.all()])
    display_options.short_description = "Options"
