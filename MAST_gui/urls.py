"""MAST_gui URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('dashboard.urls')),
    path('mast/api/v1/units/', include('units.urls')),
    path('mast/api/v1/specs/', include('specs.urls')),
    path('mast/api/v1/safety/', include('mast_safety.urls')),
    path('mast/api/v1/assignments/', include('assignments.urls')),
    path('mast/api/v1/plans/', include('plans.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
