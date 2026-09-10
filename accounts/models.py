from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Administrator'
        ENGINEER = 'ENGINEER', 'Process & Maintenance Engineer'
        TECHNICIAN = 'TECHNICIAN', 'Field Technician'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TECHNICIAN,
        help_text="Role defines access privileges within FactoryMind AI."
    )
    department = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Mechanical, Assembly, Safety")
    employee_id = models.CharField(max_length=50, blank=True, null=True, help_text="Industrial Employee Identifier")
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_engineer_user(self):
        return self.role in [self.Role.ADMIN, self.Role.ENGINEER] or self.is_superuser

    def is_technician_user(self):
        return True  # All authenticated users have technician access level

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
