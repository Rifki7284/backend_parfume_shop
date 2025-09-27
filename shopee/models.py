from django.db import models
from django.utils import timezone


class ShopeeToken(models.Model):
    partner_id = models.BigIntegerField()
    shop_id = models.BigIntegerField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    access_token_expire_at = models.DateTimeField()
    # Shopee tidak kasih refresh_token_expire_in, jadi kita simpan manual default 30 hari
    refresh_token_expire_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def is_access_token_expired(self):
        return timezone.now() >= self.access_token_expire_at

    def is_refresh_token_expired(self):
        return timezone.now() >= self.refresh_token_expire_at

    def __str__(self):
        return f"ShopeeToken shop_id={self.shop_id} (expired at {self.access_token_expire_at})"
