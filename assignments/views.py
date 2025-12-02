"""
Assignments views - Task assignments.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.assignments')


@login_required
@capability_required('canView')
def assignment_list(request):
    """List task assignments."""
    context = {
        'page_title': 'Assignments',
    }
    
    return render(request, 'assignments/list.html', context)
