import json
from .ldap_service import ldap_users

def get_admin_users():
    response = ldap_users()
    admin_users_json = json.loads(response.content)
    return admin_users_json.get('admin_users', [])

def get_users():
    response = ldap_users()
    users_json = json.loads(response.content)
    return users_json.get('users', [])

def get_expired_users():
    users = get_users()
    return [user for user in users if user.get('expired')]
