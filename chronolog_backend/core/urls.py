from django.urls import path
from .views import (home, UserDetailView, EmployeeProfileDetailView, TimeInOutView, AttendanceHistoryView, employee_dashboard, toggle_attendance, 
                    attendance_history, handle_request_action, manager_dashboard  )
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('me/profile/', EmployeeProfileDetailView.as_view(), name='employee-profile-detail'),
    path('attendance/time/', TimeInOutView.as_view(), name='time-in-out'),
    path('attendance/history/', AttendanceHistoryView.as_view(), name='attendance-history'),
    path('dashboard/', employee_dashboard, name='employee-dashboard'),
    path('toggle-attendance/', toggle_attendance, name='toggle_attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('submit-request/', views.submit_request, name='submit_request'),
    path('cancel-request/<int:pk>/', views.cancel_request, name='cancel_request'),
    path('manager/requests/', views.review_requests, name='review_requests'),
    path('manager/requests/<int:pk>/action/', views.handle_request_action, name='handle_request_action'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),

]
