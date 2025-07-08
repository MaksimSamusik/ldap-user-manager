import logging
from django.apps import AppConfig


logger = logging.getLogger(__name__)

class ExpiryNotifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expiry_notifier'
