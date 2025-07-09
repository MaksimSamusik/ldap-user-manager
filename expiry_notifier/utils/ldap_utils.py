import logging
import os
from ldap import MOD_REPLACE, MOD_ADD, MOD_DELETE
from expiry_notifier.ldap.ldap_connector import get_ldap_connection
from expiry_notifier.services.user_service import get_users
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def reset_all_user_info():
    conn = get_ldap_connection()
    users = get_users()

    for user in users:
        username = user.get("username", "unknown")
        first_name = user.get("first_name")
        last_name = user.get("last_name")

        if not first_name or not last_name:
            print(f"[SKIP] Missing first_name or last_name for user {username}")
            continue

        user_dn = f"CN={first_name} {last_name},CN=Users,DC=example,DC=com"
        print(f"[INFO] Attempting to clear info for: {user_dn}")

        try:
            conn.modify(user_dn, {"info": [(MOD_DELETE, [])]})
            print(f"[RESET] Deleted 'info' for {username}")
        except Exception as e:
            print(f"[ERROR] Failed to delete 'info' for {username}: {e}")

    conn.unbind()


def get_user_info(conn, user_dn, username):
    try:
        conn.search(user_dn, "(objectClass=*)", attributes=["info"])
        entry = conn.entries[0] if conn.entries else None
        return str(entry.info.value) if entry and hasattr(entry, "info") and entry.info.value else ""
    except Exception as e:
        logger.warning(f"Could not read 'info' for {username}: {e}")
        return ""


def get_user_dn(first_name, last_name):
    base_dn = os.getenv("AUTH_LDAP_BASE_DN")
    return f"CN={first_name} {last_name},CN=Users,{base_dn}"



def update_user_info(conn, user_dn, new_info, has_old_info, username):
    action = MOD_REPLACE if has_old_info else MOD_ADD
    try:
        conn.modify(user_dn, {"info": [(action, [new_info])]})
        logger.info(f"[INFO] {username} marked as '{new_info}' in LDAP")
    except Exception as e:
        logger.error(f"Failed to update 'info' for {username}: {e}")


def reset_user_info(conn, user_dn, username):
    try:
        conn.modify(user_dn, {"info": [(MOD_REPLACE, [""])]})
        logger.info(f"[RESET] Cleared 'info' for {username} due to password reset")
    except Exception as e:
        logger.error(f"Failed to clear 'info' for {username}: {e}")