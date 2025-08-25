from django.contrib import admin
from .models import TikTokToken

@admin.register(TikTokToken)
class TikTokTokenAdmin(admin.ModelAdmin):
    list_display = ("access_token_expire_at", "refresh_token_expire_at", "updated_at")
    readonly_fields = ("updated_at",)