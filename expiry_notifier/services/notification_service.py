import json
import logging
from datetime import datetime, timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from expiry_notifier.ldap.ldap_connector import get_ldap_connection
from expiry_notifier.services.user_service import get_users
from expiry_notifier.utils.html_utils import format_string, generate_user_table
from expiry_notifier.utils.ldap_utils import get_user_dn, get_user_info, reset_user_info, update_user_info
from expiry_notifier.utils.time_util import get_expiry_date
from ldap_notify.settings import DEFAULT_FROM_EMAIL
from expiry_notifier.services.user_service import get_admin_users
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

NOTIFICATION_DAYS = config["notification_days"]
MESSAGES = config["messages"]

STAGES = [
    (NOTIFICATION_DAYS["early"], NOTIFICATION_DAYS["middle"], "early"),
    (NOTIFICATION_DAYS["middle"], NOTIFICATION_DAYS["urgent"], "middle"),
    (NOTIFICATION_DAYS["urgent"], NOTIFICATION_DAYS["expired"], "urgent"),
    (NOTIFICATION_DAYS["expired"], float("-inf"), "expired")
]


def process_expiry():
    users = get_users()
    if not users:
        logger.warning("No users found from LDAP.")
        return []

    conn = get_ldap_connection()
    now = datetime.now(timezone.utc)
    notify_list = []

    logger.info(f"Processing {len(users)} users...")

    for user in users:
        expires_raw = user.get("account_expires_raw")
        username, email = user.get("username"), user.get("email")
        first_name, last_name = user.get("first_name"), user.get("last_name")
        user_dn = get_user_dn(first_name, last_name)

        if not (user_dn and email and expires_raw):
            logger.warning(f"[SKIP] Missing data for user {username}")
            continue

        try:
            expires = get_expiry_date(expires_raw)
        except Exception as e:
            logger.warning(f"Could not parse expiry for {username}: {e}")
            continue

        days_left = (expires - now).days
        template_context = {
            "email": email, "username": username,
            "first_name": first_name, "last_name": last_name,
            "days": days_left, "expired_days": days_left,
            "days_overdue": abs(days_left), "year": now.year,
            "date": now.date().isoformat()
        }

        info = get_user_info(conn, user_dn, username)

        if info and days_left > NOTIFICATION_DAYS["early"]:
            reset_user_info(conn, user_dn, username)
            continue

        for start, end, stage in STAGES:
            tag = f"notified_{stage}"
            if start >= days_left > end and tag not in info:
                msg_cfg = MESSAGES.get(stage, {})
                subject = format_string(msg_cfg.get("subject", ""), template_context)
                email_content = msg_cfg.get("email_content", {})
                header = format_string(email_content.get("header", ""), template_context)
                body = format_string(email_content.get("body", ""), template_context)
                footer = format_string(email_content.get("footer", ""), template_context)

                notify_list.append({
                    **user,
                    "days_left": days_left,
                    "stage": stage,
                    "subject": subject,
                    "header": header,
                    "body": body,
                    "footer": footer,
                    "expiry_date": expires.strftime('%d.%m.%Y'),
                    "sent_at": now.strftime('%d.%m.%Y %H:%M'),
                })

                new_info = f"{info};{tag}" if info else tag
                update_user_info(conn, user_dn, new_info, bool(info), username)
                break

    conn.unbind()
    logger.info(f"Finished processing. {len(notify_list)} notifications prepared.")
    return notify_list


def send_email(subject, recipients, html_content, plain_text):
    if isinstance(recipients, str):
        recipients = [recipients]

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info(f"[EMAIL SENT] To: {', '.join(recipients)}")
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed to send email to {recipients}: {e}")



def send_notification():
    logger.info("[START] Sending user notifications...")
    users_to_notify = process_expiry()
    logger.info(f"[INFO] {len(users_to_notify)} user(s) to notify")

    for user in users_to_notify:
        context = {
            "subject": user["subject"],
            "user": user,
            "message": user["body"],
            "header": user["header"],
            "footer": user["footer"],
        }

        html_body = render_to_string("emails/auto_user_notification.html", context)
        send_email(user["subject"], user["email"], html_body, user["body"])

    logger.info("[COMPLETE] Finished sending user notifications")
    send_admin_report(users_to_notify)


def send_admin_report(users: list):
    logger.info("[ADMIN REPORT] Preparing admin report...")
    now = datetime.now(timezone.utc)
    config_section = config.get("admin_auto_report", {})

    subject = format_string(config_section.get("subject", ""), {
        "date": now.date().isoformat(),
        "total_users": len(users),
    })

    email_content = config_section.get("email_content", {})
    context = {
        "subject": subject,
        "notification_date": now.strftime('%d.%m.%Y %H:%M'),
        "total_users": len(users),
        "now": now,
        "user_table": generate_user_table(users),
        "email_content": {
            "header": format_string(email_content.get("header", ""), {
                "total_users": len(users), "date": now.date().isoformat()
            }),
            "body": format_string(email_content.get("body", ""), {
                "total_users": len(users)
            }),
            "footer": format_string(email_content.get("footer", ""), {
                "date": now.date().isoformat()
            }),
        }
    }

    html = render_to_string("emails/admin_auto_report.html", context)
    to = [admin["email"] for admin in get_admin_users() if admin.get("email")]

    if not to:
        logger.warning("[ADMIN REPORT] No admin emails found in LDAP")
        return

    send_email(subject, to, html, strip_tags(html))
    logger.info(f"[ADMIN REPORT SENT] To: {', '.join(to)} | Users in report: {len(users)}")
