"""MAST_gui URL Configuration"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect

from . import views
# Fix import: use the full Python path if 'utils' is inside the project root
from mast_utils.views import django_controller_status_check
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
    path('controller-status/', django_controller_status_check, name='controller_status_check'),
    # Plans pages
    path('plans/', plans_views.plans_index, name='plans_index'),
    path('plans/new/', plans_views.plans_new, name='plans_new'),
    path('plans/<str:ulid>/edit/', plans_views.plans_edit, name='plans_edit'),
    
    # App includes
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('units/', include('units.urls')),  # ✅ Remove namespace='units'
    path('safety/', include('mast_safety.urls', namespace='safety')),
    path('assignments/', include('assignments.urls', namespace='assignments')),
    path('specs/', include('specs.urls', namespace='specs')),
    
    # Admin/management URLs
    path('manage/users/', views.admin_users, name='admin_users'),
    path('monitoring/linux/', views.grafana, {'tag': 'linux'}, name='grafana_linux'),
    path('monitoring/windows/', views.grafana, {'tag': 'windows'}, name='grafana_windows'),
    path('manage/ownerships/', views.manage_ownerships, name='manage_ownerships'),
    path('manage/ownerships/assets/', views.ownerships_assets, name='ownerships_assets'),
    path('manage/ownerships/transfer/', views.ownerships_transfer, name='ownerships_transfer'),
    path('profile/', accounts_views.profile, name='profile'),
    path('login-modal/', accounts_views.login_modal, name='login_modal'),
    path('social/force-select/<str:provider>/', accounts_views.social_force_select, name='social_force_select'),
    path('profile/edit/', accounts_views.profile_edit, name='profile_edit'),
    path('manage/users/<int:user_id>/edit/', accounts_views.admin_user_edit, name='admin_user_edit'),
    path('manage/users/<int:user_id>/approve-edit/', accounts_views.admin_approve_edit, name='admin_approve_edit'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('manage/groups/<int:group_id>/edit/', views.admin_group_edit, name='admin_group_edit'),
    path('manage/groups/<int:group_id>/delete/', views.admin_group_delete, name='admin_group_delete'),
    # User management actions
    path('manage/users/<int:user_id>/approve/', accounts_views.admin_approve_user, name='admin_approve_user'),
    path('manage/users/<int:user_id>/reject/', accounts_views.admin_reject_user, name='admin_reject_user'),
    path('manage/users/<int:user_id>/deactivate/', accounts_views.admin_deactivate_user, name='admin_deactivate_user'),
    path('manage/users/<int:user_id>/delete/', accounts_views.admin_delete_user, name='admin_delete_user'),
    path('manage/users/<int:user_id>/delete-modal/', accounts_views.admin_delete_user_modal, name='admin_delete_user_modal'),

    # Add login route for user menu
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', accounts_views.signup, name='signup'),
    path('signup/local/', accounts_views.local_signup, name='local_signup'),  # <-- Add this line
    # Override allauth's social signup to auto-connect when email already exists
    path('accounts/3rdparty/signup/', accounts_views.social_signup_auto_connect, name='socialaccount_signup'),
    # django-allauth OAuth callbacks
    path('accounts/', include('allauth.urls')),
    # Catch-all pattern for all non-static/media URLs
    # re_path(r'^.*$', mast_dash_redirect),
    path('api/users/', views.api_users, name='api_users'),
    path('api/debug/cache', views.debug_cache, name='debug_cache'),
    path('api/debug/refresh', views.refresh_cache_endpoint, name='refresh_cache'),
    
    # SSE endpoint
    path('sse/stream/', views.sse_stream, name='sse_stream'),
    
    # Notification handler
    path('api/notifications/', views.handle_notification, name='handle_notification'),  # ✅ KEEP this one
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]