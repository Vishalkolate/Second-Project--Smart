from django.urls import path
from . import views
from attendance import views as attendance_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('student-mark-present/', attendance_views.student_self_attendance, name='student_self_attendance'),
    path('intern-dashboard/', views.intern_dashboard_view, name='intern_dashboard'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('settings/', views.system_settings_view, name='system_settings'),
    path('profile/', views.profile_view, name='profile'),
    path('audit-logs/', views.audit_logs_view, name='audit_logs'),
]
