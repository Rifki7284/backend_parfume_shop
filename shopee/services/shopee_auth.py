# shopee/services/shopee_auth.py
import logging
import time
import hmac
import hashlib
import requests
from typing import Tuple
from datetime import timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from shopee.models import ShopeeToken

logger = logging.getLogger(__name__)

SHOPEE_HOST = "https://openplatform.sandbox.test-stable.shopee.sg"
PARTNER_ID = str(settings.PARTNER_ID).strip()
PARTNER_KEY = str(settings.PARTNER_KEY).strip()


class ShopeeAuthError(Exception):
    pass


def _assert_config():
    if not PARTNER_ID or not PARTNER_KEY:
        raise ShopeeAuthError("PARTNER_ID/PARTNER_KEY belum di-set di settings/env.")


def _parse_expire(value, default_seconds=14400):
    """
    Shopee biasanya kirim expire_in dalam detik.
    Kalau nggak ada → fallback ke default 4 jam.
    """
    try:
        v = int(value)
    except Exception:
        v = default_seconds
    return timezone.now() + timedelta(seconds=v)


@transaction.atomic
def refresh_access_token():
    """
    Refresh Shopee access_token menggunakan refresh_token dari database.
    """
    token = ShopeeToken.objects.order_by("-id").first()
    if not token:
        raise Exception("Token Shopee belum ada di database. Lakukan OAuth terlebih dahulu.")

    if token.is_refresh_token_expired():
        raise Exception("Refresh token sudah kadaluarsa. Harus re-authorize Shopee.")

    # Shopee API data
    partner_id = int(PARTNER_ID)
    partner_key = PARTNER_KEY
    shop_id = int(token.shop_id)
    refresh_token = token.refresh_token
    timest = int(time.time())
    path = "/api/v2/auth/access_token/get"
    host = SHOPEE_HOST  # contoh: "https://partner.shopeemobile.com"

    # buat sign
    base_string = f"{partner_id}{path}{timest}"
    sign = hmac.new(partner_key.encode(), base_string.encode(), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    body = {
        "partner_id": partner_id,
        "shop_id": shop_id,
        "refresh_token": refresh_token,
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.exception("Gagal request refresh token ke Shopee")
        raise Exception(f"Gagal menghubungi Shopee: {e}") from e

    if "access_token" not in data:
        raise Exception(f"Gagal refresh token: {data}")

    # update token di DB
    token.access_token = data["access_token"]
    token.refresh_token = data["refresh_token"]
    token.access_token_expire_at = timezone.now() + timedelta(seconds=data.get("expire_in", 14400))
    token.refresh_token_expire_at = timezone.now() + timedelta(days=30)  # sesuai docs
    token.save(update_fields=[
        "access_token", "refresh_token",
        "access_token_expire_at", "refresh_token_expire_at", "updated_at"
    ])

    logger.info("Berhasil refresh Shopee access_token. Expire pada %s", token.access_token_expire_at)
    return token.access_token, token


@transaction.atomic
def get_access_token(skew_seconds: int = 300) -> str:
    """
    Ambil access_token yang masih valid.
    Kalau hampir kadaluarsa (< skew_seconds), lakukan refresh.
    """
    _assert_config()

    token = ShopeeToken.objects.select_for_update().order_by("-id").first()
    if not token:
        raise ShopeeAuthError("Token Shopee belum ada. Selesaikan proses OAuth terlebih dahulu.")

    if token.is_access_token_expired(skew_seconds=skew_seconds):
        access, _ = refresh_access_token()
        return access

    return token.access_token
