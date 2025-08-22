
class OAuth2TokenFromCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.COOKIES.get("access_token")
        if token:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
            print("✅ Token injected:", token)
        else:
            print("⚠️ No access_token found in cookies")

        return self.get_response(request)