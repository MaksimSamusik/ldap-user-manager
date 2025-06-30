import logging
import os
import ssl
from datetime import time
from pathlib import Path
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfUniqueNamesType
from django_auth_ldap.backend import LDAPBackend
import dotenv
from dotenv import load_dotenv


load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

LDAP_SERVER = os.getenv('LDAP_SERVER')
LDAP_PORT = int(os.getenv('LDAP_PORT'))
AUTH_LDAP_SERVER_URI = f"{LDAP_SERVER}:{LDAP_PORT}"
AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD')
AUTH_LDAP_BASE_DN = os.getenv('AUTH_LDAP_BASE_DN')
LDAP_DOMAIN = os.getenv('LDAP_DOMAIN')
AUTH_LDAP_ALWAYS_UPDATE_USER = bool(os.getenv('AUTH_LDAP_ALWAYS_UPDATE_USER'))
AUTH_LDAP_FIND_GROUP_PERMS = bool(os.getenv('AUTH_LDAP_FIND_GROUP_PERMS'))
AUTH_LDAP_GROUP_TYPE = os.getenv('AUTH_LDAP_GROUP_TYPE')
AUTH_LDAP_START_TLS = False



TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "CN=Users,DC=example,DC=com",
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
    ldap.OPT_X_TLS_NEWCTX: 0
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "CN=Groups," + AUTH_LDAP_BASE_DN,
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)",
)

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
    ldap.OPT_PROTOCOL_VERSION: 3
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # Используем форматтер
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "debug.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Логирование для всего проекта
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        # Логирование для django-auth-ldap (более детальное)
        "django_auth_ldap": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        # Логирование для вашего приложения
        "expiry_notifier": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv('DEBUG', '0') == '1')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'expiry_notifier',
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

ROOT_URLCONF = 'LDAPNotify.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'LDAPNotify.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_I18N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SMTP settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = bool(os.getenv('EMAIL_USE_TLS'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login'