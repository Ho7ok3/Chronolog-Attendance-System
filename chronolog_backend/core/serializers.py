from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, AttendanceRecord
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ['id', 'user', 'profile_photo', 'position', 'schedule_start', 'schedule_end']

class AttendanceRecordSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_in = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    time_out = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'user', 'date', 'time_in', 'time_out', 'status', 'status_display']
        read_only_fields = ['user', 'status', 'date']


