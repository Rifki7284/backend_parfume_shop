import jwt
import datetime
from django.conf import settings

class JWTTokenStrategy(AbstractTokenStrategy):
    def create_access_token(self, request):
        user = request.user
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # expire 1 jam
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token

    def create_access_token_payload(self, request):
        access_token = self.create_access_token(request)
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,  # detik
        }

    def create_session_token(self, request):
        """
        Kalau kamu tidak ingin pakai session token (stateful),
        bisa return None atau implementasi custom.
        """
        return None

    def get_session_token(self, request):
        return None

    def lookup_session(self, session_token: str):
        return None