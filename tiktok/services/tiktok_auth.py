import requests
from django.utils import timezone
from tiktok.models import TikTokToken

APP_KEY = "your_app_key"
APP_SECRET = "your_app_secret"

def refresh_access_token():
    token = TikTokToken.objects.last()
    if not token:
        raise Exception("No TikTok token found in database")

    url = "https://auth.tiktok-shops.com/api/v2/token/refresh"
    params = {
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "refresh_token": token.refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.get(url, params=params).json()
    if response.get("code") == 0:
        data = response["data"]

        token.access_token = data["access_token"]
        token.refresh_token = data["refresh_token"]

        token.access_token_expire_at = timezone.datetime.fromtimestamp(
            data["access_token_expire_in"], tz=timezone.utc
        )
        token.refresh_token_expire_at = timezone.datetime.fromtimestamp(
            data["refresh_token_expire_in"], tz=timezone.utc
        )
        token.save()
        return token.access_token
    else:
        raise Exception(f"Failed to refresh token: {response}")
