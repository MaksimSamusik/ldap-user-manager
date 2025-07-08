import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ldap_notify.settings')

app = Celery('ldap_notify')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
