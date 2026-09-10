from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'employee_id', 'is_staff')
    list_filter = ('role', 'department', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Industrial Info', {'fields': ('role', 'department', 'employee_id', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Industrial Info', {'fields': ('role', 'department', 'employee_id')}),
    )
