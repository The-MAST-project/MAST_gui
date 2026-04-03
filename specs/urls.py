"""Specs URL patterns."""
from django.urls import path
from . import views

app_name = 'specs'

urlpatterns = [
    path('', views.spec_list, name='list'),
    path('model/', views.spec_model, name='model'),
    path('api/status/', views.spec_model_status, name='model_status'),
]
