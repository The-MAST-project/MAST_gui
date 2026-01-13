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
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,mast-wis-control,10.23.3.73', 
                       cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    
    # MAST apps - comment out until they exist
    'accounts',  # Make sure this is here
    'units',  # Add this
    'mast_safety',  # Changed from 'safety'
    # 'dashboard',
    # 'specs',
    # 'mast_safety',
    # 'assignments',
    # 'plans',
    'mast_utils',  # Changed from 'utils' to 'mast_utils'
    'social_django',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Add providers as needed, e.g.:
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'django.contrib.sites',
    'django_q',  # Add this for django-q2 task queue
    'MAST_gui',  # ← Django finds MastGuiConfig in MAST_gui/apps.py
]

AUTH_USER_MODEL = 'accounts.User'  # Make sure this is set to your custom user model

# There is NO 'account' app in INSTALLED_APPS.
# Only 'accounts' is present, which is correct for your custom user model.

INSTALLED_APPS += [
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.apple',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'MAST_gui.middleware.ProxyAwareLoginRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

CSRF_TRUSTED_ORIGINS = [
    "http://10.23.3.73:8000",
    # Add any other proxy/external URLs as needed
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
    'django.contrib.auth.backends.ModelBackend',  # Use Django's default
    'allauth.account.auth_backends.AuthenticationBackend',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
]

# Login URLs
LOGIN_URL = '/admin/login/'  # Use Django admin login for now
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/admin/login/'

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

# NEW (django-allauth updated settings):
SITE_ID = 1

# Authentication method: email only (no username)
ACCOUNT_LOGIN_METHODS = {'username', 'email'}

# Signup fields: email and password
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Email verification
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 'mandatory' for production
ACCOUNT_UNIQUE_EMAIL = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Print to console for development

# Allauth settings
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_ADAPTER = "accounts.adapter.CustomAccountAdapter"  # if you want to customize registration approval

# Redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'github': {
        'SCOPE': ['user', 'user:email'],
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email'],
        'FIELDS': ['email', 'name'],
    },
    'apple': {
        'APP': {
            'client_id': 'YOUR_APPLE_CLIENT_ID',
            'key': 'YOUR_APPLE_KEY',
            'team_id': 'YOUR_APPLE_TEAM_ID',
            'secret': 'YOUR_APPLE_SECRET',
        }
    }
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# MAST Configuration
MAST_SITE = config('MAST_SITE', default='wis')
MAST_CONFIG_SOURCE = config('MAST_CONFIG_SOURCE', default=None)
MAST_API_PREFIX = 'mast/api/v1'

# For python-social-auth:
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '209268696894-q7r751q0bcqu5a3jm7cb8ag9je1h6a7m.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://localhost:8010/auth/complete/google-oauth2/'

# For django-allauth:
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '209268696894-q7r751q0bcqu5a3jm7cb8ag9je1h6a7m.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
        }
    }
}

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

if no_proxy:
    # Append MAST networks to existing NO_PROXY
    no_proxy = no_proxy + ',' + ','.join(mast_networks)
else:
    no_proxy = ','.join(mast_networks)

os.environ['NO_PROXY'] = no_proxy
os.environ['no_proxy'] = no_proxy  # Some libraries check lowercase
