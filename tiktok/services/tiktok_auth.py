# tiktok/services/tiktok_auth.py
import logging
from datetime import timedelta
from typing import Tuple
import time

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from tiktok.models import TikTokToken

logger = logging.getLogger(__name__)

TIKTOK_REFRESH_URL = "https://auth.tiktok-shops.com/api/v2/token/refresh"

class TikTokAuthError(Exception):
    pass


def _assert_config():
    if not settings.TIKTOK_APP_KEY or not settings.TIKTOK_APP_SECRET:
        raise TikTokAuthError("TIKTOK_APP_KEY/TIKTOK_APP_SECRET belum di-set di settings/env.")


def _parse_expire(value):
    """
    TikTok kadang mengirim expire_in sebagai:
    - durasi (detik), contoh: 604800
    - timestamp absolute (epoch), contoh: 1693123456
    """
    try:
        v = int(value)
    except Exception:
        raise TikTokAuthError(f"Format expire_in tidak valid: {value!r}")

    now_ts = int(time.time())

    # kalau nilainya > sekarang + 1 hari → anggap epoch timestamp
    if v > now_ts + 86400:
        return timezone.datetime.fromtimestamp(v, tz=timezone.utc)
    else:
        return timezone.now() + timedelta(seconds=v)


@transaction.atomic
def refresh_access_token() -> Tuple[str, TikTokToken]:
    """
    Refresh access_token menggunakan refresh_token tersimpan.
    Transaksi atomic + SELECT ... FOR UPDATE untuk menghindari refresh ganda.
    """
    _assert_config()

    token = TikTokToken.objects.select_for_update().order_by("-id").first()
    if not token:
        raise TikTokAuthError("Token TikTok belum ada di database. Lakukan OAuth terlebih dahulu.")

    if token.is_refresh_token_expired():
        raise TikTokAuthError("Refresh token sudah kadaluarsa. Harus re-authorize aplikasi TikTok Shop.")

    params = {
        "app_key": settings.TIKTOK_APP_KEY,
        "app_secret": settings.TIKTOK_APP_SECRET,
        "refresh_token": token.refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        resp = requests.get(TIKTOK_REFRESH_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.exception("Gagal request refresh token ke TikTok")
        raise TikTokAuthError(f"Gagal menghubungi TikTok: {e}") from e
    except ValueError as e:
        raise TikTokAuthError("Respons TikTok bukan JSON valid") from e

    if data.get("code") != 0:
        raise TikTokAuthError(f"Gagal refresh token: {data}")

    d = data.get("data") or {}
    new_access = d.get("access_token")
    new_refresh = d.get("refresh_token")
    a_exp_at = _parse_expire(d.get("access_token_expire_in"))
    r_exp_at = _parse_expire(d.get("refresh_token_expire_in"))

    if not new_access or not new_refresh or not a_exp_at or not r_exp_at:
        raise TikTokAuthError(f"Data refresh tidak lengkap: {d}")

    token.access_token = new_access
    token.refresh_token = new_refresh
    token.access_token_expire_at = a_exp_at
    token.refresh_token_expire_at = r_exp_at
    token.save(update_fields=[
        "access_token", "refresh_token",
        "access_token_expire_at", "refresh_token_expire_at", "updated_at"
    ])

    logger.info("Berhasil refresh TikTok access_token. Expire pada %s", token.access_token_expire_at)
    return token.access_token, token


@transaction.atomic
def get_access_token(skew_seconds: int = 300) -> str:
    """
    Ambil access_token yang masih valid.
    Jika sudah/hampir kadaluarsa (dalam skew_seconds), lakukan refresh.
    """
    _assert_config()

    token = TikTokToken.objects.select_for_update().order_by("-id").first()
    if not token:
        raise TikTokAuthError("Token TikTok belum ada. Selesaikan proses OAuth terlebih dahulu.")

    if token.is_access_token_expired(skew_seconds=skew_seconds):
        access, _ = refresh_access_token()
        return access

    return token.access_token
