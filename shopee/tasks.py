# tiktok/tasks.py
import logging
from django.utils import timezone
from datetime import timedelta
from shopee.models import ShopeeToken
from shopee.services.shopee_auth import refresh_access_token, ShopeeAuthError

logger = logging.getLogger(__name__)

def refresh_token_if_needed():
    token = ShopeeToken.objects.order_by("-id").first()
    if not token:
        logger.warning("Tidak ada ShopeeToken di DB; lewati refresh.")
        return

    # jika sisa < 10 menit, refresh
    if token.access_token_expire_at - timezone.now() <= timedelta(minutes=10):
        try:
            refresh_access_token()
            logger.info("Auto-refresh Shopee access_token berhasil.")
        except ShopeeAuthError as e:
            logger.error("Auto-refresh gagal: %s", e)
