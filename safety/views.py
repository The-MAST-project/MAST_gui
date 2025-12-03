"""
Views for safety monitoring
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def safety_graphs(request):
    """
    Safety graphs page - Grafana iframe
    """
    grafana_url = "http://10.23.1.25:3000"
    
    return render(request, 'safety/graphs.html', {
        'grafana_url': grafana_url,
    })


@login_required
def safety_data(request):
    """
    Safety data page - JSON tree view
    TODO: Load from safety service API
    """
    return render(request, 'safety/data.html')
