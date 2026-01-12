# Plan: Implement Status Polling + Direct Notification Updates

Add background status polling (every 30s) and Server-Sent Events (SSE) for real-time activity/position notifications with direct DOM updates.

## Architecture Summary

- Single Django worker (in-memory cache, no Redis)
- Background task polls backend every 30s → updates cache
- Browser polls Django every 30s via HTMX → renders from cache
- Backend POST notifications → Django SSE stream → Browser
- Notifications update DOM directly (no backend re-fetch)

## Implementation Steps

### 1. Add SSE support to base template

- Add HTMX SSE extension in `templates/base.html` after main HTMX:
  ```html
  <script src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"></script>
  ```

### 2. Create background status polling

- Add Django-Q to `requirements.txt`: `django-q2`
- Add `'django_q'` to `INSTALLED_APPS` in `MAST_gui/settings.py`
- Create `dashboard/tasks.py` with `poll_backend_status()` function:
  - Calls `ControllerApi().get("status")`
  - Updates `_MAST_CACHE` in `MAST_gui/context_processors.py`
- Configure in `MAST_gui/settings.py`:
  ```python
  Q_CLUSTER = {
      'name': 'MAST',
      'workers': 1,
      'timeout': 90,
      'retry': 120,
      'queue_limit': 50,
      'bulk': 10,
      'orm': 'default',
      'schedule': [
          {
              'func': 'dashboard.tasks.poll_backend_status',
              'schedule_type': 'I',
              'repeats': -1,
              'seconds': 30,
          }
      ]
  }
  ```

### 3. Create notification infrastructure

- Create in-memory notification queue in `dashboard/views.py`:
  ```python
  import queue
  _notification_queue = queue.Queue(maxsize=100)
  ```
- Add `notifications_stream` view:
  - `@login_required` decorator
  - Returns `StreamingHttpResponse` with `content_type='text/event-stream'`
  - Generator function yields SSE events: `f"data: {json.dumps(notification)}\n\n"`
  - Handles `GeneratorExit` for cleanup on disconnect
- Add `receive_notification` view:
  - `@csrf_exempt` and `@require_http_methods(["POST"])` decorators
  - Accepts POST from backend with notification JSON
  - Validates basic structure (type, site, machine, component, data)
  - Adds to `_notification_queue`
  - Returns `JsonResponse({'status': 'ok'})`
- Add URL routes in `dashboard/urls.py`:
  ```python
  path('notifications/', views.notifications_stream, name='notifications'),
  path('api/notify/', views.receive_notification, name='receive_notification'),
  ```

### 4. Create units status API and partial template

- Add `units_status_api` view in `dashboard/views.py`:
  - `@login_required` and `@require_http_methods(["GET"])` decorators
  - Reads from `_MAST_CACHE` via `mast()` context processor
  - Processes unit status for current site (reuse logic from `index` view)
  - Returns `render(request, 'dashboard/partials/units_status.html', context)`
- Create `dashboard/templates/dashboard/partials/units_status.html`:
  - Display units grouped by building
  - Show status badges (operational/error/unknown)
  - Activity badges with `data-component-id` attributes
  - Clickable links to unit detail pages
  - Use Bootstrap cards/badges styling
- Add URL route in `dashboard/urls.py`:
  ```python
  path('api/units-status/', views.units_status_api, name='api_units_status'),
  ```
- Update `dashboard/templates/dashboard/index.html`:
  ```html
  <div class="card-body" 
       hx-get="{% url 'dashboard:api_units_status' %}" 
       hx-trigger="load, every 30s"
       hx-swap="innerHTML">
  ```

### 5. Add notification handler JavaScript

- Create `static/js/notifications_handler.js`:
  ```javascript
  // Connect to SSE endpoint
  const evtSource = new EventSource('/dashboard/notifications/');
  
  // Handle activity notifications
  evtSource.addEventListener('activity', (event) => {
      const notif = JSON.parse(event.data);
      updateActivityBadges(notif);
  });
  
  // Handle position notifications
  evtSource.addEventListener('position', (event) => {
      const notif = JSON.parse(event.data);
      updatePositionDisplay(notif);
  });
  
  // Helper: convert hierarchical ID to CSS-safe ID
  function componentToDomId(componentId) {
      return componentId.replace(/\./g, '-');
  }
  
  // Update activity badges
  function updateActivityBadges(notif) {
      const domId = componentToDomId(notif.component);
      const target = document.getElementById(`${domId}-activities`);
      if (!target) return; // Silently ignore if not on page
      
      const activities = notif.data.activities_verbal || [];
      target.innerHTML = activities
          .map(activity => `<span class="badge bg-info">${activity}</span>`)
          .join(' ');
  }
  
  // Update position display
  function updatePositionDisplay(notif) {
      const domId = componentToDomId(notif.component);
      const target = document.getElementById(`${domId}-position`);
      if (!target) return;
      
      target.textContent = notif.data.position;
  }
  
  // Handle reconnection
  evtSource.onerror = (err) => {
      console.warn('SSE connection error, will auto-reconnect', err);
  };
  ```
- Include in `templates/base.html` after other scripts:
  ```html
  <script src="{% get_dynamic_static_url 'js/notifications_handler.js' %}"></script>
  ```

### 6. Update component templates with targetable elements

- Modify accordion headers in `templates/units/components/`:
  - `focuser_accordion.html`
  - `camera_accordion.html`
  - `mount_accordion.html`
  - `stage_accordion.html`
  - `covers_accordion.html`
- Add `data-component-id` attribute to accordion items:
  ```html
  <div class="accordion-item" data-component-id="{{ unit_name }}.focuser">
  ```
- Add ID to activity badge containers in accordion headers:
  ```html
  <div id="{{ unit_name }}-focuser-activities" class="d-flex gap-2">
      {% for activity in focuser.activities_verbal %}
          <span class="badge bg-info">{{ activity }}</span>
      {% endfor %}
  </div>
  ```
- Add ID to position display elements:
  ```html
  <span id="{{ unit_name }}-focuser-position">{{ focuser.position }}</span>
  ```

## Notification Schema

### Component ID Format

Hierarchical dot notation:
- `unit01` - entire unit
- `unit01.focuser` - focuser component
- `unit01.camera.U` - U-band camera
- `spec.highspec.grating` - high-res spec grating
- `spec.deepspec.camera.I` - deep spec I-band camera

### Notification Structure

```json
{
  "type": "activity",
  "site": "wis",
  "machine": "unit01",
  "component": "focuser",
  "timestamp": "2026-01-06T12:34:56Z",
  "data": {
    "activities_verbal": ["Moving", "Autofocusing"]
  }
}
```

Types:
- `activity` - Activity start/end with list of current activities
- `position` - Position/state changes with current value
- More types as needed in future

### DOM Target Pattern

JavaScript converts `component.subcomponent` → `component-subcomponent` for CSS IDs:
- Component: `unit01.focuser` → ID: `unit01-focuser-activities`
- Position: `unit01.focuser` → ID: `unit01-focuser-position`

## Testing Checklist

- [ ] Background task polls backend every 30s
- [ ] Cache updates with fresh status
- [ ] Dashboard renders from cache
- [ ] SSE connection establishes
- [ ] Backend can POST notifications to Django
- [ ] Notifications appear in SSE stream
- [ ] Activity badges update without page refresh
- [ ] Open accordions stay open on notification
- [ ] Missing DOM elements fail silently
- [ ] Multiple browsers receive notifications
- [ ] SSE reconnects on disconnect

## Configuration Requirements

### Backend Changes

Backend needs to POST notifications to Django:
```python
# In backend notification handler
requests.post(
    'http://localhost:8000/dashboard/api/notify/',
    json={
        'type': 'activity',
        'site': 'wis',
        'machine': 'unit01',
        'component': 'focuser',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'activities_verbal': ['Moving']
        }
    }
)
```

### Django Settings

Ensure:
- `DEBUG = False` in production (SSE works better)
- Single worker: `gunicorn --workers 1 ...`
- Or use `python manage.py runserver` for development

## Future Considerations

1. **Backend Pydantic notification models** - Define in common/ and import for validation?
2. **Component ID mapping** - Registry/config for ID→selector mapping vs hardcoded pattern?
3. **Multi-worker support** - If scaling needed, add Redis for cache and Django Channels for SSE
4. **Notification history** - Store recent notifications for new connections to catch up?
5. **User-specific filtering** - Filter notifications by user permissions/site access?
