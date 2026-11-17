from django.urls import path
from . import views

urlpatterns = [
    path('', views.instructor_list, name='instructor_list'),
    path('save/', views.instructor_save, name='instructor_save'),
    path('edit/<int:id>/', views.instructor_edit, name='instructor_edit'),
    path('update/<int:id>/', views.instructor_update, name='instructor_update'),
    path('delete/<int:id>/', views.instructor_delete, name='instructor_delete'),
]
