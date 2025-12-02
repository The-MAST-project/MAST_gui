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
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,mast-wis-control', 
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
    # 'accounts',
    # 'dashboard',
    # 'units',
    # 'specs',
    # 'mast_safety',
    # 'assignments',
    # 'plans',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Comment out allauth middleware until we need it
    # 'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
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
                'django.contrib.auth.context_processors.auth',  # Make sure this is here
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.site_context',
                'MAST_gui.context_processors.site_data',  # Add this line
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
    'django.contrib.auth.backends.ModelBackend',
    # Comment out allauth backend until we need it
    # 'allauth.account.auth_backends.AuthenticationBackend',
]

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
ACCOUNT_LOGIN_METHODS = {'email'}

# Signup fields: email and password
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Email verification
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 'mandatory' for production
ACCOUNT_UNIQUE_EMAIL = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Print to console for development

# Redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

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
    },
}

# Development server configuration
# Run with: python manage.py runserver 8010
# Default port: 8010 (to avoid conflicts with other MAST services)
