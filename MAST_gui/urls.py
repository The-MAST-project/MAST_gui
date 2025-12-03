"""MAST_gui URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin
    path('', views.dashboard, name='dashboard'),
    path('select-site/', views.select_site, name='select_site'),
    path('accounts/', include('accounts.urls', namespace='accounts')),  # Add this
    path('units/', include('units.urls', namespace='units')),  # Add this
    path('safety/', include('mast_safety.urls', namespace='safety')),  # Changed to mast_safety
    path('manage/users/', views.admin_users, name='admin_users'),  # Changed from admin/
    path('manage/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('manage/groups/<int:group_id>/edit/', views.admin_group_edit, name='admin_group_edit'),
    path('manage/groups/<int:group_id>/delete/', views.admin_group_delete, name='admin_group_delete'),
    path('manage/resources/', views.admin_resources, name='admin_resources'),  # Changed from admin/
    path('manage/netdata-proxy/', views.netdata_proxy, name='netdata_proxy'),  # Add this
    path('manage/netdata-proxy/<path:netdata_path>', views.netdata_proxy, name='netdata_proxy_path'),  # Add this
    # path('', include('dashboard.urls')),
    # path('mast/api/v1/units/', include('units.urls')),
    # path('mast/api/v1/specs/', include('specs.urls')),
    # path('mast/api/v1/safety/', include('mast_safety.urls')),
    # path('mast/api/v1/assignments/', include('assignments.urls')),
    # path('mast/api/v1/plans/', include('plans.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
