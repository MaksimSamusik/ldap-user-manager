import json
import logging
import smtplib
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from django.core import mail
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from LDAPNotify import settings
from expiry_notifier.services.user_service import get_users, get_admin_users
from expiry_notifier.utils.time_util import format_iso_time
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

notification_sent: Dict[str, List[int]] = {}


class NotificationManager:
    def __init__(self):
        self.now = datetime.now()
        self.config = self._load_config()
        self.days_config = self.config["notification_days"]
        self.messages_config = self.config["messages"]
        self.admin_config = self.config.get('admin_notifications', {}).get('report_email', {})

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        try:
            with open('config.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.critical(f"Failed to load config file: {str(e)}")
            raise

    def send_notifications(self) -> List[Tuple[str, int]]:
        users = get_users()
        admin_users = get_admin_users()
        admin_emails = [admin['email'] for admin in admin_users if 'email' in admin]

        logger.info(f"Starting notification processing. Total users: {len(users)}")
        logger.info(f"Found admin emails for reporting: {len(admin_emails)}")

        emails_to_send = []
        notification_report = []

        for user in users:
            try:
                email = user.get('email')
                if not email:
                    continue

                processed_user = self._process_user(user)
                if processed_user:
                    emails_to_send.append(processed_user[0])
                    notification_report.append(processed_user[1])
            except Exception as e:
                logger.error(f"Error processing user {email}: {str(e)}", exc_info=True)

        if emails_to_send:
            self._send_mass_messages(emails_to_send)

        if notification_report and admin_emails:
            self._send_admin_report(notification_report, admin_emails)
        else:
            logger.warning("No admins available for report sending")

        logger.info(f"Processing complete. Notifications sent for {len(notification_report)} users")
        return [(item['email'], item['expiry_days']) for item in notification_report]

    def _process_user(self, user: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        email = user['email']
        user['account_expires_raw'] = format_iso_time(user['account_expires_raw'])

        try:
            expiry_date = datetime.strptime(user['account_expires_raw'], '%d.%m.%Y %H:%M')
        except ValueError:
            logger.error(f"Invalid date format for user {email}")
            return None

        expiry_days = (expiry_date - self.now).days
        notification_type = self._determine_notification_type(email, expiry_days)

        if not notification_type:
            return None

        message_template = self.messages_config[notification_type]
        subject = message_template["subject"].format(days=expiry_days)
        body = message_template["body"].format(email=email, days=expiry_days)

        logger.info(self._create_log_message(email, expiry_days, notification_type))

        if email not in notification_sent:
            notification_sent[email] = []
        notification_sent[email].append(self.days_config.get(notification_type, 0))

        email_data = {
            'email': email,
            'subject': subject,
            'body': body,
            'user': user,
            'notification_type': notification_type
        }

        report_data = {
            'username': user.get('username', 'N/A'),
            'email': email,
            'expiry_days': expiry_days,
            'notification_type': notification_type,
            'sent_at': self.now.strftime('%Y-%m-%d %H:%M'),
            'account_status': 'Active' if expiry_days > 0 else 'Expired'
        }

        return email_data, report_data

    def _determine_notification_type(self, email: str, expiry_days: int) -> Optional[str]:
        if self.days_config["early"] > expiry_days >= self.days_config["middle"] and \
                self.days_config["early"] not in notification_sent.get(email, []):
            return "early"
        elif self.days_config["urgent"] < expiry_days <= self.days_config["middle"] and \
                self.days_config["middle"] not in notification_sent.get(email, []):
            return "middle"
        elif 0 < expiry_days <= self.days_config["urgent"] and \
                self.days_config["urgent"] not in notification_sent.get(email, []):
            return "urgent"
        elif expiry_days <= self.days_config["expired"]:
            return "expired"
        return None

    def _create_log_message(self, email: str, expiry_days: int, notification_type: str) -> str:
        messages = {
            "early": f"User {email} (expires in {expiry_days} days): Early notification (30 days)",
            "middle": f"User {email} (expires in {expiry_days} days): Middle notification (14 days)",
            "urgent": f"User {email} (expires in {expiry_days} days): Urgent notification (7 days)",
            "expired": f"User {email} (expires in {expiry_days} days): Account expired!"
        }
        return messages.get(notification_type, "")

    def _send_admin_report(self, report_data: List[Dict[str, Any]], admin_emails: List[str]) -> None:
        if not admin_emails:
            logger.warning("No admin emails available for report")
            return

        context = self._prepare_report_context(report_data)

        try:
            html_content = render_to_string('emails/admin_report.html', context)
            email_subject = self.admin_config.get('subject', 'Notification report for {date}').format(
                date=self.now.strftime('%d.%m.%Y')
            )

            email = EmailMessage(
                subject=email_subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails,
            )
            email.content_subtype = "html"
            email.send()

            logger.info(f"HTML report successfully sent to {len(admin_emails)} admins")
        except Exception as e:
            logger.error(f"Error sending HTML report: {str(e)}", exc_info=True)

    def _prepare_report_context(self, report_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'report_title': "📊 Notification Report",
            'report_date': self.now.strftime('%Y-%m-%d %H:%M'),
            'summary_title': self.admin_config.get('summary_title', '📌 Summary'),
            'total_notifications': len(report_data),
            'total_notifications_text': self.admin_config.get('total_notifications', 'Total notifications sent:'),
            'unique_users': len({r['email'] for r in report_data}),
            'unique_users_text': self.admin_config.get('unique_users', 'Unique users:'),
            'expired_count': len([r for r in report_data if r['notification_type'] == 'expired']),
            'expired_text': self.admin_config.get('expired_accounts', 'Expired accounts:'),
            'urgent_count': len([r for r in report_data if r['notification_type'] == 'urgent']),
            'urgent_text': self.admin_config.get('urgent_notifications', 'Urgent notifications:'),
            'current_year': self.now.year,
            'footer_text': self.admin_config.get('footer_text', 'This is an automatically generated report.'),
            'copyright_text': self.admin_config.get('copyright', '© {year} Your Company.').format(year=self.now.year),
            'report_items': self._prepare_report_items(report_data)
        }

    def _prepare_report_items(self, report_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{
            'username': item['username'],
            'email': item['email'],
            'formatted_days': self._format_days(item['expiry_days']),
            'formatted_type': self._format_notification_type(item['notification_type']),
            'account_status': item['account_status'],
            'sent_at': item['sent_at'],
            'row_class': self._get_row_class(item['notification_type'])
        } for item in sorted(report_data, key=lambda x: (x['notification_type'], x['expiry_days']))]

    @staticmethod
    def _send_mass_messages(messages_data: List[Dict[str, Any]]) -> None:
        connection = None
        try:
            connection = mail.get_connection()
            connection.open()

            email_messages = []
            for data in messages_data:
                try:
                    context = {
                        'user': data['user'],
                        'message': data['body'],
                        'subject': data['subject']
                    }

                    html_message = render_to_string('emails/auto_notification.html', context)
                    text_message = strip_tags(html_message)

                    email = EmailMultiAlternatives(
                        subject=data['subject'],
                        body=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[data['email']],
                        connection=connection
                    )
                    email.attach_alternative(html_message, "text/html")
                    email_messages.append(email)

                    logger.debug(f"Prepared email: {data['subject']} for {data['email']}")
                except Exception as e:
                    logger.error(f"Error preparing email for {data['email']}: {str(e)}")
                    continue

            if email_messages:
                connection.send_messages(email_messages)
                logger.info(f"Successfully sent {len(email_messages)} emails")

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error during bulk sending: {str(e)}")
        except Exception as e:
            logger.error(f"Critical error during bulk sending: {traceback.format_exc()}")
        finally:
            if connection:
                connection.close()

    @staticmethod
    def _get_row_class(notification_type: str) -> str:
        return {
            'expired': 'expired',
            'urgent': 'urgent'
        }.get(notification_type, '')

    @staticmethod
    def _format_days(days: int) -> str:
        return f"{abs(days)} days ago" if days < 0 else str(days)

    @staticmethod
    def _format_notification_type(ntype: str) -> str:
        types = {
            'early': '🟢 Early',
            'middle': '🟡 Middle',
            'urgent': '🔴 Urgent',
            'expired': '⏳ Expired',
        }
        return types.get(ntype, ntype)


def send_notification():
    try:
        manager = NotificationManager()
        return manager.send_notifications()
    except Exception as e:
        logger.critical(f"Critical error in send_notification: {str(e)}", exc_info=True)
        return []