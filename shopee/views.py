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


def get_total_orders_and_buyers(request):
    try:
        time_from = request.GET.get("start_date_ge", "")
        time_to = request.GET.get("end_date_lt", "")

        token = get_token()
        timest = int(time.time())
        path = "/api/v2/order/get_order_list"
        sign = generate_sign_public(path, timest, token.access_token)

        url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign}"

        total_orders = 0
        buyers = set()
        order_sns = []  # simpan order_sn untuk ambil detail
        cursor = None
        page_size = 100

        # --- Ambil semua order ---
        while True:
            params = {
                "time_range_field": "create_time",
                "time_from": time_from,
                "time_to": time_to,
                "page_size": page_size,
            }
            if cursor:
                params["cursor"] = cursor

            resp = requests.get(url, params=params, timeout=20)
            data = resp.json()

            orders = data.get("response", {}).get("order_list", [])
            total_orders += len(orders)

            for order in orders:
                buyers.add(order.get("buyer_user_id"))
                order_sn = order.get("order_sn")
                if order_sn:
                    order_sns.append(order_sn)

            if not data.get("response", {}).get("more"):
                break
            cursor = data.get("response", {}).get("next_cursor")

        # --- Ambil detail order ---
        total_gmv = 0
        total_items_sold = 0
        path_detail = "/api/v2/order/get_order_detail"

        for i in range(0, len(order_sns), 50):
            chunk = order_sns[i:i+50]
            timest = int(time.time())
            sign_detail = generate_sign_public(path_detail, timest, token.access_token)
            url_detail = f"{host}{path_detail}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_detail}"
            resp_detail = requests.post(url_detail, json={"order_sn_list": chunk}, timeout=30)
            data_detail = resp_detail.json()

            order_list = data_detail.get("response", {}).get("order_list", [])
            for od in order_list:
                total_gmv += int(od.get("total_amount", 0))
                for item in od.get("item_list", []):
                    total_items_sold += int(item.get("model_quantity_purchased", 0))

        # --- Sesuaikan response untuk TS ---
        response = {
            "data": {
                "performance": {
                    "intervals": [
                        {
                            "orders": total_orders,
                            "gmv": {"amount": total_gmv},
                            "units_sold": total_items_sold,
                            "buyers": len(buyers)
                        }
                    ]
                }
            }
        }

        return JsonResponse(response)

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
        now = datetime.datetime.now()
        token = get_token()  # asumsi ada helper ini
        # --- Step 1: ambil semua item_id dari get_item_list ---
        path_list = "/api/v2/product/get_item_list"
        timest = int(time.time())
        sign_list = generate_sign_public(path_list, timest, token.access_token)
        url_list = f"{host}{path_list}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_list}"

        all_item_ids = []
        offset = 0
        page_size = 50  # sesuaikan / naikkan kalau API memperbolehkan

        while True:
            params_list = {
                "offset": offset,
                "page_size": page_size,
                "item_status": ["NORMAL"]
            }
            resp_list = requests.get(url_list, params=params_list, timeout=20)
            data_list = resp_list.json()
            items = data_list.get("response", {}).get("item", [])
            all_item_ids.extend([it["item_id"] for it in items])

            if not data_list.get("response", {}).get("has_next_page", False):
                break
            offset += page_size

        if not all_item_ids:
            return JsonResponse({"top_products": []}, safe=False)

        # --- Step 2: ambil get_item_extra_info (batched) ---
        path_extra = "/api/v2/product/get_item_extra_info"
        extra_items = []
        batch_size = 50  # pastikan sesuai limit API
        for chunk in chunked(all_item_ids, batch_size):
            timest = int(time.time())
            sign_extra = generate_sign_public(
                path_extra, timest, token.access_token)
            url_extra = f"{host}{path_extra}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_extra}"
            resp_extra = requests.get(
                url_extra, params={"item_id_list": chunk}, timeout=20)
            data_extra = resp_extra.json()
            extra_items.extend(data_extra.get(
                "response", {}).get("item_list", []))

        # --- Step 3: hitung sold, sort, ambil top N ---
        for it in extra_items:
            it["_sold_count"] = _get_sold_count(it)

        top_n = 5
        extra_items_sorted = sorted(
            extra_items, key=lambda x: x["_sold_count"], reverse=True)
        top_items = extra_items_sorted[:top_n]
        top_ids = [it["item_id"] for it in top_items]

        # --- Step 4: panggil get_item_base_info untuk top_ids dan gabungkan nama ---
        path_base = "/api/v2/product/get_item_base_info"
        base_info_list = []
        for chunk in chunked(top_ids, batch_size):
            timest = int(time.time())
            sign_base = generate_sign_public(
                path_base, timest, token.access_token)
            url_base = f"{host}{path_base}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_base}"
            resp_base = requests.get(
                url_base, params={"item_id_list": chunk}, timeout=20)
            data_base = resp_base.json()
            base_info_list.extend(data_base.get(
                "response", {}).get("item_list", []))

        id_to_name = {p["item_id"]: p.get("item_name") for p in base_info_list}

        # --- Final: gabungkan dan return hanya name + sold (plus item_id opsional) ---
        result = []
        for it in top_items:
            iid = it.get("item_id")
            result.append({
                "item_id": iid,
                "name": id_to_name.get(iid, None),
                "sold": it.get("_sold_count", 0)
            })

        return JsonResponse({"top_products": result}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_total_sold_this_month(request):
    try:
        token = get_token()
        # --- Step 1: ambil semua item_id dari get_item_list ---
        path_list = "/api/v2/product/get_item_list"
        timest = int(time.time())
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
            all_item_ids.extend([it["item_id"] for it in items])

            if not data_list.get("response", {}).get("has_next_page", False):
                break
            offset += page_size

        if not all_item_ids:
            return JsonResponse({"total_sold_this_month": 0}, safe=False)

        # --- Step 2: ambil get_item_extra_info (batched) ---
        path_extra = "/api/v2/product/get_item_extra_info"
        total_sold = 0
        batch_size = 50

        for i in range(0, len(all_item_ids), batch_size):
            chunk = all_item_ids[i:i + batch_size]
            timest = int(time.time())
            sign_extra = generate_sign_public(
                path_extra, timest, token.access_token)
            url_extra = f"{host}{path_extra}?partner_id={partner_id}&timestamp={timest}&access_token={token.access_token}&shop_id={shop_id}&sign={sign_extra}"

            resp_extra = requests.get(
                url_extra, params={"item_id_list": chunk}, timeout=20)
            data_extra = resp_extra.json()
            item_list = data_extra.get("response", {}).get("item_list", [])

            for item in item_list:
                # pakai field sold_30_days (kalau ada), fallback ke 0
                total_sold += int(item.get("sold_30_days", 0))

        return JsonResponse({"total_sold_this_month": total_sold}, safe=False)

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
        page_size = int(request.GET.get("page_size", 20))

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
