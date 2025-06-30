from django.urls import path
from expiry_notifier.views import main_views, email_views, auth_views
from .services import notification_service
urlpatterns = [
    path('', main_views.main_page, name='main_page'),
    path('login/', auth_views.ldap_login, name='login'),
    path('logout/', auth_views.ldap_logout, name='logout'),
    path("send-email/<str:email>/", email_views.send_email_view, name="send_email"),

]
