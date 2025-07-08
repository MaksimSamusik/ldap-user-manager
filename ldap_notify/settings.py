import os
from pathlib import Path
import ldap
from celery.schedules import crontab
from django_auth_ldap.config import LDAPSearch
from dotenv import load_dotenv

load_dotenv()

#Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

#Секретный ключ Django (нельзя публиковать)
SECRET_KEY = os.getenv("SECRET_KEY")

#Настройки LDAP-сервера
LDAP_SERVER = os.getenv('LDAP_SERVER')  # URI LDAP-сервера (например, ldaps://ldap.example.com)
LDAP_PORT = int(os.getenv('LDAP_PORT'))  # Порт подключения (обычно 636 или 389)
AUTH_LDAP_SERVER_URI = f"{LDAP_SERVER}:{LDAP_PORT}"  # Полный URI с портом
AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN')  # DN для подключения к LDAP (например, EXAMPLE\\admin)
AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD')  # Пароль от LDAP
AUTH_LDAP_BASE_DN = os.getenv('AUTH_LDAP_BASE_DN')  # Базовый DN, откуда начинается поиск
LDAP_DOMAIN = os.getenv('LDAP_DOMAIN')  # Домен для авторизации (например, example.com)
AUTH_LDAP_ALWAYS_UPDATE_USER = bool(os.getenv('AUTH_LDAP_ALWAYS_UPDATE_USER'))  # Обновлять данные пользователя при каждом входе
AUTH_LDAP_FIND_GROUP_PERMS = bool(os.getenv('AUTH_LDAP_FIND_GROUP_PERMS'))  # Использовать группы LDAP для прав
AUTH_LDAP_GROUP_TYPE = os.getenv('AUTH_LDAP_GROUP_TYPE')  # Тип групп (если указан)
AUTH_LDAP_START_TLS = False  # Отключено TLS (используется LDAPS напрямую)

#Временная зона и поддержка времени
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

#Шаблон поиска пользователей LDAP
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "CN=Users,DC=example,DC=com",  # DN для поиска пользователей
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"  # Фильтр поиска по логину
)

#Отображение атрибутов LDAP -> Django
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

#Глобальные опции для LDAP
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,  # Не проверять сертификаты
    ldap.OPT_X_TLS_NEWCTX: 0
}

#Поиск LDAP-групп
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "CN=Groups," + AUTH_LDAP_BASE_DN,
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)",
)

#Настройки подключения LDAP
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
    ldap.OPT_PROTOCOL_VERSION: 3  # Используем LDAPv3
}

#Бэкенды аутентификации Django
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",  # LDAP аутентификация
    "django.contrib.auth.backends.ModelBackend",  # Стандартная Django аутентификация
]

#Настройка логгирования
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
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "debug.log",  # Файл логов
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django_auth_ldap": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "expiry_notifier": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

#Отладка (вкл/выкл)
DEBUG = bool(os.getenv('DEBUG', '0') == '1')

#Разрешённые хосты (через запятую)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

#Установленные Django-приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'expiry_notifier',  # Приложение уведомлений
    'corsheaders',  # Поддержка CORS
]

#Middleware
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

#URL-конфигурация
ROOT_URLCONF = 'ldap_notify.urls'

#Шаблоны HTML
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Папка с шаблонами
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

#Доверенные домены для CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://8000-cs-97c11569-caa6-4535-8dbb-78634e625b10.cs-europe-west4-pear.cloudshell.dev",
]

#WSGI-приложение
WSGI_APPLICATION = 'ldap_notify.wsgi.application'

#База данных (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # SQLite как база
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # Файл базы данных
    }
}

#Валидаторы пароля
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

#Интернационализация
LANGUAGE_CODE = 'en-us'
USE_I18N = True

#Статика
STATIC_URL = 'static/'

#Тип ключа по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#SMTP — отправка писем
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST')  # SMTP сервер
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))  # Порт SMTP (обычно 587)
EMAIL_USE_TLS = bool(os.getenv('EMAIL_USE_TLS'))  # TLS включён?
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Логин SMTP
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # Пароль SMTP
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # Отправитель по умолчанию

#Редиректы после входа
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login'

#Разрешённые источники CORS
CORS_ALLOWED_ORIGINS = [
    "https://8000-cs-97c11569-caa6-4535-8dbb-78634e625b10.cs-europe-west4-pear.cloudshell.dev",
]
CORS_ALLOW_CREDENTIALS = True

#Celery — очередь задач
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')  # Брокер
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')  # Бэкенд для хранения результатов

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 минут лимит на задачу

#Расписание задач
CELERY_BEAT_SCHEDULE = {
    'send-daily-notification': {
        'task': 'expiry_notifier.tasks.send_daily_notification',
        'schedule': crontab(hour=11, minute=30),  # Каждый день в 11:30
    },
}
