from django.contrib import admin
from .models import LoginSession

# Register your models here.
@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'logout_time', 'is_active', 'user_agent')
    list_filter = ('is_active', 'login_time')
    search_fields = ('user_name', 'ip_address')
    