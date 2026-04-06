"""
Safety views - Safety monitoring.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mast_utils.permissions import capability_required

logger = logging.getLogger('mast.safety')


@login_required
@capability_required('can_view')
def graphs(request):
    """Show Grafana dashboard iframe."""
    grafana_url = "http://10.23.1.25:3000/grafana/d/dk8DxsWVz/neot-smadar-weather?orgId=1&refresh=10s"
    context = {
        'grafana_url': grafana_url,
        'page_title': 'Safety - Graphs',
    }
    return render(request, 'safety/graphs.html', context)


@login_required
@capability_required('can_view')
def data(request):
    """Show safety data — MAST project sensor summary."""
    import httpx
    import traceback

    def _fetch_is_safe(client, url):
        try:
            r = client.get(url, timeout=5)
            r.raise_for_status()
            return r.json().get('value', {})
        except Exception as e:
            logger.warning(f"safety data: could not fetch {url}: {e}")
            return None

    sensors = []
    fetch_error = None
    global_safety = None
    mast_safety = None

    try:
        with httpx.Client(trust_env=False) as client:
            global_safety = _fetch_is_safe(client, "http://10.23.1.25:8001/is_safe")
            mast_safety   = _fetch_is_safe(client, "http://10.23.1.25:8001/mast/is_safe")
            r = client.get("http://10.23.1.25:8001/mast/sensors", timeout=5)
            r.raise_for_status()
            raw_sensors = r.json().get('value', {}).get('sensors', [])
            for s in raw_sensors:
                # Normalize readings to always be a list, with formatted values
                raw = s.get('readings')
                if raw is None:
                    s['readings'] = []
                elif isinstance(raw, dict):
                    s['readings'] = [raw]
                # Format float values to 3 decimal places
                for reading in s['readings']:
                    v = reading.get('value')
                    if isinstance(v, float):
                        reading['value_int'] = f'{int(v):>6}'
                        reading['value_dec'] = f'{abs(v) % 1:.2f}'[1:]  # ".xx"
                    else:
                        reading['value_int'] = f'{v:>6}' if v is not None else ''
                        reading['value_dec'] = ''
            sensors = raw_sensors
    except Exception as e:
        logger.warning(f"safety data: {e}\n{traceback.format_exc()}")
        fetch_error = str(e)

    from datetime import datetime, timezone
    context = {
        'page_title': 'Safety - Data',
        'sensors': sensors,
        'fetch_error': fetch_error,
        'global_safety': global_safety,
        'mast_safety': mast_safety,
        'updated_at': datetime.now(tz=timezone.utc).strftime('%H:%M:%S UTC'),
    }
    template = 'safety/_data_content.html' if request.headers.get('HX-Request') else 'safety/data.html'
    return render(request, template, context)
