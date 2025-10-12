# views.py
from datetime import datetime, timedelta
from users.permissions import IsStaffUser
from rest_framework.decorators import api_view, permission_classes
from .courier_map import to_binderbyte_code
from .binderbyte import BinderbyteClient, BinderbyteError
from .serializers import TrackQuerySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import calendar
from datetime import datetime, timedelta, timezone
from collections import Counter
import time
import hmac
import hashlib
import requests
from django.http import JsonResponse
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
from collections import Counter
TIKTOK_APP_KEY = str(settings.TIKTOK_APP_KEY).strip()
TIKTOK_APP_SECRET = str(settings.TIKTOK_APP_SECRET).strip()

BASE_URL = "https://open-api.tiktokglobalshop.com"
# tiktok/views.py

@permission_classes([IsAuthenticated, IsStaffUser])
class TrackBinderbyteView(APIView):
    authentication_classes = []
    permission_classes = [IsAuthenticated, IsStaffUser]

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
    # Step 1: Extract and filter query parameters, exclude "access_token" and "sign", sort alphabetically
    params = request_option.get("qs", {})
    exclude_keys = ["access_token", "sign"]
    sorted_params = [
        {"key": key, "value": params[key]}
        for key in sorted(params.keys())
        if key not in exclude_keys
    ]

    # Step 2: Concatenate parameters in {key}{value} format
    param_string = "".join(
        [f"{item['key']}{item['value']}" for item in sorted_params])
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
        app_secret.encode(
            "utf-8"), wrapped_string.encode("utf-8"), hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    return sign


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
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
            "x-tts-access-token": ACCESS_TOKEN,
        },
    )

    return JsonResponse(response.json())


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_orders_list(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/order/202309/orders/search"
    timestamp = int(time.time())

    # === Ambil filter dari frontend ===
    status = request.GET.get("status")
    keyword = request.GET.get("keyword")

    page_token = request.GET.get("page_token", "")
    page_size = request.GET.get("page_size", "10")

    # === Base params ===
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "page_size": page_size,
        "page_token": page_token,
        "shop_cipher": cipher,
    }

    # === Tambahkan filter ===
    if status:
        params["order_status"] = status
    if keyword:
        params["keyword"] = keyword

    # === Generate sign ===
    request_option = {"qs": params, "uri": path, "body": {}}
    sign = generate_sign(request_option, TIKTOK_APP_SECRET)
    params["sign"] = sign

    # === Request ke TikTok ===
    url = f"{BASE_URL}{path}"
    response = requests.post(
        url,
        params=params,
        headers={
            "Content-Type": "application/json",
            "x-tts-access-token": ACCESS_TOKEN,
        },
    )

    return JsonResponse(response.json())

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_top_products(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/order/202309/orders/search"
    url = f"{BASE_URL}{path}"

    timestamp = int(time.time())
    page_size = 100
    page_token = ""
    month = request.GET.get("month")
    year = request.GET.get("year")

    try:
        if month and year:
            month = int(month)
            year = int(year)

            # start: first day of month 00:00:00 UTC
            start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)

            # last day of month at 23:59:59 UTC
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        else:
            # default last 30 days (UTC)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)

        create_time_ge = int(start_date.timestamp())
        create_time_lt = int(end_date.timestamp())

    except ValueError:
        return JsonResponse({"error": "Invalid month/year format"}, status=400)

    # debug: bantu verifikasi apa yang dikirim ke API
    print("DEBUG create_time_ge:", datetime.fromtimestamp(create_time_ge, tz=timezone.utc))
    print("DEBUG create_time_lt:", datetime.fromtimestamp(create_time_lt, tz=timezone.utc))

    all_orders = []

    while True:
        # Param sistem (query string)
        params = {
            "app_key": TIKTOK_APP_KEY,
            "timestamp": timestamp,
            "page_size": page_size,
            "page_token": page_token,
            "shop_cipher": cipher,
        }

        # Body JSON (filter + kondisi pencarian) -> kirim kedua batas waktu
        payload = {
            "order_status": "COMPLETED",
            "create_time_ge": create_time_ge,
            "create_time_lt": create_time_lt,
        }

        # Generate sign berdasarkan query + body (pastikan generate_sign mengikutkan body)
        request_option = {
            "qs": params,
            "uri": path,
            "body": payload,
        }
        sign = generate_sign(request_option, TIKTOK_APP_SECRET)
        params["sign"] = sign

        # Kirim POST request (body lewat json= so types preserved)
        response = requests.post(
            url,
            params=params,
            headers={
                "Content-Type": "application/json",
                "x-tts-access-token": ACCESS_TOKEN,
            },
            json=payload,
        )

        try:
            data = response.json()
        except ValueError:
            return JsonResponse({"error": "Invalid JSON response from TikTok", "raw": response.text}, status=500)

        if data.get("code") != 0:
            return JsonResponse(data, status=400)

        orders = data.get("data", {}).get("orders", [])
        all_orders.extend(orders)

        next_page_token = data.get("data", {}).get("next_page_token", "")
        if not next_page_token:
            break

        page_token = next_page_token

    # === Hitung produk terlaris ===
    product_counter = Counter()

    for order in all_orders:
        for item in order.get("line_items", []):
            name = item.get("product_name", "Unknown Product")
            qty = int(item.get("sku_count", 1))
            product_counter[name] += qty

    top_5 = product_counter.most_common(5)
    response_data = [{"name": n, "sold": s} for n, s in top_5]

    return JsonResponse(response_data, safe=False)



@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_product(request, cipher, id):
    ACCESS_TOKEN = get_valid_access_token()
    path = f'/product/202309/products/{id}'
    timestamp = int(time.time())
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "shop_cipher": cipher
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
            "x-tts-access-token": ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_orders_return(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/return_refund/202309/returns/search"
    timestamp = int(time.time())
    page_token = request.GET.get("page_token", "")
    page_size = request.GET.get("page_size", "10")  # default 10
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "page_size": page_size,
        "page_token": page_token,
        "shop_cipher": cipher
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
            "x-tts-access-token": ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_shop_performance(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop/performance"
    timestamp = int(time.time())

    # format date="YYYY-MM-DD"
    start_date = request.GET.get("start_date_ge", "")
    end_date = request.GET.get("end_date_lt", "")
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "start_date_ge": start_date,
        "end_date_lt": end_date,
        "shop_cipher": cipher
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
            "x-tts-access-token": ACCESS_TOKEN,
        }
    )

    return JsonResponse(response.json())


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_shop_performance_stats(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop/performance"

    # === Helper: Convert TikTok interval JSON → MonthlyStats format ===
    def map_interval(interval):
        return {
            "total_orders": interval.get("orders", 0),
            "customers": interval.get("buyers", 0),
            "sold": interval.get("units_sold", 0),
            "gmv": float(interval.get("gmv", {}).get("amount", 0.0)),
        }

    # === Helper: Hit TikTok API for date range ===
    def fetch_stats(start_date, end_date_exclusive):
        timestamp = int(time.time())
        params = {
            "app_key": TIKTOK_APP_KEY,
            "timestamp": timestamp,
            "shop_id": "7494101869654804070",
            "access_token": ACCESS_TOKEN,
            "start_date_ge": start_date,      # inclusive
            "end_date_lt": end_date_exclusive,  # exclusive
            "shop_cipher": cipher,
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
                "x-tts-access-token": ACCESS_TOKEN,
            },
        )

        try:
            res_json = response.json()
        except Exception:
            return {
                "total_orders": 0,
                "customers": 0,
                "sold": 0,
                "gmv": 0.0,
                "error": "Invalid JSON response from TikTok",
            }

        # --- Debug log biar kelihatan isi response TikTok ---
        print("TikTok API Response:", res_json)

        data = res_json.get("data")
        if not data or "performance" not in data:
            return {
                "total_orders": 0,
                "customers": 0,
                "sold": 0,
                "gmv": 0.0,
                "error": res_json.get("message", "No performance data"),
            }

        intervals = data.get("performance", {}).get("intervals", [])
        if not intervals:
            return {
                "total_orders": 0,
                "customers": 0,
                "sold": 0,
                "gmv": 0.0,
            }

        return map_interval(intervals[0])

    # === Ambil filter month & year dari query ===
    try:
        month = int(request.GET.get("month", datetime.today().month))
        year = int(request.GET.get("year", datetime.today().year))
    except ValueError:
        return JsonResponse({"error": "Invalid month or year"}, status=400)

    # === Tentukan periode waktu berdasarkan filter ===
    first_day = datetime(year, month, 1)
    # bulan ini (berdasarkan filter)
    first_day_this_month_str = first_day.strftime("%Y-%m-%d")

    # cari awal bulan berikutnya → untuk batas exclusive
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    end_this_month_str = next_month.strftime("%Y-%m-%d")

    # bulan lalu
    last_month_date = first_day - timedelta(days=1)
    first_day_last_month = last_month_date.replace(day=1)
    first_day_last_month_str = first_day_last_month.strftime("%Y-%m-%d")

    # akhir bulan lalu (exclusive)
    end_last_month_str = first_day.strftime("%Y-%m-%d")

    # === Hit API dua kali ===
    this_month_stats = fetch_stats(first_day_this_month_str, end_this_month_str)
    last_month_stats = fetch_stats(first_day_last_month_str, end_last_month_str)

    result = {
        "this_month": this_month_stats,
        "last_month": last_month_stats,
    }

    return JsonResponse(result)


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_tiktok_orders_year(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop/performance"

    def map_interval(interval):
        return {
            "total_orders": interval.get("orders", 0),
            "customers": interval.get("buyers", 0),
            "sold": interval.get("units_sold", 0),
            "gmv": float(interval.get("gmv", {}).get("amount", 0.0)),
        }

    def fetch_stats(start_date, end_date_exclusive):
        timestamp = int(time.time())
        params = {
            "app_key": TIKTOK_APP_KEY,
            "timestamp": timestamp,
            "shop_id": "7494101869654804070",  # ganti dengan shop_id kamu
            "access_token": ACCESS_TOKEN,
            "start_date_ge": start_date,
            "end_date_lt": end_date_exclusive,
            "shop_cipher": cipher,
        }

        request_option = {"qs": params, "uri": path, "body": {}}
        sign = generate_sign(request_option, TIKTOK_APP_SECRET)
        params["sign"] = sign

        url = f"{BASE_URL}{path}"
        response = requests.get(
            url,
            params=params,
            headers={
                "Content-Type": "application/json",
                "x-tts-access-token": ACCESS_TOKEN,
            },
        )

        try:
            res_json = response.json()
        except Exception:
            return {"total_orders": 0, "customers": 0, "sold": 0, "gmv": 0.0}

        # --- Debug log ---
        print("TikTok raw response:", res_json)

        # Pastikan selalu dict
        data = res_json.get("data") or {}
        performance = data.get("performance") or {}
        intervals = performance.get("intervals") or []

        if not intervals:
            return {"total_orders": 0, "customers": 0, "sold": 0, "gmv": 0.0}

        return map_interval(intervals[0])
    year = int(request.GET.get("year"))
    results = {}

    for month in range(1, 13):
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month_first = datetime(year + 1, 1, 1)
        else:
            next_month_first = datetime(year, month + 1, 1)

        stats = fetch_stats(
            first_day.strftime("%Y-%m-%d"),
            next_month_first.strftime("%Y-%m-%d"),
        )

        results[month] = stats["total_orders"]  # hanya return total order

    return JsonResponse(results)


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_shop_product_performance(request, cipher):
    ACCESS_TOKEN = get_valid_access_token()
    path = "/analytics/202405/shop_products/performance"
    timestamp = int(time.time())

    # format date="YYYY-MM-DD"
    start_date = request.GET.get("start_date_ge", "")
    end_date = request.GET.get("end_date_lt", "")
    params = {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "start_date_ge": start_date,
        "end_date_lt": end_date,
        "shop_cipher": cipher
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
            "x-tts-access-token": ACCESS_TOKEN,
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
