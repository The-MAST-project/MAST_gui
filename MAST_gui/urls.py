"""MAST_gui URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views
from mast_utils import views as mast_utils_views  # Changed from 'utils' to 'mast_utils'

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin
    path('', views.dashboard, name='dashboard'),
    path('select-site/', views.select_site, name='select_site'),
    
    # Controller status check endpoint (from mast_utils)
    path('controller-status/', mast_utils_views.controller_status_check, name='controller_status_check'),
    
    # App includes
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('units/', include('units.urls')),  # ✅ Remove namespace='units'
    path('safety/', include('mast_safety.urls', namespace='safety')),
    
    # Admin/management URLs
    path('manage/users/', views.admin_users, name='admin_users'),
    path('manage/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('manage/groups/<int:group_id>/edit/', views.admin_group_edit, name='admin_group_edit'),
    path('manage/groups/<int:group_id>/delete/', views.admin_group_delete, name='admin_group_delete'),
    path('manage/resources/', views.admin_resources, name='admin_resources'),
    path('manage/netdata-proxy/', views.netdata_proxy, name='netdata_proxy'),
    path('manage/netdata-proxy/<path:netdata_path>', views.netdata_proxy, name='netdata_proxy_path'),
    
    # API endpoints
    path('mast/api/v1/units/', include('units.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
