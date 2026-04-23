"""
Specs views - Spectrograph management.
"""
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.specs')


@login_required
@capability_required('can_view')
def spec_model(request):
    """Interactive 3D model viewer for the MAST spectrographs."""
    import json
    try:
        from config import Config
        config = Config()
        thar_filters = config.get_thar_filters() or []
    except Exception:
        thar_filters = []

    from MAST_common.spec import GratingNames
    grating_names = list(GratingNames.__args__)

    return render(request, 'specs/model.html', {
        'page_title': 'Spectrograph 3D Model',
        'thar_filters_json': json.dumps(thar_filters),
        'grating_names_json': json.dumps(grating_names),
        'spec_status_url': request.build_absolute_uri(reverse('specs:model_status')),
    })


@login_required
@capability_required('can_view')
def spec_model_status(request):
    """Return current spec status slice for the 3D model viewer."""
    from MAST_gui.context_processors import MastCache
    sites_status = MastCache().sites_status
    if not sites_status:
        return JsonResponse({'error': 'No status available'}, status=503)

    site = request.session.get('selected_site', 'wis')
    site_status = sites_status.sites.get(site)
    if not site_status or not site_status.spec:
        return JsonResponse({'error': f'No spec status for site {site}'}, status=503)

    spec = site_status.spec
    return JsonResponse(spec.model_dump(mode='json'))


@login_required
@capability_required('can_view')
def spec_list(request):
    """List spectrographs."""
    try:
        from config import Config
        config = Config()
        
        specs_config = config.get_specs()
        
        context = {
            'specs_config': specs_config,
            'page_title': 'Spectrographs',
        }
        
        return render(request, 'specs/list.html', context)
    
    except Exception as e:
        logger.error(f"Error loading specs: {e}")
        return render(request, 'specs/list.html', {
            'error': 'Error loading spectrographs data'
        })
