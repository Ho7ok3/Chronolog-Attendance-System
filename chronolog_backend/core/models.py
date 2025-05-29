from django.contrib.auth.models import AbstractUser
from django.db import models 
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

    def __str__(self):
        return f"{self.username} ({self.role})"

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    schedule_start = models.TimeField()
    schedule_end = models.TimeField()
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()

class AttendanceLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time_in = models.TimeField(blank=True, null=True)
    time_out = models.TimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('on_time', 'On Time'), ('late', 'Late'), ('absent', 'Absent')],
        default='absent'
    )
    auto_updated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class AttendanceRequest(models.Model):
    REQUEST_TYPES = [
        ('adjustment', 'Time Adjustment'),
        ('leave', 'Leave Request')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    target_date = models.DateField()
    new_time_in = models.TimeField(blank=True, null=True)
    new_time_out = models.TimeField(blank=True, null=True)
    reason = models.TextField()
    proof = models.FileField(upload_to='proofs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.request_type} ({self.status})"

class HelpRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Help from {self.user.username}"

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('on_time', 'On Time'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('on_leave', 'On Leave'),
        ('overtime', 'Overtime'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status}"