from django.urls import path
from . import views

urlpatterns = [
    path('', views.certificate_list, name='certificate_list'),
    path('issue/', views.certificate_issue, name='certificate_issue'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('download/<int:id>/', views.download_certificate, name='download_certificate'),
    path('verify/', views.verify_certificate_search, name='verify_certificate_search'),
    path('verify/<str:certificate_number>/', views.verify_certificate, name='verify_certificate'),
]
