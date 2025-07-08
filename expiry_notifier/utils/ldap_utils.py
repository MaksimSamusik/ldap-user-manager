from ldap import MOD_DELETE
from expiry_notifier.ldap.ldap_connector import get_ldap_connection
from expiry_notifier.services.user_service import get_users


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