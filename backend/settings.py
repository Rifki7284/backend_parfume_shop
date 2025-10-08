from pathlib import Path
import os

from pathlib import Path
import environ
TIME_ZONE = 'Asia/Jakarta'
USE_TZ = True
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")
PARTNER_ID = env("PARTNER_ID", default="").strip()
PARTNER_KEY = env("PARTNER_KEY", default="").strip()
SHOP_ID = env("SHOP_ID", default="").strip()
# akses variabel
TIKTOK_APP_KEY = env("TIKTOK_APP_KEY", default="").strip()
TIKTOK_APP_SECRET = env("TIKTOK_APP_SECRET", default="").strip()
TIKTOK_REDIRECT_URI = env("TIKTOK_REDIRECT_URI", default="").strip()


BINDERBYTE_API_KEY = env("BINDERBYTE_API_KEY", default="").strip()
BINDERBYTE_BASE_URL = "https://api.binderbyte.com/v1"
BINDERBYTE_TIMEOUT = 12


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-fallback")
DEBUG = True
ALLOWED_HOSTS = []

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
    "oauth2_provider.backends.OAuth2Backend",  # untuk OAuth2
    "django.contrib.auth.backends.ModelBackend",
)
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 3600,
    "REFRESH_TOKEN_EXPIRE_SECONDS": 86400,
}
# Installed Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # cron
    "django_q",
    # apps kamu
    "users",
    "store",
    "tiktok",
    "shopee",

    # third-party
    "oauth2_provider",
    "django_extensions",
    "corsheaders",
    "channels",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
]
# AUTH_USER_MODEL = "user_account.CustomUser"
# ACCOUNT_ADAPTER = "users.adapter.AutoLoginSocialAccountAdapter"
Q_CLUSTER = {
    "name": "DjangoQ",
    "workers": 2,
    "timeout": 90,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "store.utils.pagination.CustomPagination",
    "PAGE_SIZE": 10,  # default 10 item per halaman
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}
# Supaya dj-rest-auth tidak maksa pakai token bawaan
REST_AUTH_TOKEN_MODEL = None

# Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "backend.middleware.OAuth2TokenFromCookieMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:5500"]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "e-commerce",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "3306",
    }
}

# Channel Layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
