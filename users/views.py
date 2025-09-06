from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from oauth2_provider.views import TokenView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from oauth2_provider.decorators import protected_resource
from django.http import JsonResponse
from oauth2_provider.decorators import protected_resource
from oauth2_provider.models import AccessToken
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from oauth2_provider.views import TokenView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from oauth2_provider.models import AccessToken
from datetime import datetime
import json
from oauth2_provider.models import AccessToken
@protected_resource()
def account_me(request):
    user = request.resource_owner
    return JsonResponse({"username": user.username})


@permission_classes([AllowAny])
class CustomLoginView(TokenView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Panggil method TokenView post (token exchange)
        response = super().post(request, *args, **kwargs)

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid response from token endpoint"}, status=500
            )

        if response.status_code == 200:
            access_token_str = data.get("access_token")
            refresh_token = data.get("refresh_token")

            try:
                token = AccessToken.objects.select_related("user").get(
                    token=access_token_str,
                    expires__gt=datetime.now(),
                )
                user = token.user

                # ✅ Cek apakah user aktif
                if not user.is_active:
                    return JsonResponse(
                        {"error": "Akun ini tidak aktif, silakan hubungi admin."},
                        status=403
                    )

                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }

            except AccessToken.DoesNotExist:
                return JsonResponse({"error": "Invalid access token"}, status=401)

            # Buat response dengan set-cookie dan data user
            res = JsonResponse(
                {
                    "message": "Login success",
                    "user": user_data,
                }
            )
            res.set_cookie(
                "access_token",
                access_token_str,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            res.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            return res

        return JsonResponse(data, status=response.status_code)
@permission_classes([AllowAny])
class StaffLoginView(TokenView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Panggil method TokenView post (token exchange)
        response = super().post(request, *args, **kwargs)

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid response from token endpoint"}, status=500
            )

        if response.status_code == 200:
            access_token_str = data.get("access_token")
            refresh_token = data.get("refresh_token")

            try:
                token = AccessToken.objects.select_related("user").get(
                    token=access_token_str,
                    expires__gt=datetime.now(),
                )
                user = token.user

                # ✅ Cek apakah user staff
                if not user.is_staff:
                    return JsonResponse(
                        {"error": "Login hanya diperbolehkan untuk staff."},
                        status=403
                    )

                # ✅ Cek juga apakah user aktif
                if not user.is_active:
                    return JsonResponse(
                        {"error": "Akun ini tidak aktif, silakan hubungi admin."},
                        status=403
                    )

                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_staff": user.is_staff,
                }

            except AccessToken.DoesNotExist:
                return JsonResponse({"error": "Invalid access token"}, status=401)

            # Buat response dengan set-cookie dan data user
            res = JsonResponse(
                {
                    "message": "Login success (staff only)",
                    "user": user_data,
                }
            )
            res.set_cookie(
                "access_token",
                access_token_str,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            res.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            return res

        return JsonResponse(data, status=response.status_code)
