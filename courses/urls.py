from django.urls import path
from . import views

urlpatterns = [
    path('', views.courses, name='course_list'),
    path('detail/<int:id>/', views.course_detail, name='course_detail'),
    path('save/', views.course_save, name='course_save'),
    path('edit/<int:id>/', views.course_edit, name='course_edit'),
    path('update/<int:id>/', views.course_update, name='course_update'),
    path('delete/<int:id>/', views.course_delete, name='course_delete'),
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/save/', views.category_save, name='category_save'),
    path('categories/edit/<int:id>/', views.category_edit, name='category_edit'),
    path('categories/update/<int:id>/', views.category_update, name='category_update'),
    path('categories/delete/<int:id>/', views.category_delete, name='category_delete'),
]
