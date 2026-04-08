"""
Django settings for shopmore project.
"""

import os
from pathlib import Path
from decouple import config
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

DEBUG = True


ALLOWED_HOSTS = ['*', '.onrender.com', 'shopmore.fly.dev', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com', 'https://*.fly.dev']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
     'mathfilters',
    'paymentApp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shopmore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
         'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'shopmore.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

MEDIA_URL = '/image/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'static/image')

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

FLUTTER_SECRET_KEY = config("FLUTTERWAVE_SECRET_KEY")

FLUTTERWAVE_PUBLIC_KEY = "FLWPUBK_TEST-df3d4643c70606f563a47b27e8a62872-X"
FLUTTERWAVE_SECRET_KEY = "FLWSECK_TEST-3e3c6363448c60e6e29d9bbc0a5364b0-X"
FLUTTERWAVE_ENCRYPTION_KEY = "FLWSECK_TESTba3824b8453d"

# Security settings for production
# Security settings for production
if not DEBUG:
    # SECURE_SSL_REDIRECT = True  # Commented out for Render
    # SESSION_COOKIE_SECURE = True  # Commented out for Render
    # CSRF_COOKIE_SECURE = True  # Commented out for Render
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_HSTS_SECONDS = 31536000  # Commented out for Render
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Commented out for Render
    # SECURE_HSTS_PRELOAD = True  # Commented out for Render
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Commented out for Render