import logging
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from ..forms import LDAPLoginForm

logger = logging.getLogger(__name__)


def ldap_login(request):
    error = None
    form_data = None
    logger.debug("LDAP login view accessed")

    if request.method == 'POST':
        form = LDAPLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            logger.debug(f"Attempting authentication for user: {username}")

            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"User {username} successfully authenticated")
                return redirect('main_page')
            else:
                error = 'Invalid credentials'
                form_data = {'username': username}
                logger.warning(f"Failed authentication attempt for user: {username}")
        else:
            error = 'Please correct the form errors'
            logger.warning("Invalid form submission with errors: %s", form.errors)
    else:
        form = LDAPLoginForm()
        logger.debug("Serving empty login form")

    if form_data:
        form = LDAPLoginForm(initial=form_data)

    context = {
        'form': form,
        'error': error
    }
    logger.debug("Rendering login template with context")
    return render(request, 'auth/login.html', context)


def ldap_logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f"User {username} successfully logged out")
    else:
        logger.debug("Anonymous user logout attempt")
    return redirect('login')