from django.core.management.base import BaseCommand
from tiktok.tasks import scheduled_refresh

class Command(BaseCommand):
    help = "Refresh TikTok token jika sudah expired"

    def handle(self, *args, **kwargs):
        scheduled_refresh()
