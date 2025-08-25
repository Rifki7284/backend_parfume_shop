from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # jumlah form kosong tambahan
    max_num = 10  # optional, batasi max gambar


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'category')
    list_display_links = ('id', 'name')  # nama jadi link ke halaman edit
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image')
    list_filter = ('product',)
    search_fields = ('product__name',)
