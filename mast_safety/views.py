"""
Safety views - Safety monitoring.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.safety')


@login_required
@capability_required('canView')
def graphs(request):
    """Show Grafana dashboard iframe."""
    grafana_url = "http://10.23.1.25:3000/grafana/d/dk8DxsWVz/neot-smadar-weather?orgId=1&refresh=10s"
    context = {
        'grafana_url': grafana_url,
        'page_title': 'Safety - Graphs',
    }
    return render(request, 'safety/graphs.html', context)


@login_required
@capability_required('canView')
def data(request):
    """Show safety data (stations and sensors)."""
    # TODO: Fetch from safety service
    context = {
        'page_title': 'Safety - Data',
    }
    
    return render(request, 'safety/data.html', context)
