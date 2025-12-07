"""
URL patterns for utility endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('controller-status/', views.controller_status_check, name='controller_status_check'),
]
