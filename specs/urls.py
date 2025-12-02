"""Specs URL patterns."""
from django.urls import path
from . import views

app_name = 'specs'

urlpatterns = [
    path('', views.spec_list, name='list'),
]
