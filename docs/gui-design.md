# MAST GUI Design Document

## Architecture Overview

### System Components

### Communication Patterns

1. **Static content & Page loads**: Browser → nginx → Django
2. **Status polling**: Django background task → Backend Controller (every 30s)
3. **Notifications**: Backend → Django POST → SSE → Browser
4. **Control commands**: Browser → Django → Backend Controller

## Data Flow

### Status Updates (Periodic - 30s)

**Key points:**
- Single Django worker = in-memory cache works perfectly
- Backend polled once per 30s regardless of user count
- Users get cached data (max 30s stale)
- TCP socket for Django ↔ Backend

### Real-time Notifications (Event-driven)

**Key points:**
- No backend re-fetch on notification
- Notification carries complete data for display
- Best-effort updates (silently ignore missing elements)
- Preserves UI state (open accordions, etc.)

## Notification Schema

### Path Structure

Format: `[site, machine_type, machine_name?, component, ..., field]`

**Machine types:**
- `controller` - site controller
- `spec` - spectrograph
- `unit` - imaging unit (requires unit name)

**Examples:**
```python
# Unit focuser position
["wis", "unit", "mastw", "focuser", "position"]

# Spec calibration lamp
["wis", "spec", "highspec", "calibration", "lamp_on"]

# Controller status
["wis", "controller", "operational"]

# Unit camera status
["wis", "unit", "mastw", "camera", "U", "temperature"]
```

### Notification Structure

```json
{
  "type": "status_update",
  "path": ["wis", "unit", "mastw", "focuser", "position"],
  "value": 12345,
  "timestamp": "2026-01-06T12:34:56Z"
}
```

### Path to HTML ID Conversion

Django converts path to HTML element ID by joining with hyphens:

```python
def path_to_html_id(path: list) -> str:
    """Convert notification path to HTML element ID"""
    return '-'.join(str(p) for p in path)

# Examples:
# ["wis", "unit", "mastw", "focuser", "position"] → "wis-unit-mastw-focuser-position"
# ["wis", "spec", "highspec", "calibration", "lamp_on"] → "wis-spec-highspec-calibration-lamp_on"
```

### Template ID Pattern

Templates receive component-level context and use relative IDs (no site/unit prefix):

```html
<!-- In focuser_accordion.html - receives 'focuser' as context -->
<span id="focuser-position">{{ focuser.position }}</span>
<span id="focuser-target">{{ focuser.target }}</span>

<!-- In camera_accordion.html - receives 'camera' as context -->
<span id="camera-U-temperature">{{ camera.U.temperature }}</span>
```

### Notification Filtering by Session

Django filters notifications before sending to browser based on user's selected site/unit:

```python
def handle_notification(notification):
    """
    1. Update cache using full path
    2. For each connected user, check if notification matches their selection
    3. If match, generate component-relative html_id and send SSE
    """
    # Update cache with full path
    target = _MAST_CACHE['status']
    for key in notification['path'][:-1]:
        target = getattr(target, key, None)
        if target is None:
            return  # Path not found, ignore
    setattr(target, notification['path'][-1], notification['value'])
    
    # Extract site and machine from notification path
    # Path format: [site, machine_type, machine_name?, component, ..., field]
    notif_site = notification['path'][0]
    notif_machine_type = notification['path'][1]
    
    if notif_machine_type == 'unit':
        notif_unit = notification['path'][2]
        component_path = notification['path'][3:]  # Everything after unit name
    elif notif_machine_type == 'spec':
        notif_unit = None  # Spec doesn't have unit
        notif_spec = notification['path'][2]
        component_path = notification['path'][3:]
    elif notif_machine_type == 'controller':
        notif_unit = None
        component_path = notification['path'][2:]  # Everything after 'controller'
    
    # Send to each connected user if their selection matches
    for user_session in get_active_sse_connections():
        selected_site = user_session.get('selected_site')
        selected_unit = user_session.get('selected_unit')
        
        # Check if notification matches user's selection
        if notif_site != selected_site:
            continue
        
        if notif_machine_type == 'unit' and notif_unit != selected_unit:
            continue
        
        # Generate component-relative HTML ID (no site/unit prefix)
        html_id = '-'.join(str(p) for p in component_path)
        
        send_sse_to_user(user_session, 'status_update', {
            'html_id': html_id,
            'value': notification['value']
        })
```

### Example Flow

**Notification from backend:**
```json
{
  "path": ["wis", "unit", "mastw", "focuser", "position"],
  "value": 12345
}
```

**User A viewing site=wis, unit=mastw:**
- Receives SSE: `{html_id: "focuser-position", value: 12345}`
- Updates element: `<span id="focuser-position">`

**User B viewing site=wis, unit=maste:**
- Notification filtered out (different unit)
- No SSE sent

**User C viewing site=saf, unit=mastw:**
- Notification filtered out (different site)
- No SSE sent

### Alternative: Client-side Filtering

If SSE cannot be user-specific, send full path and filter client-side:

```javascript
// SSE sends full notification
eventSource.addEventListener('status_update', function(e) {
    const data = JSON.parse(e.data);
    const selectedSite = document.body.dataset.site;
    const selectedUnit = document.body.dataset.unit;
    
    // Check if notification matches current selection
    if (data.path[0] !== selectedSite) return;
    if (data.path[1] === 'unit' && data.path[2] !== selectedUnit) return;
    
    // Generate component-relative ID
    const componentPath = data.path[1] === 'unit' 
        ? data.path.slice(3)  // Skip site, 'unit', unit_name
        : data.path.slice(2); // Skip site, machine_type
    const htmlId = componentPath.join('-');
    
    const element = document.getElementById(htmlId);
    if (element) {
        element.textContent = data.value;
    }
});
```