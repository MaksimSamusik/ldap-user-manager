from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from expiry_notifier.services.user_service import get_users
from ..utils.time_util import format_iso_time


@login_required
def main_page(request):
    filter_param = request.GET.get('filter', 'all')
    users = get_users()
    for user in users:
        user['account_expires_raw'] = format_iso_time(user['account_expires_raw'])

    if filter_param == 'expired':
        users = [u for u in users if u.get('expired')]

    return render(request, "main_page.html", {
        "users": users,
        "filter": filter_param
    })