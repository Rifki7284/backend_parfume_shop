from django.apps import AppConfig


class TiktokConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tiktok'
    def ready(self):
        # Daftarkan schedule sekali (hindari duplikasi saat reload)
        from django_q.models import Schedule
        if not Schedule.objects.filter(name="Refresh TikTok Access Token Otomatis").exists():
            Schedule.objects.create(
                name="Refresh TikTok Access Token Otomatis",
                func="tiktok.tasks.refresh_token_if_needed",
                schedule_type=Schedule.MINUTES,  # tiap N menit
                minutes=15,
            )
