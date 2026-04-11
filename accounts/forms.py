# accounts/forms.py
from django import forms
from .models import SupportTicket

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description', 'category']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a brief subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please describe your issue in detail...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'subject': 'Subject',
            'description': 'Description',
            'category': 'Category',
        }