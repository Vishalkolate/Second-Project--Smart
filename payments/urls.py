from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.payment_create, name='payment_create'),
    path('receipt/<int:id>/', views.payment_receipt, name='payment_receipt'),
    path('installments/', views.installment_list, name='installment_list'),
    path('installments/create/', views.installment_create, name='installment_create'),
    path('online-pay/', views.process_online_payment, name='process_online_payment'),
    path('my-payments/', views.my_payments, name='my_payments'),
]
