import json
import logging
import os
from datetime import datetime, timezone
from dateutil.parser import isoparse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from ldap import MOD_REPLACE, MOD_ADD
from expiry_notifier.ldap.ldap_connector import get_ldap_connection
from expiry_notifier.services.user_service import get_users
from expiry_notifier.utils.format_utils import format_string
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


def process_expiry() -> list:
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
        username = user.get("username")
        email = user.get("email")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        user_dn = f"CN={first_name} {last_name},CN=Users,{os.getenv("AUTH_LDAP_BASE_DN")}"

        if not user_dn or not email or not expires_raw:
            logger.warning(f"[SKIP] Missing data for user {username}")
            continue

        try:
            if isinstance(expires_raw, str):
                expires = isoparse(expires_raw)
            elif isinstance(expires_raw, datetime):
                expires = expires_raw
            elif isinstance(expires_raw, (int, float)):
                seconds = expires_raw / 10_000_000 - 11644473600
                expires = datetime.fromtimestamp(seconds, tz=timezone.utc)
            else:
                logger.warning(f"Unsupported expiry format for {username}: {expires_raw}")
                continue
        except Exception as e:
            logger.warning(f"Could not parse expiry for {username}: {e}")
            continue

        days_left = (expires - now).days

        template_context = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "days": days_left,
            "expired_days": days_left,
            "days_overdue": abs(days_left),
            "year": now.year,
            "date": now.date().isoformat()
        }

        try:
            conn.search(user_dn, "(objectClass=*)", attributes=["info"])
            entry = conn.entries[0] if conn.entries else None
            info = str(entry.info.value) if entry and hasattr(entry, "info") and entry.info.value else ""
        except Exception as e:
            logger.warning(f"Could not read 'info' for {username}: {e}")
            info = ""

        if info and days_left > NOTIFICATION_DAYS["early"]:
            try:
                conn.modify(user_dn, {"info": [(MOD_REPLACE, [""])]})
                logger.info(f"[RESET] Cleared 'info' for {username} due to password reset")
            except Exception as e:
                logger.error(f"Failed to clear 'info' for {username}: {e}")
            continue

        for start, end, stage in STAGES:
            tag = f"notified_{stage}"
            if start >= days_left > end and tag not in info:
                message_cfg = MESSAGES.get(stage, {})
                subject = format_string(message_cfg.get("subject", ""), template_context)
                email_content = message_cfg.get("email_content", {})

                header = format_string(email_content.get("header", ""), template_context)
                body = format_string(email_content.get("body", ""), template_context)
                footer = format_string(email_content.get("footer", ""), template_context)

                full_user_data = {
                    **user,
                    "days_left": days_left,
                    "stage": stage,
                    "subject": subject,
                    "header": header,
                    "body": body,
                    "footer": footer,
                    "expiry_date": expires.strftime('%d.%m.%Y'),
                    "sent_at": now.strftime('%d.%m.%Y %H:%M'),
                }
                notify_list.append(full_user_data)

                updated_info = f"{info};{tag}" if info else tag
                mod_action = MOD_REPLACE if info else MOD_ADD
                try:
                    conn.modify(user_dn, {"info": [(mod_action, [updated_info])]})
                    logger.info(f"[INFO] {username} marked as '{tag}' in LDAP")
                except Exception as e:
                    logger.error(f"Failed to update 'info' for {username}: {e}")
                break

    conn.unbind()
    logger.info(f"Finished processing. {len(notify_list)} notifications prepared.")
    return notify_list


def send_notification():
    logger.info("[START] Sending user notifications...")

    users_to_notify = process_expiry()
    logger.info(f"[INFO] {len(users_to_notify)} user(s) to notify")

    for user in users_to_notify:
        subject = user["subject"]
        recipient = user["email"]
        context = {
            "subject": subject,
            "user": user,
            "message": user.get("body", ""),
            "header": user.get("header", ""),
            "footer": user.get("footer", ""),
        }

        try:
            html_body = render_to_string("emails/auto_user_notification.html", context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=user["body"],
                from_email=DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            email.attach_alternative(html_body, "text/html")
            email.send()

            logger.info(f"[EMAIL SENT] To: {recipient} | Stage: {user['stage']} | Days Left: {user['days_left']}")
        except Exception as e:
            logger.error(f"[EMAIL ERROR] Failed to send email to {recipient}: {e}")

    logger.info("[COMPLETE] Finished sending user notifications")

    send_admin_report(users_to_notify)


def generate_user_table(users: list) -> str:
    logger.info(f"[TABLE] Generating admin report table for {len(users)} user(s)")

    if not users:
        return "<p>No users were notified.</p>"

    rows = []
    for idx, user in enumerate(users, 1):
        rows.append(f"""
            <tr>
                <td>{idx}</td>
                <td>{user.get('username', '')}</td>
                <td>{user.get('email', '')}</td>
                <td>{user.get('days_left', '')}</td>
                <td>{user.get('stage', '')}</td>
                <td>{user.get('expiry_date', '')}</td>
                <td>{user.get('sent_at', '')}</td>
            </tr>
        """)

    logger.info(f"[TABLE DONE] Generated table with {len(rows)} rows")
    return f"""
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Username</th>
                <th>Email</th>
                <th>Days Left</th>
                <th>Stage</th>
                <th>Expiry Date</th>
                <th>Sent At</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def send_admin_report(notified_users: list):
    logger.info("[ADMIN REPORT] Preparing admin report...")
    now = datetime.now(timezone.utc)
    admin_config = config.get("admin_auto_report", {})

    subject = format_string(admin_config.get("subject", ""), {
        "date": now.date().isoformat(),
        "total_users": len(notified_users),
    })

    email_content = admin_config.get("email_content", {})
    context = {
        "subject": subject,
        "notification_date": now.strftime('%d.%m.%Y %H:%M'),
        "total_users": len(notified_users),
        "now": now,
        "user_table": generate_user_table(notified_users),
        "email_content": {
            "header": format_string(email_content.get("header", ""), {
                "total_users": len(notified_users),
                "date": now.date().isoformat()
            }),
            "body": format_string(email_content.get("body", ""), {
                "total_users": len(notified_users)
            }),
            "footer": format_string(email_content.get("footer", ""), {
                "date": now.date().isoformat()
            }),
        }
    }

    html = render_to_string("emails/admin_auto_report.html", context)
    admins = get_admin_users()
    to = [admin["email"] for admin in admins if admin.get("email")]

    if not to:
        logger.warning("[ADMIN REPORT] No admin emails found in LDAP")
        return

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html),
            from_email=DEFAULT_FROM_EMAIL,
            to=to,
        )
        email.attach_alternative(html, "text/html")
        email.send()
        logger.info(f"[ADMIN REPORT SENT] To: {', '.join(to)} | Users in report: {len(notified_users)}")
    except Exception as e:
        logger.error(f"[ADMIN REPORT ERROR] Failed to send admin report: {e}")
