import time, hmac, hashlib, requests
APP_KEY = "6h5s4qm76nrhk"
APP_SECRET = "2c2685bf956ed47b09f2ffd9b6c411e2fb0ec111"
BASE_URL = "https://open-api-sandbox.tiktokglobalshop.com"

def generate_sign(path: str, params: dict) -> str:
    """
    Generate TikTok Shop API signature.
    """
    # sort params alphabetically
    sorted_params = "".join([f"{k}{params[k]}" for k in sorted(params)])
    to_sign = path + sorted_params

    return hmac.new(
        APP_SECRET.encode("utf-8"),
        to_sign.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def get_orders():
    path = "/api/orders/search"
    timestamp = str(int(time.time() * 1000))
    params = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
    }
    params["sign"] = generate_sign(path, params)

    res = requests.get(BASE_URL + path, params=params)
    return res.json()
