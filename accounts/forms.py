from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django.views.generic import FormView, TemplateView


class SignupUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    tel = forms.CharField(max_length=11, label='電話番号')
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "tel", "gender", "age")
        widgets = {
            'kind': forms.RadioSelect,
            'gender': forms.RadioSelect,
            'age': forms.Select,
        }

    def save(self, request):
        user = super(SignupUserForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    address = forms.CharField(max_length=30, label='住所', required=False)
    tel = forms.CharField(max_length=30, label='電話番号', required=False)
