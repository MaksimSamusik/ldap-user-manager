import json
import logging
import traceback
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from LDAPNotify import settings
from expiry_notifier.services.user_service import get_admin_users, get_users
from ..utils.time_util import format_iso_time

logger = logging.getLogger(__name__)


def notify_admins():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        threshold_days = config.get("admin_notification_threshold")
        email_subject = config['admin_notification_settings']['email_subject']
        alert_message = config['admin_notification_settings']['alert_message']
        users = get_users()
        now = datetime.now()
        expiring_users = []

        for user in users:
            try:
                user['account_expires_raw'] = format_iso_time(user['account_expires_raw'])
                expiry_date = datetime.strptime(user['account_expires_raw'], '%d.%m.%Y %H:%M')
                expiry_days = (expiry_date - now).days

                if expiry_days <= threshold_days:
                    expiring_users.append({
                        'username': user.get('username', 'Неизвестно'),
                        'email': user['email'],
                        'expiry_date': expiry_date.strftime('%d.%m.%Y'),
                        'days_remaining': expiry_days
                    })

            except Exception as e:
                logger.error(f"Ошибка обработки пользователя {user.get('email')}: {str(e)}")
                continue

        if not expiring_users:
            logger.info(f"Нет пользователей с истечением срока в ближайшие {threshold_days} дней")
            return

        admin_users = get_admin_users()
        recipient_list = [admin['email'] for admin in admin_users if admin.get('email')]

        if not recipient_list:
            logger.error("Не найдено email администраторов для отправки")
            return

        context = {
            'threshold_days': threshold_days,
            'notification_date': now.strftime('%d.%m.%Y %H:%M'),
            'expiring_users': expiring_users,
            'total_users': len(expiring_users),
            'alert_message': alert_message,
        }

        html_message = render_to_string('emails/expired_accounts_notification.html', context)
        text_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject=email_subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        logger.info(f"Отправлено уведомление {len(recipient_list)} админам о {len(expiring_users)} пользователях")

    except Exception as e:
        logger.error(f"Ошибка в функции notify_admins: {str(e)}")
        traceback.print_exc()


