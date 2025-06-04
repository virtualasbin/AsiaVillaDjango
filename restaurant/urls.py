from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),
    path('order/', views.order, name='order'),
    path('status/<int:order_id>/', views.status, name='status'),
    path('payment/', views.payment, name='payment'),
]
