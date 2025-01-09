from django import forms
from .models import SupportTicket


# Create your forms here


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'message', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter the subject of your inquiry'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Describe your issue in detail',
                'rows': 5
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            })
        }