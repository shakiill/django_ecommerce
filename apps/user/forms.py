from django import forms
from django.contrib.auth.forms import AuthenticationForm

class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(
            attrs={
                'autofocus': True,
                'placeholder': 'Phone Number',
                'class': 'input-field'
            }
        )
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'input-field',
                'autocomplete': 'current-password'
            }
        )
    )
