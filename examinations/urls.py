from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('create/', views.exam_create, name='exam_create'),
    path('<int:exam_id>/questions/', views.exam_questions, name='exam_questions'),
    path('questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('submit/<int:attempt_id>/', views.submit_exam, name='submit_exam'),
    path('result/<int:attempt_id>/', views.exam_result, name='exam_result'),
]
