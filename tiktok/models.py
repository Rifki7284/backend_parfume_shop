from django.db import models
from django.utils import timezone

class TikTokToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    access_token_expire_at = models.DateTimeField()
    refresh_token_expire_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def is_access_token_expired(self):
        return timezone.now() >= self.access_token_expire_at

    def is_refresh_token_expired(self):
        return timezone.now() >= self.refresh_token_expire_at

    def __str__(self):
        return f"TikTokToken (expired at {self.access_token_expire_at})"
