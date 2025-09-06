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
from django.http import JsonResponse
import time
import requests
from tiktok.utils.tiktok_token import get_valid_access_token
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

TIKTOK_APP_KEY = str(settings.TIKTOK_APP_KEY).strip()
TIKTOK_APP_SECRET = str(settings.TIKTOK_APP_SECRET).strip()

BASE_URL = "https://open-api.tiktokglobalshop.com"
# tiktok/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TrackQuerySerializer
from .binderbyte import BinderbyteClient, BinderbyteError
from .courier_map import to_binderbyte_code

class TrackBinderbyteView(APIView):
    authentication_classes = []  
    permission_classes = []      

    def get(self, request):
        serializer = TrackQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        courier = to_binderbyte_code(serializer.validated_data["courier"])
        awb = serializer.validated_data["awb"]

        client = BinderbyteClient()
        try:
            data = client.track(courier, awb)
            return Response(data, status=status.HTTP_200_OK)
        except BinderbyteError as e:
            return Response({"status": 400, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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



def get_auth_shop(request):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/authorization/202309/shops"
    timestamp = int(time.time())
    params = {
        "app_key": TIKTOK_APP_KEY.strip(),
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,  # taruh di query param, bukan header
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        },
    )

    return JsonResponse(response.json())

@csrf_exempt
def get_orders_list(request,cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/order/202309/orders/search"
    timestamp = int(time.time())
    page_token = request.GET.get("page_token", "")
    page_size = request.GET.get("page_size", "3")  # default 10
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "page_size":page_size,
        "page_token":page_token,
        "shop_cipher":cipher
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())

@csrf_exempt
def get_product(request,cipher,id):
    ACCESS_TOKEN = get_valid_access_token()
    path = f'/product/202309/products/{id}'
    timestamp = int(time.time())
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "shop_cipher":cipher
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())

@csrf_exempt
def get_orders_return(request,cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/return_refund/202309/returns/search"
    timestamp = int(time.time())
    page_token = request.GET.get("page_token", "")
    page_size = request.GET.get("page_size", "3")  # default 10
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "page_size":page_size,
        "page_token":page_token,
        "shop_cipher":cipher
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())

@csrf_exempt
def get_shop_performance(request,cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop/performance"
    timestamp = int(time.time())
    
    # format date="YYYY-MM-DD"
    start_date = request.GET.get("start_date_ge", "")
    end_date=request.GET.get("end_date_lt","")
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "start_date_ge":start_date,
        "end_date_lt":end_date,
        "shop_cipher":cipher
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())

@csrf_exempt
def get_shop_product_performance(request,cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop_products/performance"
    timestamp = int(time.time())
    
    # format date="YYYY-MM-DD"
    start_date = request.GET.get("start_date_ge", "")
    end_date=request.GET.get("end_date_lt","")
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "start_date_ge":start_date,
        "end_date_lt":end_date,
        "shop_cipher":cipher
    }

    request_option = {
        "qs": params,
        "uri": path,
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
            "x-tts-access-token":ACCESS_TOKEN,
        }
    )
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
