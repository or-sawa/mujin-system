from django.contrib import admin
from .models import CustomUser

class CustomUserModelAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'date', 'zipCode', 'address')
    ordering = ('date',)
    list_filter = ('email', 'gender', 'age', 'address', 'date')

admin.site.register(CustomUser)
