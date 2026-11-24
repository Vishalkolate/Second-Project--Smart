from django.urls import path
from . import views

urlpatterns = [
    path('', views.internship_list, name='internship_list'),
    path('detail/<int:id>/', views.internship_detail, name='internship_detail'),
    path('apply/<int:program_id>/', views.apply_internship, name='apply_internship'),
    path('my-internship/', views.my_internship, name='my_internship'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/edit/<int:id>/', views.program_edit, name='program_edit'),
    path('applications/', views.application_list, name='internship_applications'),
    path('applications/<int:id>/status/', views.update_application_status, name='update_application_status'),
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('documents/', views.document_list, name='internship_documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:id>/verify/', views.verify_document, name='verify_document'),
    path('deposits/', views.deposit_list, name='internship_deposits'),
    path('deposits/create/', views.deposit_create, name='deposit_create'),
    # Daily Work Messages & Time Tracking
    path('daily-work-messages/', views.daily_work_messages, name='daily_work_messages'),
    path('daily-work/start/', views.work_start_action, name='work_start_action'),
    path('daily-work/break/<str:break_type>/<str:action>/', views.break_action, name='break_action'),
    path('daily-work/stop/', views.work_stop_action, name='work_stop_action'),
    path('daily-work/reset/', views.reset_day_action, name='reset_day_action'),
    path('daily-work/logs/', views.work_tracking_logs, name='work_tracking_logs'),
]
