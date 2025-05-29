from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from rest_framework import generics, permissions, status
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, AttendanceRecord, AttendanceLog, AttendanceRequest 
from .serializers import UserSerializer, EmployeeProfileSerializer, AttendanceRecordSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, time
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from collections import defaultdict
from django.views.decorators.cache import never_cache
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from .forms import AttendanceRequestForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

User = get_user_model()

# Existing test view
def home(request):
    return JsonResponse({"message": "Welcome to ChronoLog API!"})

# New view to get user details
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

# New view to get logged-in employee's profile
class EmployeeProfileDetailView(generics.RetrieveAPIView):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.queryset.get(user=self.request.user)

class TimeInOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        attendance, created = AttendanceRecord.objects.get_or_create(user=user, date=today)

        # If time_in is not set yet
        if not attendance.time_in:
            attendance.time_in = current_time
            # Check if on time (adjust this logic based on actual schedule)
            if current_time <= time(8, 0):
                attendance.status = 'on_time'
            else:
                attendance.status = 'late'
            attendance.save()
            return Response({"message": "Time in recorded."})

        # If time_out is not set
        elif not attendance.time_out:
            attendance.time_out = current_time
            # Check for overtime (adjust this logic as needed)
            if current_time >= time(17, 0):
                attendance.status = 'overtime'
            attendance.save()
            return Response({"message": "Time out recorded."})

        return Response({"message": "Already timed in and out for today."}, status=status.HTTP_400_BAD_REQUEST)

class AttendanceHistoryView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'date']

    def get_queryset(self):
        return AttendanceRecord.objects.filter(user=self.request.user).order_by('-date')
    
@never_cache
@login_required
def employee_dashboard(request):

    if request.user.is_staff:
        return redirect('manager_dashboard')

    user = request.user
    today = datetime.today().date()

    # Get today's log or create it
    today_log, _ = AttendanceLog.objects.get_or_create(user=user, date=today)
    is_timed_in = today_log.time_in is not None and today_log.time_out is None

    # Common context
    context = {
        'today_log': today_log,
        'is_timed_in': is_timed_in,
    }

    if user.is_staff:
        # This is a manager — no EmployeeProfile expected
        return render(request, 'core/manager_dashboard.html', context)

    # Regular employee path
    try:
        profile = EmployeeProfile.objects.get(user=user)
    except EmployeeProfile.DoesNotExist:
        return HttpResponse("Employee profile not found.", status=404)

    attendance_records = AttendanceRecord.objects.filter(user=user).order_by('-date')
    attendance_by_date = {}

    for record in attendance_records:
        date_key = record.date.strftime('%Y-%m-%d')

        # Determine dot status (you can enhance this logic later if needed)
        time_in_status = 'on_time' if record.time_in else None
        time_out_status = 'overtime' if record.time_out else None

        attendance_by_date[date_key] = {
            'time_in': time_in_status,
            'time_out': time_out_status,
            'status': record.status  # keep this if you still need the overall status
        }

    photo_url = profile.profile_photo.url if profile.profile_photo else '/static/default.jpg'

    context.update({
        'profile': profile,
        'attendance_records': attendance_records,
        'attendance_by_date': attendance_by_date,
        'attendance_data_json': json.dumps(attendance_by_date),
        'photo_url': photo_url,
    })

    return render(request, 'core/employee_dashboard.html', context)


@require_POST
@login_required
def toggle_attendance(request):
    user = request.user
    today = datetime.today().date()
    now = datetime.now()

    log, _ = AttendanceLog.objects.get_or_create(user=user, date=today)
    record, _ = AttendanceRecord.objects.get_or_create(user=user, date=today)

    # Try to get the employee schedule
    try:
        profile = EmployeeProfile.objects.get(user=user)
        schedule_start = datetime.combine(today, profile.schedule_start)
        schedule_end = datetime.combine(today, profile.schedule_end)
    except EmployeeProfile.DoesNotExist:
        return JsonResponse({'error': 'No schedule found'}, status=400)

    label = ""
    status_label = record.status  # default

    if log.time_in is None:
        # TIME IN
        log.time_in = now
        record.time_in = now.time()

        if now <= schedule_start:
            record.status = 'on_time'
        else:
            record.status = 'late'

        label = "Time Out"
        status_label = record.status

    elif log.time_out is None:
        # TIME OUT
        log.time_out = now
        record.time_out = now.time()

        # Only set overtime if clock-out is after scheduled end
        if now >= schedule_end:
            record.status = 'overtime'
        label = "Done"
        status_label = record.status

    else:
        label = "Already Completed"

    log.status = record.status  # keep log in sync
    log.save()
    record.save()

    return JsonResponse({
        'time_in': log.time_in.strftime('%H:%M:%S') if log.time_in else None,
        'time_out': log.time_out.strftime('%H:%M:%S') if log.time_out else None,
        'status': status_label,
        'label': label,
    })


def dashboard_view(request):
    # Example attendance_by_date format:
    attendance_by_date = {
        "2025-05-01": "on_time",
        "2025-05-02": "late",
        "2025-05-03": "on_leave",
    }

    context = {
        # your other context variables here
        "attendance_data_json": json.dumps(attendance_by_date, cls=DjangoJSONEncoder),
    }
    return render(request, 'your_template.html', context)

@login_required
def attendance_history(request):
    selected_date = request.GET.get('date')
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    logs = AttendanceLog.objects.filter(user=request.user).order_by('-date')

    if selected_date:
        parsed_date = parse_date(selected_date)
        if parsed_date:
            logs = logs.filter(date=parsed_date)

    elif selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
            logs = logs.filter(date__year=year, date__month=month)
        except ValueError:
            pass

    elif selected_year:
        try:
            logs = logs.filter(date__year=int(selected_year))
        except ValueError:
            pass

    return render(request, 'core/history.html', {
        'attendance_logs': logs,
        'selected_date': selected_date,
        'selected_month': selected_month,
        'selected_year': selected_year,
    })


@login_required
def submit_request(request):
    if request.method == 'POST':
        form = AttendanceRequestForm(request.POST, request.FILES)
        if form.is_valid():
            attendance_request = form.save(commit=False)
            attendance_request.user = request.user
            attendance_request.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': attendance_request.id,
                    'type': attendance_request.get_request_type_display(),
                    'date': attendance_request.target_date.strftime('%Y-%m-%d'),
                    'new_in': attendance_request.new_time_in.strftime('%H:%M') if attendance_request.new_time_in else '—',
                    'new_out': attendance_request.new_time_out.strftime('%H:%M') if attendance_request.new_time_out else '—',
                    'status': attendance_request.status,
                    'status_display': attendance_request.get_status_display(),
                    'proof_url': attendance_request.proof.url if attendance_request.proof else None,
                })
            return redirect('submit_request')
    else:
        form = AttendanceRequestForm()

    # ✅ Always include user's previous requests
    status_filter = request.GET.get('status')
    user_requests = AttendanceRequest.objects.filter(user=request.user).order_by('-submitted_at')
    if status_filter:
        user_requests = user_requests.filter(status=status_filter)

    return render(request, 'core/submit_request.html', {
        'form': form,
        'user_requests': user_requests,
        'status_filter': status_filter,
    })

@login_required
def my_requests(request):
    requests = AttendanceRequest.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'core/my_requests.html', {'requests': requests})


@require_POST
@login_required
def cancel_request(request, pk):
    req = get_object_or_404(AttendanceRequest, pk=pk, user=request.user)
    
    if req.status == 'pending':
        req.status = 'cancelled'  # ✅ update status
        req.save()  # ✅ commit change to database

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'new_status': 'cancelled'})
        messages.success(request, "Request cancelled successfully.")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Only pending requests can be cancelled.'})
        messages.error(request, "Only pending requests can be cancelled.")
    
    return redirect('attendance_request')


@login_required
@staff_member_required
def review_requests(request):
    status_filter = request.GET.get('status')
    requests_qs = AttendanceRequest.objects.exclude(status='cancelled').order_by('-submitted_at')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    return render(request, 'core/manager_requests.html', {
        'requests': requests_qs,
        'selected_status': status_filter,
    })

@require_POST
@staff_member_required
def handle_request_action(request, pk):
    req = get_object_or_404(AttendanceRequest, pk=pk)
    action = request.POST.get('action')

    if req.status != 'pending':
        messages.warning(request, "Request already processed.")
        return redirect('review_requests')

    if action == 'approve':
        req.status = 'approved'
    elif action == 'reject':
        req.status = 'rejected'
    req.reviewed_by = request.user
    req.save()

    messages.success(request, f"Request {action}ed.")
    return redirect('review_requests')

@staff_member_required
@login_required
def manager_dashboard(request):
    user = request.user
    today = datetime.today().date()

    # Only use EmployeeProfile if manager has one (optional)
    profile = EmployeeProfile.objects.filter(user=user).first()

    today_log, _ = AttendanceLog.objects.get_or_create(user=user, date=today)
    is_timed_in = today_log.time_in is not None and today_log.time_out is None

    attendance_records = AttendanceRecord.objects.filter(user=user).order_by('-date')
    attendance_by_date = {
        record.date.strftime('%Y-%m-%d'): record.status
        for record in attendance_records
    }

    return render(request, 'core/manager_dashboard.html', {
        'profile': profile,
        'photo_url': profile.profile_photo.url if profile and profile.profile_photo else '/static/default.jpg',
        'today_log': today_log,
        'is_timed_in': is_timed_in,
        'attendance_records': attendance_records,
        'attendance_by_date': attendance_by_date,
        'attendance_data_json': json.dumps(attendance_by_date),
    })
