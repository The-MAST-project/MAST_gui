"""
Plans views - Observation plans.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.plans')


@login_required
@capability_required('canView')
def plan_list(request):
    """List observation plans."""
    # TODO: Fetch from database/API
    plans = []
    
    context = {
        'plans': plans,
        'page_title': 'Observation Plans',
    }
    
    return render(request, 'plans/list.html', context)


@login_required
@capability_required('canView')
def plan_detail(request, plan_id):
    """Show plan details (HTMX partial)."""
    # TODO: Fetch plan by ID
    context = {
        'plan_id': plan_id,
    }
    
    return render(request, 'plans/partials/plan_detail.html', context)


@login_required
@capability_required('canChangeConfiguration')
def plan_edit(request, plan_id):
    """Edit plan (HTMX partial)."""
    # TODO: Handle POST to save changes
    context = {
        'plan_id': plan_id,
    }
    
    return render(request, 'plans/partials/plan_edit.html', context)
