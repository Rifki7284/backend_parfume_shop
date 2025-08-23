from tiktok.models import TikTokToken
from tiktok.services.tiktok_auth import refresh_access_token

def get_valid_access_token():
    token = TikTokToken.objects.last()
    if not token:
        raise Exception("No TikTok token found in database")

    if token.is_access_token_expired():
        return refresh_access_token()
    return token.access_token
