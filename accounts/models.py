from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
import random


# Create your models here.
class LoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_sessions')
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    login_time = models.DateTimeField(auto_now_add = True)
    logout_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def duration(self):
        """ Returns the duration of the session in seconds. """
        end = self.logout_time or timezone.now()
        return end - self.login_time
        ##if self.logout_time:
        ##    return (self.logout_time - self.login_time).total_seconds()
        ##return timezone.now() - self.login_time

    def __str__(self):
        return f"{self.user.username} logged in @ {self.login_time: %Y-%m-%d %H:%M:%S}" 
    

class TwoFactorCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() -self.created_at < timedelta(minutes=10)
    
    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))  
    


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login_email = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username