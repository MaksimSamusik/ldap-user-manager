from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from ..forms import LDAPLoginForm

def ldap_login(request):
    error = None
    form_data = None



    if request.method == 'POST':
        form = LDAPLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('main_page')
            else:
                error = 'Неверные учетные данные'
                form_data = {'username': username}
        else:
            error = 'Пожалуйста, исправьте ошибки в форме'
    else:
        form = LDAPLoginForm()

    if form_data:
        form = LDAPLoginForm(initial=form_data)

    return render(request, 'auth/login.html', {
        'form': form,
        'error': error
    })

def ldap_logout(request):
    logout(request)
    return redirect('login')