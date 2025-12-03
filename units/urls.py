"""Units URL patterns."""
from django.urls import path
from . import views

app_name = 'units'

urlpatterns = [
    path('', views.units_list, name='list'),
    path('<str:unit_name>/', views.unit_detail, name='detail'),
    path('<str:unit_name>/power_switch/set_outlet/<str:outlet_id>/toggle', views.toggle_outlet, name='toggle_outlet'),
]
