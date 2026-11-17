from django.urls import path
from . import views

urlpatterns = [
    path('', views.placement_portal, name='placement_portal'),
    path('companies/create/', views.company_create, name='company_create'),
    path('vacancies/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/<int:vacancy_id>/apply/', views.job_apply, name='job_apply'),
    path('applications/', views.job_applications, name='job_applications'),
    path('mock-interviews/', views.mock_interviews, name='mock_interviews'),
    path('mock-interviews/schedule/', views.mock_interview_schedule, name='mock_interview_schedule'),
    path('mock-interviews/<int:id>/evaluate/', views.mock_interview_evaluate, name='mock_interview_evaluate'),
]
