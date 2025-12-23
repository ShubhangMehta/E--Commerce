from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.actions import delete_selected
from .models import LoginSession



@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'ip_address',
        'login_time',
        'logout_time',
        'is_active',
        'user_agent',
    )
    list_filter = ('is_active', 'login_time')
    search_fields = ('user__username', 'ip_address')

    actions = [delete_selected]
    actions_on_top = True
    actions_on_bottom = True

    search_fields = ('user__username', 'ip_address')

    actions = [delete_selected]
    actions_on_top = True
    actions_on_bottom = True
