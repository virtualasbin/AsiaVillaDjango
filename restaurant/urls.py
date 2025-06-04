from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),
    path('basket/add/', views.add_to_basket, name='add_to_basket'),
    path('basket/', views.view_basket, name='view_basket'),
    path('basket/remove/<int:item_id>/', views.remove_from_basket, name='remove_from_basket'),
    path('basket/update/<int:item_id>/', views.update_basket_item, name='update_basket_item'),
    path('order/', views.order, name='order'),
    path('status/<int:order_id>/', views.status, name='status'),
    path('payment/', views.payment, name='payment'),
]
