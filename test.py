import hmac
import time
import hashlib
import requests
import json
def get_token_shop_level(code, partner_id, tmp_partner_key, shop_id):
    timest = int(time.time())
    host = "https://openplatform.sandbox.test-stable.shopee.sg"
    path = "/api/v2/auth/token/get"
    body = {"code": code, "shop_id": shop_id, "partner_id": partner_id}
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    partner_key = tmp_partner_key.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    # print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    print("Status:", resp.status_code)
    print("Response JSON:", ret)
    print(access_token)
    print(new_refresh_token)
    return access_token, new_refresh_token

def refresh_token(partner_id, partner_key_str, shop_id, refresh_token):
    timest = int(time.time())
    host = "https://openplatform.sandbox.test-stable.shopee.sg"
    path = "/api/v2/auth/access_token/get"

    # base string untuk sign
    base_string = f"{partner_id}{path}{timest}".encode()
    partner_key = partner_key_str.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={timest}&sign={sign}"
    headers = {"Content-Type": "application/json"}

    body = {
        "partner_id": partner_id,
        "shop_id": shop_id,
        "refresh_token": refresh_token
    }

    resp = requests.post(url, json=body, headers=headers)
    ret = resp.json()

    print("Status:", resp.status_code)
    print("Response:", json.dumps(ret, indent=2))

    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")

    print("New Access Token :", access_token)
    print("New Refresh Token:", new_refresh_token)

    return access_token, new_refresh_token


def shop_auth():
    timest = int(time.time())
    host = "https://openplatform.sandbox.test-stable.shopee.sg"
    path = "/api/v2/shop/auth_partner"
    redirect_url = "https://callback-shopee.vercel.app/"
    partner_id = 1186913
    tmp = "shpk6a63516246536748554547686c7761585569535452557a4b735458627175"
    partner_key = tmp.encode()
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    ##generate api
    url = host + path + "?partner_id=%s&timestamp=%s&sign=%s&redirect=%s" % (partner_id, timest, sign, redirect_url)
    print(url)
# shop_auth()
get_token_shop_level("54737a4c76626e464370694462664e77",1186913,"shpk6a63516246536748554547686c7761585569535452557a4b735458627175",225919411)
# refresh_token(
#     1186913,
#     "shpk6a63516246536748554547686c7761585569535452557a4b735458627175",
#     225919411,
#     "eyJhbGciOiJIUzI1NiJ9.COG4SBABGN3X22sgAijZqbHGBjCk2q1IOAFAAQ.NX5_xWAQx5L8kl21OzBzDFjqnkOvS8VzrEYWaoJ6qZk"
# )