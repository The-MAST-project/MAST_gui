"""Plans URL patterns."""
from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    path('', views.plan_list, name='list'),
    path('<int:plan_id>/', views.plan_detail, name='detail'),
    path('<int:plan_id>/edit/', views.plan_edit, name='edit'),
]
