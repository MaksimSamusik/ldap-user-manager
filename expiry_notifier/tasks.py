import logging
from celery import shared_task

from expiry_notifier.services.notification_service import send_notification

logger = logging.getLogger(__name__)


@shared_task
def send_daily_notification():
    send_notification()