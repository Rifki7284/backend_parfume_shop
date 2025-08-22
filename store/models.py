from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from itertools import product as iter_product
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1️⃣ MODEL PRODUK DASAR
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.CharField(max_length=50)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 1)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return f"{self.product.name} Image"


# 2️⃣ MODEL RATING & REVIEW
class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating})"


# 3️⃣ MODEL OPSI & VARIAN PRODUK
class ProductOptionType(models.Model):
    # contoh: Warna, Ukuran, Brand
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    # contoh: Sepatu -> Warna=Merah, Ukuran=42
    product = models.ForeignKey(Product, related_name='options', on_delete=models.CASCADE)
    option_type = models.ForeignKey(ProductOptionType, related_name='options', on_delete=models.CASCADE)
    value = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.product.name} - {self.option_type.name}: {self.value}"


class ProductVariant(models.Model):
    # Kombinasi dari beberapa opsi membentuk varian unik
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    options = models.ManyToManyField(ProductOption, related_name='variants')
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # bisa override harga
    def __str__(self):
        opts = ", ".join([o.value for o in self.options.all()]) if self.pk else "Belum ada opsi"
        return f"Varian {self.product.name} ({opts})"

@receiver(post_save, sender=ProductOption)
def create_variants_for_product(sender, instance, **kwargs):
    """
    Signal ini akan otomatis membuat ProductVariant dari semua kombinasi opsi.
    Dipanggil setiap kali ProductOption baru dibuat.
    """
    product_obj = instance.product

    # Ambil semua opsi yang ada untuk product ini, kelompokkan per option_type
    option_groups = {}
    for opt in product_obj.options.all():
        option_groups.setdefault(opt.option_type_id, []).append(opt)

    # Kalau cuma 1 jenis opsi (misalnya hanya warna tanpa ukuran), 
    # jangan buat kombinasi, langsung bikin varian per opsi
    if len(option_groups) == 1:
        for opts in option_groups.values():
            for single_opt in opts:
                variant, created = ProductVariant.objects.get_or_create(product=product_obj)
                variant.options.set([single_opt])
    else:
        # Buat semua kombinasi opsi
        all_combinations = list(iter_product(*option_groups.values()))

        for combo in all_combinations:
            variant, created = ProductVariant.objects.get_or_create(product=product_obj)
            variant.save()
            variant.options.set(combo)