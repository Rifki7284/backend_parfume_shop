# views.py
import time, hmac, hashlib, requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.conf import settings
import hmac
import hashlib
from urllib.parse import urlparse
import json
import requests
import time
from django.views.decorators.csrf import csrf_exempt
TIKTOK_APP_KEY = "6h7mvifltn5ft"
TIKTOK_APP_SECRET = "fc8a575471cba9137ff9b1031a17b8ddf8bf6f03"
ACCESS_TOKEN = "ROW_YOM-RgAAAAAtBjpXonNymt3IiN_W-ebc6-djOYM0peX5Q2LW70-2fN1KzontN-qO7ookKra1UF5hdw60KiRmcakNfBnCiVFn17gqMFLBfE2QkPdyC5TV8D4xECynlHGcDDpSCiL5VnU"

BASE_URL = "https://open-api.tiktokglobalshop.com"


def generate_sign(request_option, app_secret):
    """
    Generate HMAC-SHA256 signature
    :param request_option: Request options dictionary containing qs (query params), uri (path), headers, body etc.
    :param app_secret: Secret key for signing
    :return: Hexadecimal signature string
    """
    # Step 1: Extract and filter query parameters, exclude "access_token" and "sign", sort alphabetically
    params = request_option.get("qs", {})
    exclude_keys = ["access_token", "sign"]
    sorted_params = [
        {"key": key, "value": params[key]}
        for key in sorted(params.keys())
        if key not in exclude_keys
    ]

    # Step 2: Concatenate parameters in {key}{value} format
    param_string = "".join([f"{item['key']}{item['value']}" for item in sorted_params])
    sign_string = param_string

    # Step 3: Append API request path to the signature string
    uri = request_option.get("uri", "")
    pathname = urlparse(uri).path if uri else ""
    sign_string = f"{pathname}{param_string}"

    # Step 4: If not multipart/form-data and request body exists, append JSON-serialized body
    content_type = request_option.get("headers", {}).get("content-type", "")
    body = request_option.get("body", {})
    if content_type != "multipart/form-data" and body:
        body_str = json.dumps(body)  # JSON serialization ensures consistency
        sign_string += body_str

    # Step 5: Wrap signature string with app_secret
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"

    # Step 6: Encode using HMAC-SHA256 and generate hexadecimal signature
    hmac_obj = hmac.new(
        app_secret.encode("utf-8"), wrapped_string.encode("utf-8"), hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    return sign


from django.http import JsonResponse
import time
import requests


def get_auth_shop(request):
    path = "/authorization/202309/shops"
    timestamp = int(time.time())
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,  # taruh di query param, bukan header
    }

    request_option = {
        "qs": params,
        "uri": path,
        "headers": {
            "content-type": "application/json",
            "x-tts-access-token": "ROW_QZzzyAAAAAAtBjpXonNymt3IiN_W-ebcRtBpjzpRzqTXHua4zIiuv04EDe6C-tUTpCWlIt2Y2Uwn2IBsodBcXTu_HOg8Qask_hv-nPCF9zE4AZI29Pc5qw",
        },
        "body": {},
    }

    sign = generate_sign(request_option, TIKTOK_APP_SECRET)
    params["sign"] = sign

    url = f"{BASE_URL}{path}"
    response = requests.get(
        url,
        params=params,
        headers={
            "Content-Type": "application/json",
            "x-tts-access-token": "ROW_QZzzyAAAAAAtBjpXonNymt3IiN_W-ebcRtBpjzpRzqTXHua4zIiuv04EDe6C-tUTpCWlIt2Y2Uwn2IBsodBcXTu_HOg8Qask_hv-nPCF9zE4AZI29Pc5qw",
        },
    )
    print("Headers:", response.request.headers)
    return JsonResponse(response.json())

@csrf_exempt
def get_orders_list(request):
    path = "/order/202309/orders/search"
    timestamp = int(time.time())
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "page_size":"1",
        "shop_cipher":"ROW_zd-y1QAAAAC6SwPm247gu7HfNeEcnZSe"
    }

    request_option = {
        "qs": params,
        "uri": path,
        "headers": {
            "content-type": "application/json",
            "x-tts-access-token": "ROW_YOM-RgAAAAAtBjpXonNymt3IiN_W-ebc6-djOYM0peX5Q2LW70-2fN1KzontN-qO7ookKra1UF5hdw60KiRmcakNfBnCiVFn17gqMFLBfE2QkPdyC5TV8D4xECynlHGcDDpSCiL5VnU",
        },
        "body": {},
    }

    sign = generate_sign(request_option, TIKTOK_APP_SECRET)
    params["sign"] = sign

    url = f"{BASE_URL}{path}"
    response = requests.post(
        url,
        params=params,
        headers={
            "Content-Type": "application/json",
            "x-tts-access-token": "ROW_YOM-RgAAAAAtBjpXonNymt3IiN_W-ebc6-djOYM0peX5Q2LW70-2fN1KzontN-qO7ookKra1UF5hdw60KiRmcakNfBnCiVFn17gqMFLBfE2QkPdyC5TV8D4xECynlHGcDDpSCiL5VnU",
        },
    )
    print("Headers:", response.request.headers)
    return JsonResponse(response.json())

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
    code = request.GET.get("code")
    state = request.GET.get("state")
    return JsonResponse({"code": code, "state": state})
