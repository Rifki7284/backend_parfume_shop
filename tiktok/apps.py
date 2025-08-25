# tiktok/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TiktokConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tiktok'

    def ready(self):
        from django_q.models import Schedule
        from django.dispatch import receiver

        @receiver(post_migrate)
        def create_refresh_schedule(sender, **kwargs):
            if sender.name == self.name:  # hanya untuk app ini
                if not Schedule.objects.filter(name="Refresh TikTok Access Token Otomatis").exists():
                    Schedule.objects.create(
                        name="Refresh TikTok Access Token Otomatis",
                        func="tiktok.tasks.refresh_token_if_needed",
                        schedule_type=Schedule.MINUTES,
                        minutes=15,
                    )
