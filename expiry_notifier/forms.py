from django import forms

class LDAPLoginForm(forms.Form):
    username = forms.CharField(label="Login")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class LDAPRegisterForm(forms.Form):
    username = forms.CharField(label="Login")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Confirm password", widget=forms.PasswordInput)
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Surname")
    email = forms.EmailField(label="Email")