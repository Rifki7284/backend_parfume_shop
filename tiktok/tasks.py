from django.utils import timezone
from .models import TikTokToken
from .services.tiktok_auth import refresh_access_token

def scheduled_refresh():
    """
    Cron job untuk cek apakah access token sudah expired
    lalu refresh otomatis.
    """
    token = TikTokToken.objects.last()
    if not token:
        print("⚠️ Tidak ada TikTok token di database.")
        return

    # Kalau sudah expired atau tinggal < 5 menit lagi → refresh
    if timezone.now() >= token.access_token_expire_at or \
       (token.access_token_expire_at - timezone.now()).total_seconds() < 300:
        try:
            refresh_access_token()
            print("✅ TikTok token berhasil diperbarui otomatis")
        except Exception as e:
            print(f"❌ Gagal refresh token: {e}")
    else:
        print("ℹ️ Access token masih valid, tidak perlu refresh.")
