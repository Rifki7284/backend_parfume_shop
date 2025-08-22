import time, hashlib, hmac, requests

APP_KEY = "6h5s4qm76nrhk"
APP_SECRET = "2c2685bf956ed47b09f2ffd9b6c411e2fb0ec111"
BASE_URL = "https://open-api-sandbox.tiktokglobalshop.com"

def make_sign(path, params):
    # sort params alphabetically
    sorted_params = "".join([f"{k}{params[k]}" for k in sorted(params)])
    to_sign = path + sorted_params
    sign = hmac.new(APP_SECRET.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    return sign

def get_orders():
    path = "/api/orders/search"
    params = {
        "app_key": APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
    }
    params["sign"] = make_sign(path, params)

    res = requests.get(BASE_URL + path, params=params)
    return res.json()

print(get_orders())
