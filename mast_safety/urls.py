"""Safety URL patterns."""
from django.urls import path
from . import views

app_name = 'safety'

urlpatterns = [
    path('graphs/', views.graphs, name='graphs'),
    path('data/', views.data, name='data'),
]
