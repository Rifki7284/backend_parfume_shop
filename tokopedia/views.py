# views.py
import time, hmac, hashlib, requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.conf import settings


def tiktok_authorize(request):
    """
    Redirect user ke halaman OAuth TikTok.
    """
    app_key = settings.TIKTOK_APP_KEY
    redirect_uri = settings.TIKTOK_REDIRECT_URI
    state = "xyz123"  # random string (untuk validasi CSRF)

    url = (
        f"https://auth.tiktokglobalshop.com/oauth/authorize"
        f"?app_key={app_key}&redirect_uri={redirect_uri}&state={state}"
    )
    return redirect(url)


def TikTokCallbackView(request):
    """
    Callback setelah authorize, tukar code → access_token.
    """
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code:
        return HttpResponse("No code received", status=400)

    url = "https://auth.tiktokglobalshop.com/api/v2/token/get"
    data = {
        "app_key": settings.TIKTOK_APP_KEY,
        "app_secret": settings.TIKTOK_APP_SECRET,
        "auth_code": code,
        "grant_type": "authorized_code",
    }

    resp = requests.post(url, json=data)
    token_data = resp.json()

    # TODO: simpan access_token & refresh_token ke DB
    return JsonResponse(token_data)


def generate_sign(app_key, app_secret, api_path, params: dict):
    """
    Buat sign & timestamp untuk API TikTok v202309
    """
    timestamp = str(int(time.time()))
    params_with = {**params, "app_key": app_key, "timestamp": timestamp}

    sorted_str = "".join(f"{k}{v}" for k, v in sorted(params_with.items()))
    raw = f"{app_key}{api_path}{sorted_str}{timestamp}"

    sign = hmac.new(app_secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return sign, timestamp


def get_product(request, product_id):
    """
    Contoh: Get Product API pakai access_token.
    """
    access_token = "ISI_DARI_DB"  # ganti setelah authorize

    api_path = f"/product/202309/products/{product_id}"
    url = f"https://open-api.tiktokglobalshop.com{api_path}"

    app_key = settings.TIKTOK_APP_KEY
    app_secret = settings.TIKTOK_APP_SECRET

    sign, ts = generate_sign(app_key, app_secret, api_path, {})

    params = {"app_key": app_key, "timestamp": ts, "sign": sign}
    headers = {"x-tts-access-token": access_token, "Content-Type": "application/json"}

    resp = requests.get(url, headers=headers, params=params)
    return JsonResponse(resp.json())
