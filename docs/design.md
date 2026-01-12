# MAST_gui Design Guidelines

## Project Overview

**Project Name:** MAST_gui 
**Full Name:** Multiple Aperture Spectroscopic Telescope - Web GUI 
**Motto:**  Spectra MASTers 
**Technology Stack:** Django + HTMX + Bootstrap 5 + Alpine.js + JS9

-----

## System Architecture

### Components

#### MAST System Structure

- **Up to 20 MAST-units**: Windows IoT machines controlling telescopes
  - Each unit controls a telescope
  - Gathers light onto optical fiber leading to spectrographs
- **1 MAST-spec**: Windows machine controlling spectrographs
- **1 MAST-controller**: Linux machine (hostname: `mast-wis-control`)
  - Main control system
  - Primary user interaction point
  - Runs scheduler
  - Hosts MongoDB configuration database

### Sites

#### WIS (Weizmann Institute, Rehovot)

- Development site
- **Deployed units**: `mastw`
- **Buildings**: Butke (building #1)
- **Controller**: `mast-wis-control`
- **Spec**: `mast-wis-spec`

#### NS (Neot Smadar, Southern Desert)

- Production site (deployment in progress)
- **Planned units**: `mast00` to `mast20` (21 units total)
- **Unit naming**: Short format (`0`, `1`, `w`) or long format (`mast00`, `mast01`, `mastw`)
- **Buildings**:
  - **Clamshell** (fast transient): 
    - Unit `mast00` (single unit)
  - **North** (building #1): 
    - Units `mast01-10` (2 rows × 5 units)
    - Numbering alternates: NE corner starts with 1, alternates North↔South rows
    - Row 1 (North): `mast01`, `mast03`, `mast05`, `mast07`, `mast09`
    - Row 2 (South): `mast02`, `mast04`, `mast06`, `mast08`, `mast10`
  - **South** (building #2):
    - Units `mast11-20` (2 rows × 5 units)
    - Row 1 (North): `mast11`, `mast13`, `mast15`, `mast17`, `mast19`
    - Row 2 (South): `mast12`, `mast14`, `mast16`, `mast18`, `mast20`
- **Controller**: `mast-ns-control` (planned)
- **Spec**: `mast-ns-spec` (planned)

**Unit Name Resolution:**
- Short format: `'w'` → `mastw` at local site
- Short format: `'0'` → `mast00` at local site
- Short format: `'1'` → `mast01` at local site
- Long format: `'mast01'` → `mast01` (explicit)
- Units 11-20: Always refer to South building units at NS site

### Configuration Database

- **Location**: MongoDB on `mast-wis-control`
- **Code**: MAST_common/config module
- **Collections**: groups, services, sites, specs, units, users
- **Special Logic**:
  - Units have `common` configuration + unit-specific overrides
  - When getting: merge common → specific
  - When setting: store only delta from common
  - Same pattern for specs (deepspec bands)

### Control Architecture

#### Centralized Control via ControlApi

**Design principle**: All GUI operations go through the MAST-controller, even for unit-specific or spec-specific commands.

**Architecture:**
```
MAST_gui (Django/HTMX)
    ↓
ControlApi (FastAPI on mast-*-control)
    ↓
├─→ UnitApi (units via network)
├─→ SpecApi (spec via network)
├─→ PowerApi (power supplies via network)
└─→ SafetyApi (safety service)
```

**Benefits:**
- **Single point of control**: All operations coordinated through controller
- **Safety enforcement**: Controller validates operations (e.g., weather checks before dome opening)
- **Centralized logging**: All commands and responses logged in one location
- **Simplified authentication**: GUI authenticates only with controller
- **Scheduling coordination**: Scheduler can manage and prioritize operations across all units
- **Transaction coordination**: Multi-unit operations handled atomically
- **State consistency**: Controller maintains global system state
- **Policy enforcement**: Business logic centralized (e.g., prevent conflicting observations)

**Implementation:**
- GUI uses `common/api.py` ControllerApi class
- All API calls return `CanonicalResponse` (defined in MAST_common)
- Backend endpoints marked with `@gui_endpoint(capability='...')` decorator
- GUI enforces access via `@proxy_backend` decorator on views
- Controller acts as proxy/coordinator for unit/spec/power operations
- Direct unit/spec access reserved for emergency/debugging only

**Alternative considered**: Direct GUI → Unit/Spec communication rejected due to:
- Safety risks (no central validation)
- Complex authentication (20+ endpoints)
- Coordination challenges (conflicting commands)
- Distributed state management complexity

-----

## Page Layout

### Banner Header (Fixed, Always Visible)

- **Height**: Fixed, 80px
- **Position**: Top of page, does not scroll
- **Left side**: Weizmann Institute logo, followed by search, site selector, breadcrumb, and user menu
- **Right side**: MAST logo + "MASTers of Spectra" motto
- **Background**: Gradient (gray)
- **Components** (left to right):
  1. Weizmann Institute logo
  2. Search field
  3. Site selector with "Site:" label
  4. Breadcrumb navigation
  5. User menu dropdown
  6. MAST logo and motto

### Toolbar (Fixed, Below Banner)

- **Height**: 64px
- **Position**: Below banner, does not scroll
- **Components** (left to right):
1. **Search field**: Global search input
1. **Site selector**: Dropdown (WIS ↔ NS)
   - **Data source**: Sites list from MongoDB config database (`Config().world().sites`)
   - **Default**: Site 'wis' (development site)
   - **Display**: Site's full name (e.g., "Weizmann Institute" for 'wis', "Neot Smadar" for 'ns')
   - **Value**: Site's short name (e.g., 'wis', 'ns')
   - **Persistence**: Selected site stored in session
   - **Behavior**: Changing site refreshes page to load site-specific data
1. **Breadcrumb navigation**: Shows current location in site
1. **User authentication**: Avatar/name dropdown with profile/logout

### Sidebar (Collapsible, Fixed)

- **Width**: 300px (expanded), 70px (collapsed)
- **Position**: Left side, always present on all pages
- **Color**: Light background (#f8f9fa) with dark text
- **Border**: Right border to separate from content
- **Behavior**:
  - Collapsible via toggle button at top of sidebar
  - State persists during navigation
  - Sub-items collapse when sidebar collapses
  - Collapse indicators: chevron points down when collapsed, up when expanded

#### Sidebar Menu Structure

1. **Units**
1. **Specs**
1. **Safety** (collapsible)
   - Graphs (Grafana iframe)
   - Data (API queries → collapsible JSON trees)
1. **Assignments**
1. **Plans**
1. **Admin** (collapsible, requires `canChangeUsers`)
   - User Management
   - Resources (Netdata monitoring)
   - ...

#### Sidebar: Plans link (implementation note)

If the "Plans" sidebar entry currently does nothing, implement it as a regular navigation link to the Plans page route. Recommended minimal template markup (Django) — insert into your sidebar template where menu items are rendered:

```html
{# filepath: templates/includes/sidebar.html (example) #}
<ul class="nav flex-column">
  <!-- ...other menu items... -->
  <li class="nav-item">
    <a class="nav-link" href="{% url 'plans_index' %}" id="sidebar-link-plans">
      <i class="bi bi-list-ul"></i>
      <span class="ms-1">Plans</span>
    </a>
  </li>
  <!-- ...other menu items... -->
</ul>
```

Notes:
- Use the Django URL name 'plans_index' (ensure you have path("plans/", plans.plans_index, name="plans_index") in core/urls.py).  
- If you prefer a client-side activation (SPA-like), keep href but also attach a small script to avoid page reload and toggle active classes.

Minimal JS to ensure click navigates and sets active class (drop into your global script file or base template):

```javascript
// filepath: static/js/sidebar.js (or inline <script> in base.html)
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('sidebar-link-plans');
  if (!el) return;
  el.addEventListener('click', (ev) => {
    // Default behavior: navigate to the plans page (href)
    // If you want client-side handling (no full reload), call ev.preventDefault()
    // and use history.pushState + dynamic content load.

    // Visually mark active
    document.querySelectorAll('.sidebar .nav-link.active').forEach(a => a.classList.remove('active'));
    el.classList.add('active');
  });
});
```

If you already use a sidebar rendering mechanism (server-side active detection), prefer server-side logic:

```django
<a class="nav-link {% if request.path == '/plans/' %}active{% endif %}" href="{% url 'plans_index' %}">Plans</a>
```

Finally, ensure the Plans view exists at /plans/ (core/views/plans.py -> plans_index) and is referenced in core/urls.py with name='plans_index'. Once the sidebar anchor is present and the view/URL exist, clicking "Plans" will load the plans page.

### Main Content Area

- **Position**: Right of sidebar, below toolbar and banner
- **Responsive**: Adjusts when sidebar collapses
- **Padding**: 20px

-----

## Dashboard (Landing Page)

### Layout Sections

1. **Units Status Grid**
- Visual grid/cards showing all units
- **Grouped by building** for multi-building sites
- Traffic light status indicators per unit:
  - 🟢 Green = operational/online
  - 🟡 Yellow = warning/maintenance
  - 🔴 Red = error/offline
  - ⚪ Gray = planned (not deployed)
- Each unit clickable → unit detail page
- **Placeholder units**: Show with “Planned” badge
1. **Spectrographs Status** (2 specs)
- Traffic light indicators
- Current status display
1. **Observation Plans Panel**
- Statistics/counts:
  - Submitted
  - Pending
  - Running
  - Completed
  - Failed/Aborted
1. **Safety Status Panel**
- Current safety conditions
- Key sensor readings
- Weather alerts

-----

## Units Page

### Unit Selector

- Shows all units for selected site
- Three visual categories:
1. **Deployed** (green/active borders): Operational, responds to connections
1. **In Maintenance** (yellow/orange borders): Temporarily offline
1. **Planned** (gray borders with “Planned” badge): Not yet deployed

### When Unit Selected

#### Power Supply Section (Above accordion, scrollable)

- **Layout**: Single horizontal line with 8 power outlets
- **Compact design**: Bold labels, narrow buttons (50px min-width)
- **Each outlet shows**:
  - Socket name (bold)
  - Colored button showing state:
    - Green (ON) / Gray (OFF) / Yellow (Unknown)
- **Interaction**:
  - If `canUseControls`: clickable to toggle
  - **Computer outlet special behavior**:
    - If ON: Shows modal warning to use Unit controls (auto-closes 3 seconds)
    - If OFF: Disabled button
  - Otherwise: read-only (disabled button)

#### Component Accordion

Each component shows:

**Collapsed (header) view:**

- Component name (Unit, Mount, Power Supply, Stage, Camera, Focuser)
- **Status columns**:
  - ✓ Powered (checkmark or dash)
  - ✓ Detected (checkmark or dash)
  - ✓ Operational (checkmark or dash)
- **Status indicators**:
  - ✓ Green checkmark = true/good
  - ➖ Red dash = false/problem
  - ⚪ Gray = unknown/N/A
- **Key detail**:
  - Focuser: position
  - Stage: position, preset name (if at preset)
  - Mount: coordinates (RA, Dec)
  - Camera: temperature
  - Unit: status info
- **Activity status**:
  - List of in-progress activities, OR
  - “Idle” if no activities

**Expanded view (three sections):**

1. **Configuration Section**
- Component-specific parameters
- **Editable** if user has `canChangeConfiguration`
- **Read-only** otherwise
- Edit/Submit/Cancel pattern
1. **Control Section**
- Component-specific controls/actions
- **Interactive** if user has `canUseControls`
- **Disabled/read-only** otherwise
1. **Visual Section** (component-dependent)
- **Dropdown selector**: Sorted by date, latest first (default)
- **Content** (loaded via HTMX on accordion open):
  - Focuser: V-curve graph
  - Camera: FITS image (JS9 viewer)
  - Unit: Acquisition status
  - Mount: Position chart
- Load on accordion open, swap on dropdown change

### Component Status System

Each component has `endpoint_status()` returning:

```json
{
  "powered": bool,
  "detected": bool,
  "operational": bool,
  "why_not_operational": ["reason1", "reason2"],
  "activities_verbal": ["Activity in progress", ...]
}
```

**Hover behavior**: Non-operational indicators show tooltip with `why_not_operational` reasons

-----

## Real-time Activity Notifications

### Architecture Overview

The MAST GUI implements a real-time notification system using Server-Sent Events (SSE) to push status updates from backend machines to the browser without polling.

#### System Components

**Backend Machines (Units, Specs):**
- Generate notifications for status changes (position updates, activity changes, errors)
- Send notifications to Backend Controller via `Notifier().send_update()`
- Use `common/notifications.py` module

**Backend Controller (`mast-*-control`):**
- Receives notifications from all machines via POST `/api/notifications`
- Forwards notifications to Django GUI server
- Acts as central notification hub

**Django GUI Server:**
- Receives notifications via POST `/api/notifications` endpoint
- Updates in-memory cache (`_MAST_CACHE`)
- Sends SSE events to connected browsers
- Filters notifications by user session (site/unit selection)

**Browser:**
- Maintains SSE connection to Django
- Receives filtered notification events
- Updates DOM elements without page reload
- Displays toast cards for important events

#### Communication Flow

```
Unit/Spec Machine
    ↓ (Notifier.send_update())
Backend Controller
    ↓ (POST /api/notifications)
Django GUI Server
    ↓ (notification_handler())
    ├─→ Update _MAST_CACHE
    ├─→ Filter by session
    └─→ Send SSE events
        ↓
Browser (EventSource)
    ├─→ Update DOM elements
    └─→ Display toast cards
```

### Notification Data Structure

#### Backend Notification (Python)

```python
from common.notifications import Notifier

# Send status update notification
Notifier().send_update(
    path=['focuser', 'position'],           # Component-relative path
    value=12345,                             # New value
    update_cache=True,                       # Update cached status
    update_dom_as='text',                    # 'text' or 'badge'
    update_card={                            # Optional toast card
        'type': 'info',                      # 'info'|'warning'|'error'|'start'|'end'
        'message': 'Focuser moved',
        'details': ['From 10000 to 12345'],
        'duration': '2.3s'                   # For 'end' type
    }
)
```

#### Notification Packet Structure

```python
class NotificationUpdateData(BaseModel):
    """Complete notification sent from backend to Django"""
    initiator: NotificationInitiator  # Site, machine_type, machine_name
    type: Literal["status_update"]
    value: list[str] | str | int | float | bool | None
    cache: dict = {}   # Cache update info
    dom: dict = {}     # DOM update info
    card: dict = {}    # Toast card info

# Example: Focuser position update from unit 'mastw' at site 'wis'
{
    "initiator": {
        "site": "wis",
        "machine_type": "unit",
        "machine_name": "mastw",
        "project": "mast"
    },
    "type": "status_update",
    "value": 12345,
    "cache": {
        "path": ["wis", "unit", "mastw", "focuser", "position"]
    },
    "dom": {
        "id": "id-focuser-position",
        "render_as": "text"
    },
    "card": {}  # Empty = no toast
}
```

### Cache Update Logic

The notification handler updates the Django context processor's in-memory cache:

```python
def update_cache(notification):
    """
    Navigate cache structure and update leaf value
    Path format: [site, machine_type, machine_name?, component, ..., field]
    """
    path = notification['cache']['path']
    
    # Parse path components
    site = path[0]              # 'wis'
    machine_type = path[1]      # 'unit', 'spec', 'controller'
    
    if machine_type == 'unit':
        machine = path[2]       # 'mastw'
        dict_path = path[3:]    # ['focuser', 'position']
    else:
        machine = None
        dict_path = path[2:]    # remaining path
    
    # Navigate to target in cache
    target = _MAST_CACHE['status'][site]
    
    if machine_type == 'unit':
        target = target['units'][machine]
    elif machine_type == 'spec':
        target = target['spec']
    elif machine_type == 'controller':
        target = target['controller']
    
    # Walk dict_path to leaf
    for key in dict_path[:-1]:
        if hasattr(target, key):
            target = getattr(target, key)
        else:
            target = target[key]
    
    # Set final value
    final_key = dict_path[-1]
    if hasattr(target, final_key):
        setattr(target, final_key, notification['value'])
    else:
        target[final_key] = notification['value']
    
    # Update cache timestamp
    _MAST_CACHE['last_refresh'] = time.time()
```

### DOM Update Logic

The notification handler sends pre-rendered content to browsers via SSE:

```python
def send_dom_update(notification, user_sessions):
    """
    Pre-render content and send to matching user sessions
    """
    if not notification['dom']:
        return
    
    # Extract initiator info
    initiator = notification['initiator']
    notif_site = initiator['site']
    notif_machine_type = initiator['machine_type']
    notif_machine_name = initiator.get('machine_name')
    
    # Pre-render content based on render_as
    value = notification['value']
    render_as = notification['dom']['render_as']
    
    if render_as == 'text':
        rendered = str(value)
    elif render_as == 'badge':
        # Create badge HTML for each value
        badges = []
        values = value if isinstance(value, list) else [value]
        for v in values:
            badge_class = get_activity_badge_class(v)
            badges.append(f'<span class="badge {badge_class}">{v}</span>')
        rendered = ' '.join(badges)
    
    # Send to each matching user session
    for session in user_sessions:
        selected_site = session.get('selected_site')
        selected_unit = session.get('selected_unit')
        
        # Filter by site
        if notif_site != selected_site:
            continue
        
        # Filter by machine (units only)
        if notif_machine_type == 'unit' and notif_machine_name != selected_unit:
            continue
        
        # Send SSE event
        send_sse_to_user(session, 'dom_update', {
            'html_id': notification['dom']['id'],
            'rendered': rendered,
            'initiator': initiator
        })
```

### Toast Card Logic

```python
def send_toast_card(notification, user_sessions):
    """
    Send toast card notification to all users viewing the site
    """
    if not notification['card']:
        return
    
    card = notification['card']
    initiator = notification['initiator']
    notif_site = initiator['site']
    
    # Send to users viewing this site
    for session in user_sessions:
        selected_site = session.get('selected_site')
        
        if notif_site != selected_site:
            continue
        
        # Build card data
        card_data = {
            'type': card.get('type', 'info'),
            'message': card.get('message'),
            'details': card.get('details', []),
            'component': card.get('component'),
            'duration': card.get('duration'),
            'initiator': initiator
        }
        
        send_sse_to_user(session, 'toast_card', card_data)
```

### SSE Event Types

**1. DOM Update Event**
```javascript
// Event: 'dom_update'
{
    "html_id": "focuser-position",      // Component-relative ID
    "rendered": "12345",                 // Pre-rendered HTML/text
    "initiator": {
        "site": "wis",
        "machine_type": "unit",
        "machine_name": "mastw"
    }
}
```

**2. Toast Card Event**
```javascript
// Event: 'toast_card'
{
    "type": "warning",                   // 'info'|'warning'|'error'|'start'|'end'
    "message": "Focuser movement timeout",
    "details": [
        "Target: 15000",
        "Current: 12340"
    ],
    "component": "focuser",              // Optional
    "duration": "5.2s",                  // Optional (for 'end' type)
    "initiator": {
        "site": "wis",
        "machine_type": "unit",
        "machine_name": "mastw"
    }
}
```

### Client-Side JavaScript

```javascript
// Establish SSE connection
const eventSource = new EventSource('/api/sse');

// Store selected site/unit from page data
const selectedSite = document.body.dataset.site;
const selectedUnit = document.body.dataset.unit;

// Handle DOM updates
eventSource.addEventListener('dom_update', function(e) {
    const data = JSON.parse(e.data);
    
    // Filter by site (safety check, already filtered server-side)
    if (data.initiator.site !== selectedSite) return;
    
    // Filter by machine if on unit page
    if (data.initiator.machine_type === 'unit' && 
        data.initiator.machine_name !== selectedUnit) return;
    
    // Update DOM element
    const element = document.getElementById(data.html_id);
    if (element) {
        element.innerHTML = data.rendered;
    }
});

// Handle toast cards
eventSource.addEventListener('toast_card', function(e) {
    const data = JSON.parse(e.data);
    
    // Filter by site
    if (data.initiator.site !== selectedSite) return;
    
    // Display toast with appropriate icon and color
    showToast(data);
});

// Toast display function
function showToast(data) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${data.type}`;
    
    // Icon based on type
    const icons = {
        'info': 'bi-info-circle',
        'warning': 'bi-exclamation-triangle',
        'error': 'bi-x-circle',
        'start': 'bi-play-circle',
        'end': 'bi-check-circle'
    };
    const icon = icons[data.type] || 'bi-info-circle';
    
    let html = `
        <div class="toast-header">
            <i class="bi ${icon}"></i>
            <strong>${data.message || 'Notification'}</strong>
            <button type="button" class="btn-close" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;
    
    if (data.component || data.details || data.duration) {
        html += '<div class="toast-body">';
        if (data.component) html += `<div>Component: ${data.component}</div>`;
        if (data.details) {
            data.details.forEach(detail => {
                html += `<div>${detail}</div>`;
            });
        }
        if (data.duration) html += `<div>Duration: ${data.duration}</div>`;
        html += '</div>';
    }
    
    toast.innerHTML = html;
    
    // Add to toast container (bottom-right)
    const container = document.getElementById('toast-container');
    container.appendChild(toast);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => toast.remove(), 5000);
}
```

### HTML Template Structure

**Component IDs (component-relative, no site/unit prefix):**

```html
<!-- Focuser accordion in templates/units/components/focuser_accordion.html -->
<div class="accordion-item">
    <h2 class="accordion-header">
        <button class="accordion-button collapsed">
            <div class="d-flex w-100 align-items-center">
                <div><strong>Focuser</strong></div>
                
                <!-- Status indicators -->
                <div id="focuser-powered">
                    {% if focuser.powered %}✓{% else %}➖{% endif %}
                </div>
                
                <!-- Position display -->
                <div>
                    <span id="focuser-position">{{ focuser.position }}</span>
                </div>
                
                <!-- Activity badges -->
                <div id="focuser-activities">
                    {% for activity in focuser.activities_verbal %}
                        <span class="badge bg-warning">{{ activity }}</span>
                    {% endfor %}
                </div>
            </div>
        </button>
    </h2>
</div>
```

**Toast container in base template:**

```html
<!-- templates/base.html -->
<body data-site="{{ current_site }}" data-unit="{{ selected_unit }}">
    <!-- ...existing content... -->
    
    <!-- Toast container (bottom-right corner) -->
    <div id="toast-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999;">
        <!-- Toasts dynamically inserted here -->
    </div>
    
    <script src="{% static 'js/notifications.js' %}"></script>
</body>
```

### Django Endpoint Implementation

```python
# MAST_gui/urls.py
urlpatterns = [
    # ...existing patterns...
    path('api/notifications', views.handle_notification, name='api_notifications'),
    path('api/sse', views.sse_stream, name='api_sse'),
]

# MAST_gui/views.py
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time

@csrf_exempt
@require_http_methods(["POST"])
def handle_notification(request):
    """
    Receive notifications from backend controller
    Process: update cache, send SSE to browsers
    """
    try:
        notification = json.loads(request.body)
        
        # 1. Update cache if requested
        if notification.get('cache'):
            update_cache(notification)
        
        # 2. Send DOM update if requested
        if notification.get('dom'):
            send_dom_update(notification, get_active_sse_sessions())
        
        # 3. Send toast card if requested
        if notification.get('card'):
            send_toast_card(notification, get_active_sse_sessions())
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"Notification handling error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def sse_stream(request):
    """
    Server-Sent Events stream for real-time updates
    """
    def event_stream():
        # Register this connection
        session_id = request.session.session_key
        register_sse_connection(session_id, request.session)
        
        try:
            while True:
                # Check for events in queue for this session
                events = get_pending_events(session_id)
                
                for event in events:
                    yield f"event: {event['type']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                
                # Send keepalive every 30 seconds
                yield ": keepalive\n\n"
                time.sleep(30)
        
        finally:
            # Unregister on disconnect
            unregister_sse_connection(session_id)
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
```

### Backend Notification Examples

**Example 1: Focuser Position Update**

```python
# In unit focuser code
from common.notifications import Notifier

def on_position_changed(new_position):
    Notifier().send_update(
        path=['focuser', 'position'],
        value=new_position,
        update_cache=True,
        update_dom_as='text'
    )
```

**Example 2: Activity Start (with toast)**

```python
def start_slewing(target_ra, target_dec):
    Notifier().send_update(
        path=['mount', 'activities_verbal'],
        value=['Slewing'],
        update_cache=True,
        update_dom_as='badge',
        update_card={
            'type': 'start',
            'message': 'Mount slewing started',
            'details': [f'RA: {target_ra}', f'Dec: {target_dec}']
        }
    )
```

**Example 3: Activity End (with duration)**

```python
def slewing_complete(duration_seconds):
    Notifier().send_update(
        path=['mount', 'activities_verbal'],
        value=['Idle'],
        update_cache=True,
        update_dom_as='badge',
        update_card={
            'type': 'end',
            'message': 'Mount slewing completed',
            'duration': f'{duration_seconds:.1f}s'
        }
    )
```

**Example 4: Error Notification**

```python
def on_focuser_timeout(target, current):
    Notifier().send_update(
        path=['focuser', 'activities_verbal'],
        value=['Error: Timeout'],
        update_cache=True,
        update_dom_as='badge',
        update_card={
            'type': 'error',
            'message': 'Focuser movement timeout',
            'details': [
                f'Target: {target}',
                f'Current: {current}',
                'Manual intervention required'
            ]
        }
    )
```

### Path Structure Examples

All paths follow the format: `[site, machine_type, machine_name?, component, ..., field]`

```python
# Unit paths (include machine_name)
["wis", "unit", "mastw", "focuser", "position"]          # Unit focuser position
["wis", "unit", "mastw", "mount", "ra_j2000_hours"]      # Mount RA coordinate
["wis", "unit", "mastw", "camera", "U", "temperature"]   # Camera U-band temp
["wis", "unit", "mastw", "stage", "position"]            # Stage position
["wis", "unit", "mastw", "covers", "state"]              # Covers state

# Spec paths (no machine_name for single spec per site)
["wis", "spec", "highspec", "calibration", "lamp_on"]    # Calibration lamp state
["wis", "spec", "deepspec", "grating", "position"]       # Grating position

# Controller paths (no machine_name)
["wis", "controller", "operational"]                      # Controller status
["wis", "controller", "scheduler", "running"]             # Scheduler state
```

### Performance Considerations

**Cache Updates:**
- Single Django worker = thread-safe in-memory cache
- No race conditions (sequential processing)
- Max 30s stale data acceptable (polling fallback)

**SSE Scalability:**
- One SSE connection per browser tab
- Server-side filtering reduces bandwidth
- Keepalive prevents connection timeout

**Notification Queue:**
- Backend uses deque with max size (10 messages)
- Auto-retry on failure
- Oldest messages dropped if queue full

### Error Handling

**Missing DOM Elements:**
- Client silently ignores updates for missing IDs
- Best-effort approach (preserves UI state)
- No error thrown

**Cache Path Not Found:**
- Server logs warning
- Notification dropped
- No crash, system continues

**SSE Connection Lost:**
- Browser auto-reconnects
- Missed notifications caught by next 30s polling refresh
- Graceful degradation

### Testing Notifications

**Manual Testing:**

```python
# In Django shell or test script
from common.notifications import Notifier

# Test focuser position update
Notifier().send_update(
    path=['focuser', 'position'],
    value=99999,
    update_cache=True,
    update_dom_as='text',
    update_card={
        'type': 'info',
        'message': 'Test notification',
        'details': ['Position updated to 99999']
    }
)
```

**Browser Console Testing:**

```javascript
// Check SSE connection
eventSource.readyState  // 0=CONNECTING, 1=OPEN, 2=CLOSED

// Manually trigger DOM update
const testEvent = new MessageEvent('dom_update', {
    data: JSON.stringify({
        html_id: 'focuser-position',
        rendered: '12345',
        initiator: {site: 'wis', machine_type: 'unit', machine_name: 'mastw'}
    })
});
eventSource.dispatchEvent(testEvent);
```

### WebSocket Integration

- **Trigger**: Activity start/end events
- **Display**: Notification cards stack in **bottom-right corner**
- **Visibility**: Only when Units page is shown

### Notification Card Design

**Activity Start:**

```
┌─────────────────────────────┐
│ 🔵 Mount - Slewing          │
│ Details: RA 12:34, Dec +45° │
│                        [×]   │
└─────────────────────────────┘
```

**Activity End:**

```
┌─────────────────────────────┐
│ ✅ Mount - Slewing          │
│ Duration: 2.3s              │
│                        [×]   │
└─────────────────────────────┘
```

**Behavior:**

- Shows component name
- Auto-dismiss after timeout (5 seconds)
- Manual close button [×]
- Stack vertically in bottom-right corner, newest on top
- Fade in/out animations
- Click does not jump to component (static notification)
