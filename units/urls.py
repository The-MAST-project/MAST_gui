"""Units URL patterns."""
from django.urls import path
from . import views

app_name = 'units'

urlpatterns = [
    path('', views.unit_list, name='list'),
    path('<str:unit_name>/', views.unit_detail, name='detail'),
    path('<str:unit_name>/status/', views.unit_status, name='status'),
]
