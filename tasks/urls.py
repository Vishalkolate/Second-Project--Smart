from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('detail/<int:id>/', views.task_detail, name='task_detail'),
    path('submit/<int:assignment_id>/', views.task_submit, name='task_submit'),
    path('review/<int:assignment_id>/', views.task_review, name='task_review'),
    path('daily-reports/', views.daily_reports_list, name='daily_reports_list'),
    path('daily-reports/submit/', views.submit_daily_report, name='submit_daily_report'),
    path('daily-reports/<int:id>/feedback/', views.report_feedback, name='report_feedback'),
]
