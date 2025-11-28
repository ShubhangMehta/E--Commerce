from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('forgot-passowrd/', views.forgot_password_view, name='forgot_password'),

    #Django built-ins for password reset
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_complete'),

    #Django built-in for sessions-logs
    path('session-logs/', views.session_logs_view, name='session_logs'),

    #Django built-in for 2FA verification
    path('verify-2fa/', views.verify_2fa_view, name='verify_2fa'),

    #Logout url
    path('logout/', views.logout_view, name='logout'),

    #Logout from all devices
    path('logout-all/', views.logout_all_devices_view, name='logout_all'),

]