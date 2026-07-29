"""
Assignments views - Task assignments.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required
from common.mast_logging import get_logger

logger = get_logger(__name__)


@login_required
@capability_required("canView")
def assignment_list(request):
    """List task assignments."""
    context = {
        "page_title": "Assignments",
    }

    return render(request, "assignments/list.html", context)
