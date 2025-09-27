from rest_framework_simplejwt.tokens import AccessToken

class CustomAccessToken(AccessToken):
    @property
    def payload(self):
        data = super().payload
        user = self.user
        data["is_staff"] = user.is_staff
        return data
