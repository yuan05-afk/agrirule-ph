import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Secure by default: DEBUG is only on when DJANGO_DEBUG=1 is set explicitly (see .env.example).
DEBUG = os.getenv('DJANGO_DEBUG', '0') == '1'

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is not 1.')
    SECRET_KEY = 'insecure-local-development-key'
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,.vercel.app').split(',')
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:8000,http://localhost:8000',
    ).split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'expert_system',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.PerformanceMetricsMiddleware',
    'core.middleware.DatabaseUnavailableMiddleware',
]

ROOT_URLCONF = 'agriruleph_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agriruleph_project.wsgi.application'
ASGI_APPLICATION = 'agriruleph_project.asgi.application'

IS_COLLECTSTATIC = len(sys.argv) > 1 and sys.argv[1] == 'collectstatic'
DATABASE_URL = os.getenv('DATABASE_URL', '').strip().strip('"').strip("'")

# Seconds to wait for the database before failing. A short timeout turns a dead or paused
# database into a fast 503 (see core.middleware.DatabaseUnavailableMiddleware) instead of a
# serverless function that hangs for ~16 s and then returns a bare 500.
DB_CONNECT_TIMEOUT = int(os.getenv('DB_CONNECT_TIMEOUT', '5'))

if IS_COLLECTSTATIC or (not DATABASE_URL and DEBUG):
    # collectstatic needs no real database, and local development falls back to SQLite.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is required.')
    if not urlsplit(DATABASE_URL).scheme:
        raise RuntimeError(
            "DATABASE_URL is malformed. It must start with a scheme like "
            "'postgresql://' or 'postgres://'."
        )

    DB_CONN_MAX_AGE = int(os.getenv('DB_CONN_MAX_AGE', '0' if DEBUG else '60'))
    try:
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=DB_CONN_MAX_AGE,
                conn_health_checks=True,
                ssl_require=not DEBUG,
            )
        }
    except dj_database_url.UnknownSchemeError as exc:
        raise RuntimeError(
            "DATABASE_URL uses an unsupported scheme. Use a standard database URL "
            "such as 'postgresql://user:password@host:port/dbname'."
        ) from exc
    DATABASES['default'].setdefault('OPTIONS', {})['connect_timeout'] = DB_CONNECT_TIMEOUT
    # Pooled (transaction-mode) endpoints such as Neon's -pooler host cannot use server-side cursors.
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
# Fallback for serverless packaging issues: allow WhiteNoise to serve files
# discovered via STATICFILES_DIRS even if STATIC_ROOT artifacts are missing.
WHITENOISE_USE_FINDERS = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'agriruleph-cache',
        'TIMEOUT': 300,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'perf.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.health': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
