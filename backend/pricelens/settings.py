import os
from pathlib import Path
from datetime import timedelta
from decouple import Config, RepositoryEnv
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env from BASE_DIR/.env
env_file = BASE_DIR / '.env'
if env_file.exists():
    env = Config(RepositoryEnv(str(env_file)))
else:
    from decouple import config as env

SECRET_KEY = env('SECRET_KEY', default='django-insecure-pricelens-ai-secret-key-change-in-production')
DEBUG = env('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = [host.strip() for host in env('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',') if host.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    # Local Apps
    'accounts.apps.AccountsConfig',
    'catalog.apps.CatalogConfig',
    'marketplaces.apps.MarketplacesConfig',
    'reviews.apps.ReviewsConfig',
    'recommendations.apps.RecommendationsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pricelens.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pricelens.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', default='price_ai'),
        'USER': env('DB_USER', default='root'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
            'NAME': 'test_price_ai',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '300/minute',
        'auth': '30/minute',
    },
}

# SimpleJWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME_REMEMBER_ME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
]
CORS_ALLOW_CREDENTIALS = True

# Marketplace API Credentials
AMAZON_ACCESS_KEY = env('AMAZON_ACCESS_KEY', default='')
AMAZON_SECRET_KEY = env('AMAZON_SECRET_KEY', default='')
AMAZON_ASSOCIATE_TAG = env('AMAZON_ASSOCIATE_TAG', default='')
AMAZON_COUNTRY = env('AMAZON_COUNTRY', default='IN')

FLIPKART_AFFILIATE_ID = env('FLIPKART_AFFILIATE_ID', default='')
FLIPKART_AFFILIATE_TOKEN = env('FLIPKART_AFFILIATE_TOKEN', default='')

# Recommendation Engine Weights
RECOMMENDATION_WEIGHTS = {
    'price': 0.30,
    'discount': 0.15,
    'rating': 0.20,
    'sentiment': 0.20,
    'availability': 0.10,
    'seller': 0.05,
}
