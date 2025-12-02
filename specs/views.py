"""
Specs views - Spectrograph management.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.specs')


@login_required
@capability_required('canView')
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
