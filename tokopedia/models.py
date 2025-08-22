from django.db import models

class TikTokAuth(models.Model):
    shop_id = models.CharField(max_length=100, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

class TikTokOrder(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    buyer = models.CharField(max_length=200, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField()
