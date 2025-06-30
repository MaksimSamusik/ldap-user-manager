import logging
from datetime import datetime, timezone
from django.http import JsonResponse
from expiry_notifier.ldap.ldap_connector import get_ldap_connection
from django.conf import settings

logger = logging.getLogger(__name__)


def ldap_users() -> JsonResponse | None:
    try:
        conn = get_ldap_connection()
        search_base = settings.AUTH_LDAP_BASE_DN

        user_filter = (
            '(&'
            '(objectClass=user)'
            '(!(userAccountControl:1.2.840.113556.1.4.803:=2))'
            '(!(memberOf=CN=Domain Admins,CN=Users,DC=example,DC=com))'
            ')'
        )

        admin_filter = (
            '(&'
            '(objectCategory=person)'
            '(objectClass=user)'
            '(memberOf=CN=Domain Admins,CN=Users,DC=example,DC=com)'
            ')'
        )

        attributes = [
            'cn',
            'mail',
            'accountExpires',
            'userAccountControl',
            'displayName',
            'sAMAccountName',
            'givenName',
            'sn',
            'memberOf'
        ]

        conn.search(search_base, user_filter, attributes=attributes)
        user_entries = conn.entries.copy()

        conn.search(search_base, admin_filter, attributes=attributes)
        admin_entries = conn.entries.copy()

        users = []
        admin_users = []
        current_time = datetime.now(timezone.utc)

        def process_entry(entry, is_admin=False):
            try:
                user_data = {
                    'name': getattr(entry, 'cn', [''])[0],
                    'email': getattr(entry, 'mail', [''])[0],
                    'username': getattr(entry, 'sAMAccountName', [''])[0],
                    'first_name': getattr(entry, 'givenName', [''])[0],
                    'last_name': getattr(entry, 'sn', [''])[0],
                    'expired': False,
                    'disabled': False,
                    'is_admin': is_admin,
                    'account_expires_raw': None
                }

                if hasattr(entry, 'accountExpires'):
                    expiry_value = entry.accountExpires.value
                    user_data['account_expires_raw'] = expiry_value

                    if expiry_value not in (None, 0, 9223372036854775807):
                        try:
                            if isinstance(expiry_value, datetime):
                                expiry_dt = expiry_value
                            elif isinstance(expiry_value, str):
                                expiry_dt = datetime.fromisoformat(expiry_value.replace('Z', '+00:00'))
                            else:
                                expiry_value = int(expiry_value)
                                if expiry_value > 0:
                                    seconds_since_1601 = expiry_value / 10_000_000
                                    unix_timestamp = seconds_since_1601 - 11644473600
                                    expiry_dt = datetime.fromtimestamp(unix_timestamp, timezone.utc)
                                else:
                                    expiry_dt = None

                            if expiry_dt:
                                user_data['expired'] = expiry_dt <= current_time

                        except (ValueError, TypeError, AttributeError) as e:
                            logger.warning(f"Failed to parse accountExpires for {user_data['username']}: {str(e)}")

                if hasattr(entry, 'userAccountControl'):
                    uac_value = entry.userAccountControl.value
                    if uac_value is not None:
                        try:
                            uac = int(uac_value)
                            user_data['disabled'] = bool(uac & 0x0002)
                        except (ValueError, TypeError):
                            pass
                    return user_data

            except Exception as e:
                logger.error(f"Error processing user {getattr(entry, 'cn', 'unknown')}: {str(e)}")
                return None

        for entry in user_entries:
            user_data = process_entry(entry, is_admin=False)
            if user_data:
                users.append(user_data)

        for entry in admin_entries:
            admin_data = process_entry(entry, is_admin=True)
            if admin_data:
                admin_users.append(admin_data)

        return JsonResponse({
            'status': 'success',
            'users': users,
            'admin_users': admin_users,
            'user_count': len(users),
            'admin_count': len(admin_users),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"LDAP operation failed: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'LDAP server operation failed',
            'details': str(e)
        }, status=500)
