from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core import signing
import requests

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def Check_token(request):
    user = request.user
    return Response({
        "username": user.username,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
    })
@permission_classes([AllowAny])
class StaffLoginView(APIView):

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")

        if not all([username, password, client_id, client_secret]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # 🔹 Forward request ke /o/token/
        token_url = request.build_absolute_uri("/o/token/")
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        r = requests.post(token_url, data=payload)
        if r.status_code != 200:
            return JsonResponse(r.json(), status=r.status_code)

        token_data = r.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # 🔹 Cari user di DB
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({"error": "User tidak ditemukan"}, status=404)

        # 🔹 Hanya staff yang boleh login
        if not user.is_staff:
            return JsonResponse({"error": "Login hanya untuk staff"}, status=403)

        # 🔹 Response custom tanpa token di body
        res = JsonResponse({
            "message": "Staff login success",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            },
            "access_token":access_token,
            "refresh_token":refresh_token
        })

        # 🔹 Signed role cookie (tidak bisa diubah user)
        # signed_role = signing.dumps("staff", key="b8f9a2c1d3e4f567890abcdef1234567890abcdef1234567890abcdef12345678")

        # 🔹 Set HttpOnly cookies
        res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # ganti True di production
            samesite="Lax",
            max_age=60 * 60,  # 1 jam
        )
        res.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 hari
        )
        # res.set_cookie(
        #     key="role",
        #     value=signed_role,
        #     httponly=True,
        #     secure=False,
        #     samesite="Lax",
        #     max_age=60 * 60,
        # )

        return res