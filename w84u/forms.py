# forms.py
from django.forms import ModelForm, CharField, PasswordInput, Form, EmailField
from .models import CustomUser
from django.core.exceptions import ValidationError


class UserRegistrationForm(ModelForm):
    email = EmailField(label='Email', max_length=100, help_text='')
    password = CharField(label='Пароль', widget=PasswordInput, help_text='')
    password2 = CharField(label='Повторите пароль', widget=PasswordInput, help_text='')

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'real_name', 'age', 'gender')

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким Email уже существует")
        return email

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise ValidationError('Пароли не совпадают')
        return cd['password2']


class LoginForm(Form):
    email = EmailField()
    password = CharField(widget=PasswordInput)
