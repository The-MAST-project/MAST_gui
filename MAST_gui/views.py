"""
Core views for site selection and basic pages
"""
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


@require_http_methods(["POST"])
def select_site(request):
    """
    Handle site selection from dropdown
    Stores selection in session and redirects back to referrer
    """
    site_name = request.POST.get('site')
    if site_name:
        request.session['selected_site'] = site_name
    
    # Redirect back to the page that submitted the form
    return redirect(request.META.get('HTTP_REFERER', '/'))


def dashboard(request):
    """
    Main dashboard/landing page
    """
    return render(request, 'dashboard.html')


@login_required
def admin_users(request):
    """
    User management page for admins
    Requires canChangeUsers capability
    """
    # TODO: Check user has canChangeUsers capability
    return render(request, 'admin/users.html')


@login_required
def admin_resources(request):
    """
    System resources monitoring page (Netdata iframe)
    """
    # Netdata URL based on current site
    current_site = request.session.get('selected_site', 'wis')
    netdata_url = f"http://mast-{current_site}-control:19999"
    
    return render(request, 'admin/resources.html', {
        'netdata_url': netdata_url
    })
