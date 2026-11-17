from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('detail/<int:id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/milestones/add/', views.milestone_add, name='milestone_add'),
    path('milestones/<int:milestone_id>/toggle/', views.milestone_toggle, name='milestone_toggle'),
    path('<int:project_id>/submit/', views.project_submit, name='project_submit'),
    path('submissions/<int:submission_id>/review/', views.submission_review, name='submission_review'),
]
