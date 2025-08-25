import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_q.models import Schedule

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def create_refresh_schedule(sender, **kwargs):
    """
    Signal ini dipanggil setelah migrate selesai.
    Tujuannya: memastikan jadwal auto-refresh token TikTok selalu ada.
    """
    try:
        schedule_name = "Refresh TikTok Access Token Otomatis"

        # Cek apakah schedule sudah ada
        if not Schedule.objects.filter(name=schedule_name).exists():
            Schedule.objects.create(
                name=schedule_name,
                func="tiktok.tasks.refresh_token_if_needed",  # path ke fungsi task kamu
                schedule_type=Schedule.MINUTES,
                minutes=1,      # dijalankan tiap 1 menit (bisa kamu ubah ke 5 menit)
                repeats=-1      # -1 = jalan terus tanpa batas
            )
            logger.info("Schedule '%s' berhasil dibuat.", schedule_name)
        else:
            logger.info("Schedule '%s' sudah ada, lewati.", schedule_name)

    except Exception as e:
        logger.error("Gagal membuat schedule refresh token: %s", e)
