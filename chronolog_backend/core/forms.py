from django import forms
from .models import AttendanceRequest

class AttendanceRequestForm(forms.ModelForm):
    class Meta:
        model = AttendanceRequest
        fields = ['request_type', 'target_date', 'new_time_in', 'new_time_out', 'reason', 'proof']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'new_time_in': forms.TimeInput(attrs={'type': 'time'}),
            'new_time_out': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
