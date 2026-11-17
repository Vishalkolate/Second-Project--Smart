from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('student-admissions/', views.student_admissions_report, name='student_admissions_report'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('fees/', views.fees_report, name='fees_report'),
    path('internships/', views.internships_report, name='internships_report'),
]
