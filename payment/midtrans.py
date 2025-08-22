import midtransclient
from django.conf import settings

snap = midtransclient.Snap(
    is_production=False,  # sandbox dulu
    server_key=settings.MIDTRANS_SERVER_KEY,
    client_key=settings.MIDTRANS_CLIENT_KEY,
)
