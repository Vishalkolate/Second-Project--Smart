from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('check-in/', views.quick_checkin, name='quick_checkin'),
    path('check-out/', views.quick_checkout, name='quick_checkout'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
    path('student/', views.student_attendance_view, name='student_attendance'),
    path('intern/', views.intern_attendance_view, name='intern_attendance'),
    path('lecture/mark/', views.mark_lecture_attendance, name='mark_lecture_attendance'),
    path('export/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/apply/', views.leave_apply, name='leave_apply'),
    path('leaves/<int:id>/action/', views.leave_action, name='leave_action'),
]
