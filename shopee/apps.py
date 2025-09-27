# shopee/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ShopeeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shopee"

    def ready(self):
        from django.dispatch import receiver

        @receiver(post_migrate)
        def create_refresh_schedule(sender, **kwargs):
            # pastikan hanya jalan untuk app shopee
            if kwargs.get("app_config") and kwargs["app_config"].name == self.name:
                try:
                    from django_q.models import Schedule

                    if not Schedule.objects.filter(
                        name="Refresh Shopee Access Token Otomatis"
                    ).exists():
                        Schedule.objects.create(
                            name="Refresh Shopee Access Token Otomatis",
                            func="shopee.tasks.refresh_token_if_needed",  # path ke fungsi task
                            schedule_type=Schedule.MINUTES,
                            minutes=1,  # setiap 15 menit
                            repeats=-1,  # biar jalan terus
                        )
                except Exception:
                    # biar ga error kalau tabel django_q_schedule belum ada saat migrate
                    pass
