from shopee.models import ShopeeToken
from shopee.services.shopee_auth import refresh_access_token

def get_valid_access_token():
    token = ShopeeToken.objects.last()
    if not token:
        raise Exception("No Shopee token found in database")

    if token.is_access_token_expired():
        token = refresh_access_token()  # refresh harus return ShopeeToken object
    return token
