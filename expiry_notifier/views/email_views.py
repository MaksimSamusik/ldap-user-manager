import logging
from datetime import datetime
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from LDAPNotify import settings
from ..services.user_service import get_users
import json
from django.conf import settings

logger = logging.getLogger(__name__)

CONFIG_PATH = 'config.json'
with open(CONFIG_PATH) as f:
    NOTIFICATION_CONFIG = json.load(f)


@require_POST
def send_email_view(request, email):
    try:
        users = get_users()
        user_data = next((user for user in users if user['email'] == email), None)

        if not user_data:
            messages.error(request, "User not found")
            return redirect('main_page')

        try:
            expiry_date = datetime.fromisoformat(
                user_data['account_expires_raw'].replace('Z', '+00:00')
            ).date()
            today = datetime.now().date()
            expired_days = (expiry_date - today).days
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Date parsing error: {str(e)}")
            messages.error(request, "Failed to determine account expiration")
            return redirect('main_page')

        context = {
            'username': user_data.get('username', 'user'),
            'expired_days': expired_days,
            'days_overdue': abs(expired_days) if expired_days < 0 else 0,
            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
            'current_date': today.strftime('%Y-%m-%d')
        }

        config = NOTIFICATION_CONFIG['manual_notification_settings']

        if expired_days > config['early']['days']:
            notification_type = 'early'
        elif expired_days > config['middle']['days']:
            notification_type = 'middle'
        elif expired_days > config['urgent']['days']:
            notification_type = 'urgent'
        elif expired_days == config['today']['days']:
            notification_type = 'today'
        elif expired_days < 0:
            notification_type = 'expired'

        notification_config = config[notification_type]

        # Форматируем контент из JSON
        email_content = notification_config['email_content']
        formatted_content = {
            'header': email_content['header'].format(**context),
            'body': email_content['body'].format(**context),
            'footer': email_content['footer'].format(**context)
        }

        context.update({
            'subject': notification_config['subject'].format(**context),
            'urgency_level': notification_config['urgency_level'],
            'message_type': notification_config['message_type'],
            'email_content': formatted_content
        })

        html_message = render_to_string('emails/notification.html', context)
        text_message = strip_tags(html_message)

        email_msg = EmailMultiAlternatives(
            subject=context['subject'],
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_msg.attach_alternative(html_message, "text/html")
        email_msg.send(fail_silently=False)

        messages.success(request, f"Notification sent: {context['subject']}")
        logger.info(f"Email sent to {email}")

    except Exception as e:
        messages.error(request, f"Sending error: {str(e)}")
        logger.error(f"Email sending error: {str(e)}", exc_info=True)

    return redirect('main_page')
