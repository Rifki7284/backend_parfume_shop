# tiktok/binderbyte.py
import requests
from django.conf import settings

class BinderbyteError(Exception):
    pass

class BinderbyteClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.BINDERBYTE_API_KEY
        self.base_url = settings.BINDERBYTE_BASE_URL
        self.timeout = settings.BINDERBYTE_TIMEOUT

    def track(self, courier: str, awb: str):
        if not self.api_key:
            raise BinderbyteError("BINDERBYTE_API_KEY belum diset.")

        url = f"{self.base_url}/track"
        params = {"api_key": self.api_key, "courier": courier.lower(), "awb": awb.strip()}

        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise BinderbyteError(f"Gagal konek ke Binderbyte: {e}")

        try:
            data = resp.json()
        except ValueError:
            raise BinderbyteError("Response bukan JSON")

        if str(data.get("status")) != "200":
            raise BinderbyteError(data.get("message") or "Binderbyte error")

        return data
