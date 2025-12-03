"""
URL configuration for safety app
"""
from django.urls import path
from . import views

app_name = 'safety'

urlpatterns = [
    path('graphs/', views.safety_graphs, name='graphs'),
    path('data/', views.safety_data, name='data'),
]
