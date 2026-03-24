"""Accounts URL patterns."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_modal, name='profile'),
    path('user/<uuid:uid>/', views.user_profile, name='user_profile'),
]
