from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    GENDER_CHOICES = [
        ('male', 'Pria'),
        ('female', 'Wanita'),
        ('unisex', 'Unisex'),
    ]

    name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)

    fragrance_notes_top = models.CharField(max_length=200, blank=True, default="")
    fragrance_notes_middle = models.CharField(max_length=200, blank=True, default="")
    fragrance_notes_base = models.CharField(max_length=200, blank=True, default="")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    volume_ml = models.PositiveIntegerField(default=50)

    tokopedia_link = models.URLField(blank=True, null=True)
    shopee_link = models.URLField(blank=True, null=True)
    tiktok_link = models.URLField(blank=True, null=True)

    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.brand})" if self.brand else self.name

    def get_purchase_link(self):
        """Ambil link prioritas (Tokopedia → Shopee → TikTok)"""
        return self.tokopedia_link or self.shopee_link or self.tiktok_link


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Gambar {self.product.name}"
