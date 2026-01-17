"""MAST_gui URL Configuration"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect

from . import views
# Fix import: use the full Python path if 'utils' is inside the project root
from mast_utils.views import controller_status_check
from core.views import plans as plans_views  # new: plans view for /plans/ page
from accounts import views as accounts_views
from django.contrib.auth.views import LogoutView, LoginView

def mast_dash_redirect(request, *args, **kwargs):
    # The site is selected and stored in the session by views.select_site (see 'select-site/' route)
    # It is set as: request.session['selected_site'] = site_name
    site = request.session.get('selected_site')
    if not site:
        # If not set, redirect to the dashboard (which has the site selection feature)
        return views.dashboard(request)
    return HttpResponseRedirect(f"http://mast-{site}-control:8000/mast-dash")

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin
    path('', views.dashboard, name='dashboard'),
    path('select-site/', views.select_site, name='select_site'),
    
    # Controller status check endpoint (from mast_utils)
    path('controller-status/', controller_status_check, name='controller_status_check'),
    # Plans page (only one path to plans)
    path('plans/', plans_views.plans_index, name='plans_index'),
    
    # App includes
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('units/', include('units.urls')),  # ✅ Remove namespace='units'
    path('safety/', include('mast_safety.urls', namespace='safety')),
    path('assignments/', include('assignments.urls', namespace='assignments')),
    path('specs/', include('specs.urls', namespace='specs')),
    
    # Admin/management URLs
    path('manage/users/', views.admin_users, name='admin_users'),
    path('profile/', accounts_views.profile, name='profile'),
    path('manage/users/<int:user_id>/edit/', accounts_views.admin_user_edit, name='admin_user_edit'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('manage/groups/<int:group_id>/edit/', views.admin_group_edit, name='admin_group_edit'),
    path('manage/groups/<int:group_id>/delete/', views.admin_group_delete, name='admin_group_delete'),
    path('manage/resources/', views.admin_resources, name='admin_resources'),
    path('manage/netdata-proxy/', views.netdata_proxy, name='netdata_proxy'),
    path('manage/netdata-proxy/<path:netdata_path>', views.netdata_proxy, name='netdata_proxy_path'),
        
    # Approval/Rejection URLs
    path('admin/users/<int:user_id>/approve/', accounts_views.admin_approve_user, name='admin_approve_user'),
    path('admin/users/<int:user_id>/reject/', accounts_views.admin_reject_user, name='admin_reject_user'),

    # Add login route for user menu
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', accounts_views.signup, name='signup'),
    path('signup/local/', accounts_views.local_signup, name='local_signup'),  # <-- Add this line
    # Social auth URLs (python-social-auth)
    path('auth/', include('social_django.urls', namespace='social')),
    # Django-allauth URLs (if you use allauth)
    path('accounts/', include('allauth.urls')),
    # Catch-all pattern for all non-static/media URLs
    # re_path(r'^.*$', mast_dash_redirect),
    # path('api/notifications', views.handle_notification, name='api_notifications'), # Remove?
    path('api/debug/cache', views.debug_cache, name='debug_cache'),
    path('api/debug/refresh', views.refresh_cache_endpoint, name='refresh_cache'),
    
    # SSE endpoint
    path('sse/stream/', views.sse_stream, name='sse_stream'),
    
    # Notification handler
    path('api/notification/', views.handle_notification, name='handle_notification'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
