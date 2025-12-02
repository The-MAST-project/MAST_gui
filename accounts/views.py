"""
Accounts views - User profile and authentication.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

logger = logging.getLogger('mast.accounts')


@login_required
def profile(request):
    """User profile page."""
    context = {
        'page_title': 'Profile',
    }
    
    return render(request, 'accounts/profile.html', context)
