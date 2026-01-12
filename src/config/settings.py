"""
Django settings for Metal Info Backend project.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,believably-graphitic-ann.ngrok-free.dev").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    "safedelete",
    "django_celery_beat",
    # Local apps
    "shared",
    "metal_prices",
    "metal_news",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "metal_prices_db"),
        "USER": os.getenv("POSTGRES_USER", "metal_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "metal_password"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

# CORS Configuration
# Allow all origins (useful for development, restrict in production)
CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOWED_ORIGINS = os.getenv(
#     "CORS_ALLOWED_ORIGINS",
#     "http://localhost:5173,http://localhost:3000,http://localhost:8080"
# ).split(",")

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "x-requested-with",
    "ngrok-skip-browser-warning",
]

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "fetch-metal-news-every-hour": {
        "task": "metal_news.tasks.fetch_metal_news_task",
        "schedule": 3600.0,  # Every hour (in seconds)
    },
}

# Metal Prices Configuration
METAL_PRICES_CONFIG = {
    "API_URL": os.getenv(
        "METAL_PRICES_API_URL",
        "https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/"
    ),
    "API_TIMEOUT": int(os.getenv("METAL_PRICES_API_TIMEOUT", "30")),
    "SUPPORTED_METALS": [
        "Aroma",
        "Berry",
        "Birch",
        "Candy",
        "Cliff",
        "Clove",
        "Elmo",
        "Taldon",
        "Tainttabor",
        "Tense",
        "Troma",
        "Zorba",
    ],
}

# Metal News Configuration
METAL_NEWS_CONFIG = {
    "RSS_SEARCH_TERMS": [
        "metal industry prices",
        "copper prices",
        "aluminum market",
        "steel industry news",
        "metal commodities",
    ],
    "RSS_BASE_URL": "https://news.google.com/rss/search",
    "RSS_PARAMS": {
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    },
    "FETCH_LIMIT": 50,  # Max articles per fetch
    "REQUEST_TIMEOUT": 30,  # Timeout for RSS feed requests
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "metal_prices": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "metal_news": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
