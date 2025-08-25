# tiktok/tasks.py
import logging
from django.utils import timezone
from datetime import timedelta
from tiktok.models import TikTokToken
from tiktok.services.tiktok_auth import refresh_access_token, TikTokAuthError

logger = logging.getLogger(__name__)

def refresh_token_if_needed():
    token = TikTokToken.objects.order_by("-id").first()
    if not token:
        logger.warning("Tidak ada TikTokToken di DB; lewati refresh.")
        return

    # jika sisa < 10 menit, refresh
    if token.access_token_expire_at - timezone.now() <= timedelta(minutes=10):
        try:
            refresh_access_token()
            logger.info("Auto-refresh TikTok access_token berhasil.")
        except TikTokAuthError as e:
            logger.error("Auto-refresh gagal: %s", e)
