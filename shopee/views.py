# views.py
import time
import hmac
import hashlib
import requests
import datetime
import json
from django.http import JsonResponse
from django.conf import settings
from shopee.models import ShopeeToken
from django.views.decorators.csrf import csrf_exempt
import os
from dotenv import load_dotenv
from rest_framework.decorators import api_view, permission_classes
from users.permissions import IsStaffUser
from rest_framework.permissions import IsAuthenticated
load_dotenv()

host = "https://openplatform.sandbox.test-stable.shopee.sg"
partner_id = str(settings.PARTNER_ID).strip()
partner_key_str = str(settings.PARTNER_KEY).strip()
shop_id = str(settings.SHOP_ID).strip()


def generate_sign_public(path, timest, access_token=None):
    """Utility untuk generate HMAC-SHA256 sign Shopee"""
    base_string = f"{partner_id}{path}{timest}{access_token or ''}{shop_id}".encode()
    return hmac.new(partner_key_str.encode(), base_string, hashlib.sha256).hexdigest()


def get_token():
    """Ambil token terbaru dari DB"""
    token = ShopeeToken.objects.order_by("-id").first()
    if not token:
        raise ValueError("Shopee token not found")
    return token


def Shop_info(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/shop/get_shop_info"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&sign={sign}&shop_id={shop_id}&access_token={token.access_token}"

        resp = requests.get(url, headers={"Content-Type": "application/json"})
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_product_list(request):
    try:
        now = datetime.datetime.now()
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/product/get_item_list"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        all_item_ids = []
        offset = 0
        page_size = 50  # bisa diperbesar (max biasanya 100)

        while True:
            params = {
                "offset": offset,
                "page_size": page_size,
                "item_status": ["NORMAL"]
            }

            resp = requests.get(url, params=params, timeout=20)
            data = resp.json()

            # ambil item_id dari item list
            items = data.get("response", {}).get("item", [])
            for it in items:
                all_item_ids.append(it["item_id"])

            # cek apakah masih ada next page
            has_next = data.get("response", {}).get("has_next_page", False)
            if not has_next:
                break

            offset += page_size

        return JsonResponse({"item_ids": all_item_ids}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_product_info(request):
    try:
        now = datetime.datetime.now()
        token = get_token()
        timest = int(time.time())

        # --- Step 1: Ambil semua item_id ---
        path_list = "/api/v2/product/get_item_list"
        sign_list = generate_sign_public(path_list, timest, token.access_token)
        url_list = f"{host}{path_list}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_list}"

        all_item_ids = []
        offset = 0
        page_size = 50

        while True:
            params_list = {
                "offset": offset,
                "page_size": page_size,
                "item_status": ["NORMAL"]
            }
            resp_list = requests.get(url_list, params=params_list, timeout=20)
            data_list = resp_list.json()

            items = data_list.get("response", {}).get("item", [])
            for it in items:
                all_item_ids.append(it["item_id"])

            if not data_list.get("response", {}).get("has_next_page", False):
                break
            offset += page_size

        # --- Step 2: Masukkan item_id_list ke get_item_base_info ---
        path_info = "/api/v2/product/get_item_base_info"
        sign_info = generate_sign_public(path_info, timest, token.access_token)
        url_info = f"{host}{path_info}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_info}"

        params_info = {
            "item_id_list": all_item_ids  # ← hasil dari step 1
        }

        resp_info = requests.get(url_info, params=params_info, timeout=20)
        return JsonResponse(resp_info.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def chunked(iterable, size):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def _get_sold_count(extra_item):
    """
    Coba beberapa nama field yang umum dipakai di extra_info.
    Tambah key jika sandbox/production punya nama lain.
    """
    for k in ("historical_sold", "sold", "sales", "total_sold", "sold_count"):
        v = extra_item.get(k)
        if v is not None:
            try:
                return int(v)
            except Exception:
                try:
                    return int(float(v))
                except Exception:
                    return 0
    # fallback 0 jika tidak ada
    return 0


def get_top_products(request):
    try:
        token = get_token()
        timest = int(time.time())

        # === Base info ===
        list_path = "/api/v2/order/get_order_list"
        list_sign = generate_sign_public(list_path, timest, token.access_token)
        list_url = (
            f"{host}{list_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={list_sign}"
        )

        detail_path = "/api/v2/order/get_order_detail"
        detail_sign = generate_sign_public(
            detail_path, timest, token.access_token)
        detail_url = (
            f"{host}{detail_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={detail_sign}"
        )

        page_size = 100
        now = datetime.datetime.now()

        # === Helper: awal & akhir bulan ===
        def get_month_range(dt: datetime.datetime):
            start = datetime.datetime(dt.year, dt.month, 1)
            next_month = datetime.datetime(
                dt.year + (dt.month // 12), ((dt.month % 12) + 1), 1
            )
            end = next_month - datetime.timedelta(seconds=1)
            return start, end

        # === Helper: fetch SNs dalam range (max 15 hari sekali) ===
        def fetch_orders_in_range(start_time, end_time):
            all_orders = []
            cursor = ""
            params = {
                "time_range_field": "create_time",
                "time_from": int(start_time.timestamp()),
                "time_to": int(end_time.timestamp()),
                "page_size": page_size,
            }

            while True:
                if cursor:
                    params["cursor"] = cursor

                resp = requests.get(list_url, params=params, timeout=20)
                data = resp.json()

                orders = data.get("response", {}).get("order_list", [])
                all_orders.extend([o["order_sn"] for o in orders])

                more = data.get("response", {}).get("more", False)
                cursor = data.get("response", {}).get("next_cursor", "")

                if not more or not cursor:
                    break

            return all_orders

        # === Helper: full month (split 15 hari) ===
        def fetch_full_month(start_month, end_month):
            all_orders = []
            temp_start = start_month
            while temp_start < end_month:
                temp_end = min(
                    temp_start + datetime.timedelta(days=15), end_month)
                all_orders.extend(fetch_orders_in_range(temp_start, temp_end))
                temp_start = temp_end
            return all_orders

        # === Helper: fetch detail order (batch 50) + hitung per produk ===
        def fetch_top_products(order_sns):
            product_sales = {}
            for i in range(0, len(order_sns), 50):
                batch = order_sns[i:i+50]
                payload = {
                    "order_sn_list": ",".join(batch),
                    "response_optional_fields": "item_list,order_status",
                }
                resp = requests.get(detail_url, params=payload, timeout=20)
                data = resp.json()
                order_list = data.get("response", {}).get("order_list", [])

                for order in order_list:
                    if order.get("order_status") == "CANCELLED":
                        continue
                    for item in order.get("item_list", []):
                        item_id = item.get("item_id")
                        name = item.get("item_name")
                        qty = item.get("model_quantity_purchased", 0)

                        if item_id not in product_sales:
                            product_sales[item_id] = {
                                "name": name,
                                "sold": 0
                            }
                        product_sales[item_id]["sold"] += qty

            # urutkan berdasarkan sold
            sorted_products = sorted(
                product_sales.values(),
                key=lambda x: x["sold"],
                reverse=True
            )[:5]

            return sorted_products

        # Bulan ini
        this_start, this_end = get_month_range(now)
        this_month_sns = fetch_full_month(this_start, this_end)
        top_this_month = fetch_top_products(this_month_sns)

        return JsonResponse(
            top_this_month, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def fetch_orders_in_range(start_time, end_time, token, path, url_base, page_size=100):
    """Helper untuk fetch order dengan pagination Shopee."""
    total_orders = 0
    cursor = ""
    params = {
        "time_range_field": "create_time",
        "time_from": int(start_time.timestamp()),
        "time_to": int(end_time.timestamp()),
        "page_size": page_size,
    }

    while True:
        if cursor:
            params["cursor"] = cursor
        else:
            params.pop("cursor", None)

        resp = requests.get(url_base, params=params, timeout=20)
        data = resp.json()

        order_list = data.get("response", {}).get("order_list", [])
        total_orders += len(order_list)

        response_meta = data.get("response", {})
        if response_meta.get("more") and response_meta.get("next_cursor"):
            cursor = response_meta["next_cursor"]
        else:
            break

    return total_orders


def get_month_date_ranges(year, month):
    """Bagi 1 bulan jadi beberapa range 15 hari."""
    first_day = datetime.datetime(year, month, 1)
    if month == 12:
        next_month = datetime.datetime(year + 1, 1, 1)
    else:
        next_month = datetime.datetime(year, month + 1, 1)

    ranges = []
    current_start = first_day
    while current_start < next_month:
        current_end = min(
            current_start + datetime.timedelta(days=15), next_month)
        ranges.append((current_start, current_end))
        current_start = current_end
    return ranges


def get_total_orders_month(request):
    try:
        # --- Token & Signing
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/order/get_order_list"
        sign = generate_sign_public(path, timest, token.access_token)
        url_base = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        now = datetime.datetime.now()

        # bulan ini
        this_month_year = now.year
        this_month = now.month
        this_month_ranges = get_month_date_ranges(this_month_year, this_month)

        total_this_month = 0
        for start, end in this_month_ranges:
            total_this_month += fetch_orders_in_range(
                start, end, token, path, url_base)

        # bulan lalu
        last_month_date = (now.replace(day=1) - datetime.timedelta(days=1))
        last_month_year = last_month_date.year
        last_month = last_month_date.month
        last_month_ranges = get_month_date_ranges(last_month_year, last_month)

        total_last_month = 0
        for start, end in last_month_ranges:
            total_last_month += fetch_orders_in_range(
                start, end, token, path, url_base)

        return JsonResponse({
            "total_orders_this_month": total_this_month,
            "total_orders_last_month": total_last_month,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_shopee_orders_year(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/order/get_order_list"
        sign = generate_sign_public(path, timest, token.access_token)
        url_base = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        now = datetime.datetime.now()
        year = now.year

        # Jan–Des
        sales_data = {}

        for month in range(1, 13):
            month_ranges = get_month_date_ranges(year, month)

            total_orders = 0
            for start, end in month_ranges:
                total_orders += fetch_orders_in_range(
                    start, end, token, path, url_base
                )

            # simpan ke dict dengan key angka bulan
            sales_data[month] = total_orders

        return JsonResponse(sales_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_total_customers(request):
    try:
        token = get_token()
        timest = int(time.time())

        # === Base info ===
        list_path = "/api/v2/order/get_order_list"
        list_sign = generate_sign_public(list_path, timest, token.access_token)
        list_url = (
            f"{host}{list_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={list_sign}"
        )

        detail_path = "/api/v2/order/get_order_detail"
        detail_sign = generate_sign_public(
            detail_path, timest, token.access_token)
        detail_url = (
            f"{host}{detail_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={detail_sign}"
        )

        page_size = 100
        now = datetime.datetime.now()

        # === Helper: awal & akhir bulan ===
        def get_month_range(dt: datetime.datetime):
            start = datetime.datetime(dt.year, dt.month, 1)
            next_month = datetime.datetime(
                dt.year + (dt.month // 12), ((dt.month % 12) + 1), 1
            )
            end = next_month - datetime.timedelta(seconds=1)
            return start, end

        # === Helper: fetch SNs dalam range (max 15 hari sekali) ===
        def fetch_orders_in_range(start_time, end_time):
            all_orders = []
            cursor = ""
            params = {
                "time_range_field": "create_time",
                "time_from": int(start_time.timestamp()),
                "time_to": int(end_time.timestamp()),
                "page_size": page_size,
            }

            while True:
                if cursor:
                    params["cursor"] = cursor

                resp = requests.get(list_url, params=params, timeout=20)
                data = resp.json()

                orders = data.get("response", {}).get("order_list", [])
                all_orders.extend([o["order_sn"] for o in orders])

                more = data.get("response", {}).get("more", False)
                cursor = data.get("response", {}).get("next_cursor", "")

                if not more or not cursor:
                    break

            return all_orders

        # === Helper: fetch full month (split 15 hari) ===
        def fetch_full_month(start_month, end_month):
            all_orders = []
            temp_start = start_month
            while temp_start < end_month:
                temp_end = min(
                    temp_start + datetime.timedelta(days=15), end_month)
                all_orders.extend(fetch_orders_in_range(temp_start, temp_end))
                temp_start = temp_end
            return all_orders

        # === Helper: fetch buyers (duplikat dihitung) ===
        def fetch_buyers(order_sns):
            buyers = []
            for i in range(0, len(order_sns), 50):
                batch = order_sns[i:i+50]
                payload = {
                    "order_sn_list": ",".join(batch),
                    "response_optional_fields": "buyer_user_id,order_status",
                }
                resp = requests.get(detail_url, params=payload, timeout=20)
                data = resp.json()
                order_list = data.get("response", {}).get("order_list", [])

                for order in order_list:
                    if order.get("order_status") == "CANCELLED":
                        continue
                    buyer_id = order.get("buyer_user_id")
                    if buyer_id:
                        buyers.append(buyer_id)  # simpan duplikat

            return buyers

        # Bulan ini
        this_start, this_end = get_month_range(now)
        this_month_sns = fetch_full_month(this_start, this_end)
        this_month_buyers = fetch_buyers(this_month_sns)

        # Bulan lalu
        last_month_ref = this_start - datetime.timedelta(days=1)
        last_start, last_end = get_month_range(last_month_ref)
        last_month_sns = fetch_full_month(last_start, last_end)
        last_month_buyers = fetch_buyers(last_month_sns)

        return JsonResponse({
            "this_month_customers": len(this_month_buyers),
            "last_month_customers": len(last_month_buyers),
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_total_sold(request):
    try:
        token = get_token()
        timest = int(time.time())

        # === Base info ===
        list_path = "/api/v2/order/get_order_list"
        list_sign = generate_sign_public(list_path, timest, token.access_token)
        list_url = (
            f"{host}{list_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={list_sign}"
        )

        detail_path = "/api/v2/order/get_order_detail"
        detail_sign = generate_sign_public(
            detail_path, timest, token.access_token)
        detail_url = (
            f"{host}{detail_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={detail_sign}"
        )

        page_size = 100
        now = datetime.datetime.now()

        # === Helper: awal & akhir bulan ===
        def get_month_range(dt: datetime.datetime):
            start = datetime.datetime(dt.year, dt.month, 1)
            next_month = datetime.datetime(
                dt.year + (dt.month // 12), ((dt.month % 12) + 1), 1
            )
            end = next_month - datetime.timedelta(seconds=1)
            return start, end

        # === Helper: fetch SNs dalam range (max 15 hari sekali) ===
        def fetch_orders_in_range(start_time, end_time):
            all_orders = []
            cursor = ""
            params = {
                "time_range_field": "create_time",
                "time_from": int(start_time.timestamp()),
                "time_to": int(end_time.timestamp()),
                "page_size": page_size,
            }

            while True:
                if cursor:
                    params["cursor"] = cursor

                resp = requests.get(list_url, params=params, timeout=20)
                data = resp.json()

                orders = data.get("response", {}).get("order_list", [])
                all_orders.extend([o["order_sn"] for o in orders])

                more = data.get("response", {}).get("more", False)
                cursor = data.get("response", {}).get("next_cursor", "")

                if not more or not cursor:
                    break

            return all_orders

        # === Helper: full month (split 15 hari) ===
        def fetch_full_month(start_month, end_month):
            all_orders = []
            temp_start = start_month
            while temp_start < end_month:
                temp_end = min(
                    temp_start + datetime.timedelta(days=15), end_month)
                all_orders.extend(fetch_orders_in_range(temp_start, temp_end))
                temp_start = temp_end
            return all_orders

        # === Helper: fetch detail order (batch 50) + hitung total sold ===
        def fetch_total_sold(order_sns):
            total_sold = 0
            for i in range(0, len(order_sns), 50):
                batch = order_sns[i:i+50]
                payload = {
                    "order_sn_list": ",".join(batch),
                    "response_optional_fields": "item_list,order_status",
                }
                resp = requests.get(detail_url, params=payload, timeout=20)
                data = resp.json()
                order_list = data.get("response", {}).get("order_list", [])

                for order in order_list:
                    # Skip jika order cancelled
                    if order.get("order_status") == "CANCELLED":
                        continue
                    for item in order.get("item_list", []):
                        total_sold += item.get("model_quantity_purchased", 0)

            return total_sold

        # Bulan ini
        this_start, this_end = get_month_range(now)
        this_month_sns = fetch_full_month(this_start, this_end)
        this_month_sold = fetch_total_sold(this_month_sns)

        # Bulan lalu
        last_month_ref = this_start - datetime.timedelta(days=1)
        last_start, last_end = get_month_range(last_month_ref)
        last_month_sns = fetch_full_month(last_start, last_end)
        last_month_sold = fetch_total_sold(last_month_sns)

        return JsonResponse({
            "this_month_sold": this_month_sold,
            "last_month_sold": last_month_sold,
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_total_gmv(request):
    try:
        token = get_token()
        timest = int(time.time())

        # === Base info ===
        list_path = "/api/v2/order/get_order_list"
        list_sign = generate_sign_public(list_path, timest, token.access_token)
        list_url = (
            f"{host}{list_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={list_sign}"
        )

        detail_path = "/api/v2/order/get_order_detail"
        detail_sign = generate_sign_public(
            detail_path, timest, token.access_token)
        detail_url = (
            f"{host}{detail_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={detail_sign}"
        )

        page_size = 100
        now = datetime.datetime.now()

        # === Helper: awal & akhir bulan ===
        def get_month_range(dt: datetime.datetime):
            start = datetime.datetime(dt.year, dt.month, 1)
            next_month = datetime.datetime(
                dt.year + (dt.month // 12), ((dt.month % 12) + 1), 1
            )
            end = next_month - datetime.timedelta(seconds=1)
            return start, end

        # === Helper: fetch SNs dalam range (max 15 hari sekali) ===
        def fetch_orders_in_range(start_time, end_time):
            all_orders = []
            cursor = ""
            params = {
                "time_range_field": "create_time",
                "time_from": int(start_time.timestamp()),
                "time_to": int(end_time.timestamp()),
                "page_size": page_size,
            }

            while True:
                if cursor:
                    params["cursor"] = cursor

                resp = requests.get(list_url, params=params, timeout=20)
                data = resp.json()

                orders = data.get("response", {}).get("order_list", [])
                all_orders.extend([o["order_sn"] for o in orders])

                more = data.get("response", {}).get("more", False)
                cursor = data.get("response", {}).get("next_cursor", "")

                if not more or not cursor:
                    break

            return all_orders

        # === Helper: full month (split 15 hari) ===
        def fetch_full_month(start_month, end_month):
            all_orders = []
            temp_start = start_month
            while temp_start < end_month:
                temp_end = min(
                    temp_start + datetime.timedelta(days=15), end_month)
                all_orders.extend(fetch_orders_in_range(temp_start, temp_end))
                temp_start = temp_end
            return all_orders

        # === Helper: fetch detail order (batch 50) + hitung GMV ===
        def fetch_total_gmv(order_sns):
            gmv = 0
            for i in range(0, len(order_sns), 50):
                batch = order_sns[i:i+50]
                payload = {
                    "order_sn_list": ",".join(batch),
                    "response_optional_fields": "item_list,order_status",
                }
                resp = requests.get(detail_url, params=payload, timeout=20)
                data = resp.json()
                order_list = data.get("response", {}).get("order_list", [])

                for order in order_list:
                    # Skip jika order cancelled
                    if order.get("order_status") == "CANCELLED":
                        continue
                    for item in order.get("item_list", []):
                        qty = item.get("model_quantity_purchased", 0)
                        # pakai harga diskon
                        price = float(item.get("model_discounted_price", 0))
                        gmv += qty * price
            return gmv

        # Bulan ini
        this_start, this_end = get_month_range(now)
        this_month_sns = fetch_full_month(this_start, this_end)
        this_month_gmv = fetch_total_gmv(this_month_sns)

        # Bulan lalu
        last_month_ref = this_start - datetime.timedelta(days=1)
        last_start, last_end = get_month_range(last_month_ref)
        last_month_sns = fetch_full_month(last_start, last_end)
        last_month_gmv = fetch_total_gmv(last_month_sns)

        return JsonResponse({
            "this_month_gmv": this_month_gmv,
            "last_month_gmv": last_month_gmv,
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_shopee_stats(request):
    try:
        token = get_token()
        timest = int(time.time())

        # === Base info ===
        list_path = "/api/v2/order/get_order_list"
        list_sign = generate_sign_public(list_path, timest, token.access_token)
        list_url = (
            f"{host}{list_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={list_sign}"
        )

        detail_path = "/api/v2/order/get_order_detail"
        detail_sign = generate_sign_public(
            detail_path, timest, token.access_token)
        detail_url = (
            f"{host}{detail_path}?partner_id={partner_id}"
            f"&timestamp={timest}&access_token={token.access_token}"
            f"&shop_id={shop_id}&sign={detail_sign}"
        )

        page_size = 100
        now = datetime.datetime.now()

        # === Helper: awal & akhir bulan ===
        def get_month_range(dt: datetime.datetime):
            start = datetime.datetime(dt.year, dt.month, 1)
            next_month = datetime.datetime(
                dt.year + (dt.month // 12), ((dt.month % 12) + 1), 1
            )
            end = next_month - datetime.timedelta(seconds=1)
            return start, end

        # === Helper: fetch order_sn dalam range (max 15 hari sekali) ===
        def fetch_orders_in_range(start_time, end_time):
            all_orders = []
            cursor = ""
            params = {
                "time_range_field": "create_time",
                "time_from": int(start_time.timestamp()),
                "time_to": int(end_time.timestamp()),
                "page_size": page_size,
            }
            while True:
                if cursor:
                    params["cursor"] = cursor

                resp = requests.get(list_url, params=params, timeout=20)
                data = resp.json()

                orders = data.get("response", {}).get("order_list", [])
                all_orders.extend([o["order_sn"] for o in orders])

                more = data.get("response", {}).get("more", False)
                cursor = data.get("response", {}).get("next_cursor", "")

                if not more or not cursor:
                    break
            return all_orders

        # === Helper: fetch full month (split 15 hari) ===
        def fetch_full_month(start_month, end_month):
            all_orders = []
            temp_start = start_month
            while temp_start < end_month:
                temp_end = min(
                    temp_start + datetime.timedelta(days=15), end_month)
                all_orders.extend(fetch_orders_in_range(temp_start, temp_end))
                temp_start = temp_end
            return all_orders

        # === Helper: fetch detail order (batch 50) ===
        def fetch_order_details(order_sns):
            details = []
            for i in range(0, len(order_sns), 50):
                batch = order_sns[i:i+50]
                payload = {
                    "order_sn_list": ",".join(batch),
                    "response_optional_fields": "item_list,order_status,buyer_user_id",
                }
                resp = requests.get(detail_url, params=payload, timeout=20)
                data = resp.json()
                order_list = data.get("response", {}).get("order_list", [])
                details.extend(order_list)
            return details

        # === Kalkulasi untuk 1 bulan (orders, customers, sold, gmv) ===
        def calculate_stats(start, end):
            order_sns = fetch_full_month(start, end)
            details = fetch_order_details(order_sns)

            total_orders = 0
            buyers = []
            total_sold = 0
            gmv = 0

            for order in details:
                if order.get("order_status") == "CANCELLED":
                    continue
                total_orders += 1
                buyer_id = order.get("buyer_user_id")
                if buyer_id:
                    buyers.append(buyer_id)
                for item in order.get("item_list", []):
                    qty = item.get("model_quantity_purchased", 0)
                    # harga diskon
                    price = float(item.get("model_discounted_price", 0))
                    total_sold += qty
                    gmv += qty * price

            return {
                "total_orders": total_orders,
                "customers": len(buyers),  # duplikat dihitung
                "sold": total_sold,
                "gmv": gmv,
            }

        # Bulan ini
        this_start, this_end = get_month_range(now)
        this_stats = calculate_stats(this_start, this_end)

        # Bulan lalu
        last_month_ref = this_start - datetime.timedelta(days=1)
        last_start, last_end = get_month_range(last_month_ref)
        last_stats = calculate_stats(last_start, last_end)

        return JsonResponse({
            "this_month": this_stats,
            "last_month": last_stats,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_item_list(token):
    timest = int(time.time())
    path = "/api/v2/product/get_item_list"
    sign = generate_sign_public(path, timest, token.access_token)

    url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"
    return requests.get(url).json()


def get_item_detail(token, item_ids):
    timest = int(time.time())
    path = "/api/v2/product/get_item_base_info"
    sign = generate_sign_public(path, timest, token.access_token)

    item_id_str = ",".join([str(i) for i in item_ids])
    url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}&item_id_list={item_id_str}"
    return requests.get(url).json()


def product_list(request):
    try:
        token = get_token()
        item_list_resp = get_item_list(token)

        if "response" not in item_list_resp:
            return JsonResponse(item_list_resp, safe=False)

        item_ids = [item["item_id"]
                    for item in item_list_resp["response"].get("item", [])]
        details_resp = get_item_detail(token, item_ids)

        products = []
        if "response" in details_resp:
            for product in details_resp["response"].get("item_list", []):
                products.append({
                    "item_id": product["item_id"],
                    "name": product.get("item_name", ""),
                    "description": product.get("description", ""),
                    "price": product.get("price_info", [{}])[0].get("current_price"),
                    "stock": product.get("stock_info", {}).get("stock"),
                })

        return JsonResponse(products, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStaffUser])
def get_order_list(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/order/get_order_list"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        cursor = request.GET.get("cursor", "")  # pagination cursor
        page_size = int(request.GET.get("page_size", 10))
        status = request.GET.get("status", "")  # ✅ filter status (optional)

        now = datetime.datetime.now()
        end_time = now
        start_time = now - datetime.timedelta(days=15)

        params = {
            "time_range_field": "create_time",
            "time_from": int(start_time.timestamp()),
            "time_to": int(end_time.timestamp()),
            "page_size": page_size,
        }

        if cursor:
            params["cursor"] = cursor

        if status and status.lower() != "all":
            params["order_status"] = status.upper()

        resp = requests.get(url, params=params, timeout=20)
        data = resp.json()

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def get_order_detail(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/order/get_order_detail"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        # order_sn_list bisa dikirim dari frontend (misalnya user klik detail order)
        order_sn_list = request.GET.get("order_sn_list")
        if not order_sn_list:
            return JsonResponse({"error": "order_sn_list is required"}, status=400)

        params = {
            "order_sn_list": order_sn_list,
            "response_optional_fields": "total_amount,item_list,order_status,payment_method,package_list,shipping_carrier"
        }

        resp = requests.get(url, params=params, timeout=20)
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_tracking_number(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/logistics/get_tracking_number"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        # order_sn_list bisa dikirim dari frontend (misalnya user klik detail order)
        order_sn_list = request.GET.get("order_sn_list")
        if not order_sn_list:
            return JsonResponse({"error": "order_sn_list is required"}, status=400)

        params = {
            "order_sn": order_sn_list,
        }

        resp = requests.get(url, params=params, timeout=20)
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_tracking_info(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/logistics/get_tracking_info"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        # order_sn_list bisa dikirim dari frontend (misalnya user klik detail order)
        order_sn_list = request.GET.get("order_sn_list")
        if not order_sn_list:
            return JsonResponse({"error": "order_sn_list is required"}, status=400)

        params = {
            "order_sn": order_sn_list,
        }

        resp = requests.get(url, params=params, timeout=20)
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_return_list(request):
    try:
        token = get_token()
        now = datetime.datetime.now()

        # ambil 15 hari terakhir (Shopee max 15 hari range)
        end_time = now
        start_time = now - datetime.timedelta(days=15)

        timest = int(time.time())
        path = "/api/v2/returns/get_return_list"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        params = {
            "time_range_field": "create_time",
            "time_from": int(start_time.timestamp()),
            "time_to": int(end_time.timestamp()),
            "page_size": 100
        }

        resp = requests.get(url, params=params, timeout=20)
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_return_detail(request):
    try:
        token = get_token()
        timest = int(time.time())
        path = "/api/v2/returns/get_return_detail"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        params = {
            "return_sn": "201214JAJXU6G7,201214JASXYXY6"
        }

        resp = requests.get(url, params=params, timeout=20)
        return JsonResponse(resp.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_top_5_products(request):
    try:
        token = get_token()
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(days=15)

        # 1. Ambil order list
        timest = int(time.time())
        path = "/api/v2/order/get_order_list"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        params = {
            "time_range_field": "create_time",
            "time_from": int(start_time.timestamp()),
            "time_to": int(now.timestamp()),
            "page_size": 100
        }
        resp = requests.get(url, params=params, timeout=20).json()

        if "response" not in resp:
            return JsonResponse(resp, safe=False)

        order_sn_list = [o["order_sn"]
                         for o in resp["response"].get("order_list", [])]

        # 2. Ambil detail setiap order
        sales_counter = {}
        path_detail = "/api/v2/order/get_order_detail"

        for order_sn in order_sn_list:
            timest = int(time.time())
            sign = generate_sign_public(
                path_detail, timest, token.access_token)
            detail_url = f"{host}{path_detail}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}&order_sn_list={order_sn}"
            order_detail = requests.get(detail_url, timeout=20).json()

            if "response" in order_detail:
                for order in order_detail["response"].get("order_list", []):
                    for item in order.get("item_list", []):
                        item_id = item["item_id"]
                        qty = item.get("model_quantity_purchased", 0)
                        sales_counter[item_id] = sales_counter.get(
                            item_id, 0) + qty

        # 3. Ambil top 5
        top_items = sorted(sales_counter.items(),
                           key=lambda x: x[1], reverse=True)[:5]
        top_ids = [str(item_id) for item_id, _ in top_items]

        if not top_ids:
            return JsonResponse({"top_5": [], "sales_count": []}, safe=False)

        # 4. Ambil detail barang
        timest = int(time.time())
        path_product = "/api/v2/product/get_item_base_info"
        sign = generate_sign_public(path_product, timest, token.access_token)
        product_url = f"{host}{path_product}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}&item_id_list={','.join(top_ids)}"
        products = requests.get(product_url, timeout=20).json()

        return JsonResponse({
            "top_5": products,
            "sales_count": top_items
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
