"""
Django settings for MAST_gui project with HTMX.
"""
import os
import sys
from pathlib import Path
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Add MAST_common to Python path
MAST_COMMON_PATH = config('MAST_COMMON_PATH', default=str(BASE_DIR.parent / 'MAST_common'))
sys.path.insert(0, MAST_COMMON_PATH)

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,mast-wis-control,10.23.3.73',
                       cast=lambda v: [s.strip() for s in v.split(',')])
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # MAST apps
    'accounts',
    'units',
    'mast_safety',
    'mast_utils',

    # Third-party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.orcid',
    'django.contrib.sites',
    'django_q',
    'MAST_gui',
    'debug_toolbar',
]

AUTH_USER_MODEL = 'accounts.User'

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'MAST_gui.middleware.RequireLoginMiddleware',
    'MAST_gui.middleware.ProxyAwareLoginRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # Optional: Django Debug Toolbar
]

CSRF_TRUSTED_ORIGINS = [
    "http://10.23.3.73:8000",
    "https://10.23.3.73",
    "https://10.23.3.73:443",
    "http://mast-wis-control",
    "https://mast-wis-control",
    "http://mast-wis-control.weizmann.ac.il",
    "https://mast-wis-control.weizmann.ac.il",
    "http://mast-wis-control.weizmann.ac.il:8000",
    "https://mast-wis-control.weizmann.ac.il:443",
]

ROOT_URLCONF = 'MAST_gui.urls'

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
                'MAST_gui.context_processors.site_data',
                'MAST_gui.context_processors.controller_status',  # Add this line
                # 'accounts.context_processors.user_capabilities',  # Comment this out
                'MAST_gui.context_processors.mast',
            ],
        },
    },
]

WSGI_APPLICATION = 'MAST_gui.wsgi.application'
ASGI_APPLICATION = 'MAST_gui.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.RegisteredUserBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jerusalem'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# django-allauth
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_ADAPTER = 'accounts.adapter.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.CustomSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'doar.weizmann.ac.il'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'MAST <noreply@mast-wis-control.weizmann.ac.il>'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APPS': [{
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': '',
        }],
    },
    'github': {
        'SCOPE': ['user', 'user:email'],
        'APPS': [{
            'client_id': config('GITHUB_CLIENT_ID', default=''),
            'secret': config('GITHUB_CLIENT_SECRET', default=''),
        }],
    },
    'orcid': {
        'BASE_DOMAIN': 'orcid.org',
        'MEMBER_API': False,
        'APPS': [{
            'client_id': config('ORCID_CLIENT_ID', default=''),
            'secret': config('ORCID_CLIENT_SECRET', default=''),
        }],
    },
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# MAST Configuration
MAST_SITE = config('MAST_SITE', default='wis')
MAST_CONFIG_SOURCE = config('MAST_CONFIG_SOURCE', default=None)
MAST_API_PREFIX = 'mast/api/v1'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'MAST_gui.logging_handlers.DailyDirectoryHandler',
            'base_dir': '/var/log/mast',
            'filename': 'ui.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'mast': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Django-Q2 Configuration (for background tasks and scheduled polling)
Q_CLUSTER = {
    'name': 'MAST_gui',
    'workers': 2,
    'recycle': 500,
    'timeout': 60,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',  # Use Django ORM as broker (simple setup)
}

# Development server configuration
# Run with: python manage.py runserver 8010
# Default port: 8010 (to avoid conflicts with other MAST services)

# Proxy settings for internal network access
# Bypass proxy for MAST internal hosts
import os
no_proxy = os.environ.get('NO_PROXY', '')

# Add MAST internal network ranges and hosts
mast_networks = [
    'localhost',
    '127.0.0.1',
    '10.23.1.0/24',  # MAST network 1
    '10.23.2.0/24',  # MAST network 2
    '10.23.3.0/24',  # MAST network 3
    '10.23.4.0/24',  # MAST network 4
    'mast-wis-control',
    'mast-ns-control',
    '*.weizmann.ac.il',
]

INTERNAL_IPS = [
    '127.0.0.1',
    '10.23.3.73',  # Add your client IP
]

if no_proxy:
    # Append MAST networks to existing NO_PROXY
    no_proxy = no_proxy + ',' + ','.join(mast_networks)
else:
    no_proxy = ','.join(mast_networks)

os.environ['NO_PROXY'] = no_proxy
os.environ['no_proxy'] = no_proxy  # Some libraries check lowercase
