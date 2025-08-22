from django.db import models
from django.contrib.auth.models import User
from store.models import ProductVariant

class Cart(models.Model):
    user = models.ForeignKey(User, related_name='cart', on_delete=models.CASCADE)

    @property
    def total_price(self):
        return sum([item.subtotal for item in self.items.all()])

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.price_at_add * self.quantity
