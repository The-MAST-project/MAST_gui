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
     - Sign-up requests
     - User changes/approvals
     - Group management
   - Resources (Netdata monitoring)
     - iframe: `http://mast-wis-control:19999`
     - **Note**: Internal network access, bypasses HTTP_PROXY/HTTPS_PROXY

**Note**: All sidebar entries with sub-entries appear initially as collapsed

**Permissions**:
- Admin menu visible only to users with `canChangeUsers` capability
- Resources page accessible with `canView` capability

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
- Auto-dismiss after timeout (5-10 seconds)
- Manual close button [×]
- Stack vertically, newest on top
- Fade in/out animations
- No jump to component on click

-----

## Plans & Assignments System

### Overview

The MAST observation system separates **scientific goals** (Plans) from **execution attempts** (Assignments):

- **Plans**: Persistent entities defining **what** to observe (target, constraints, requirements)
- **Assignments**: Transient execution wrappers defining **how** observations are attempted (unit allocations, timing)

**Key Principle**: Plans survive assignment failures and can be rescheduled into new assignments with different resource allocations.

**Relationship**: 
- **One plan = One target** (1:1 relationship between plan and target)
- **One assignment = Multiple plans** (1:N relationship between assignment and plans)
- Plans can participate in multiple assignments over time
- Failed plans automatically return to eligible state for rescheduling

### Architecture Flow

```
Researcher creates Plan (M87 observation)
    ↓
PlanManager approves Plan
    ↓
Scheduler evaluates constraints (moon, airmass, seeing, time window)
    ↓
Scheduler creates Assignment (combines multiple plans with current conditions)
    - Plan A (M87) + Plan B (NGC1234) + Plan C (Crab)
    - Allocates: wis:w, ns:2, ns:5, ns:7
    ↓
Assignment executes (some plans may fail)
    - Plan A: Succeeded (units reached guiding)
    - Plan B: Succeeded
    - Plan C: Failed (guiding timeout)
    ↓
Failed plans return to Approved state (eligible for rescheduling)
Succeeded plans: observations_completed++
    ↓
Scheduler creates new Assignment (Plan C + Plan D + Plan E)
```

---

## Plans

### Concept

**A Plan defines one target with observation requirements and constraints.**

- One plan = one target (immutable association)
- Plans are persistent (survive assignment failures)
- Plans define scientific goals independent of execution details
- Plans can be re-observed multiple times (numbered or indefinite)
- Plans maintain links to all assignment attempts (success and failure)

### Plan Lifecycle

```
Draft (user editing)
  ↓ [Submit]
Submitted (awaiting approval)
  ↓ [PlanManager approves/rejects]
Approved (eligible for scheduling) / Rejected
  ↓ [Scheduler creates assignment]
Scheduled (included in assignment)
  ↓ [Assignment executes]
Succeeded / Failed
  ↓ [Owner/PlanManager can re-submit]
Approved (for additional observations)
  ↓ [When all observations complete]
Completed (archived)
```

### Plan States

- **Draft**: User creating/editing, not visible to scheduler
- **Submitted**: Awaiting review by PlanManager
- **Approved**: Eligible for scheduling by scheduler
- **Rejected**: Declined by PlanManager (with reasons)
- **Scheduled**: Currently included in an active assignment
- **Succeeded**: Observation completed successfully (linked to assignment)
- **Failed**: Assignment attempt failed (linked to assignment)
- **Completed**: All requested observations finished (archived)

**State Transitions After Assignment:**
- **Assignment succeeds** → Plan moves to `Succeeded`
  - `observations_completed` incremented
  - Link to successful assignment added to `assignment_history`
  - If `observations_completed < observations_requested` → Plan returns to `Approved` (eligible for more observations)
  - If `observations_completed >= observations_requested` → Plan moves to `Completed` (archived)
  
- **Assignment fails** → Plan moves to `Failed`
  - Link to failed assignment added to `assignment_history`
  - Plan **automatically** returns to `Approved` (eligible for rescheduling)
  - Merit may be raised (prioritizes retry)

### Plan TOML Structure

**File Pattern**: `PLN_<ULID>.toml`

**Location**: `/data/plans/<status>/PLN_<ULID>.toml`

```toml
[plan]
ulid = "01kk6rzhvkve6ta6xj9jm4cjpw"
name = "M87 Deep Spectroscopy"
owner = "john.doe"
merit = 5
status = "approved"  # draft/submitted/approved/rejected/scheduled/succeeded/failed/completed
quorum = 3  # Minimum operational units required
timeout_to_guiding = 600  # Seconds for units to reach guiding state
observations_requested = 3  # Number of observations requested (null = indefinite)
observations_completed = 1  # Number successfully completed

# Timestamps (state snapshots)
created_at = "2024-12-01T10:00:00Z"
created_by = "john.doe"
submitted_at = "2024-12-01T12:30:00Z"
approved_at = "2024-12-01T14:00:00Z"
approved_by = "admin"
last_modified = "2024-12-06T23:30:00Z"

# Links to assignments that attempted this plan
assignment_history = ["01mm...", "01nn...", "01oo..."]

[target]
name = "M87"
ra = "12:30:49.4"  # Sexagesimal or decimal degrees
dec = "+12:23:28"   # Decimal degrees

[spec]
instrument = "deepspec"  # or "highspec"
exposure = 300.0  # seconds

[spec.camera]
binning = { x=2, y=3 }
# ... other camera settings ...

[spec.camera.U]
# Band-specific overrides for deepspec
binning = { x=1 }

[constraints]
# All optional - missing constraint = no restriction

[constraints.moon]
max_phase = 0.3        # 0=new, 1=full
min_distance = 30.0    # degrees from target

[constraints.airmass]
max = 2.0              # Maximum airmass

[constraints.seeing]
max = 2.5              # arcseconds

[constraints.time_window]
start = "2024-12-01T00:00:00Z"
end = "2024-12-31T23:59:59Z"
```

**Note**: No `[[event]]` sections in TOML - detailed events stored in MongoDB.

---

## Assignments

### Concept

**An Assignment is an execution wrapper combining multiple plans that satisfy current constraints.**

- One assignment = multiple plans (targets)
- Assignments are transient (created, executed, archived)
- Assignments allocate specific units to specific plans
- Assignments execute when conditions permit
- Assignment success/failure tracked at both assignment and individual plan level

### Plan-Assignment Relationship

**Key Points:**
- Plans are **reusable** - same plan can be in multiple assignments over time
- Assignments **combine** plans that share:
  - Compatible time windows
  - Similar constraints (moon, airmass, seeing)
  - Same instrument requirements
  - Current favorable conditions

**Example Timeline:**
```
Night 1:
  Assignment #42: [Plan A, Plan B, Plan C]
    → Plan A: Succeeded
    → Plan B: Succeeded  
    → Plan C: Failed (timeout)

Night 2:
  Assignment #43: [Plan C, Plan D]  # Plan C rescheduled
    → Plan C: Succeeded
    → Plan D: Failed (spec failure)

Night 3:
  Assignment #44: [Plan D, Plan E, Plan F]  # Plan D rescheduled
    → All succeeded
```

### Assignment Lifecycle

```
Created (by scheduler)
  ↓
InProgress (executing)
  ↓
Completed (with individual plan results)
```

**No separate "Failed" state** - assignments always reach `Completed` with individual plan success/failure tracked.

### Assignment Execution Logic

**Pre-Execution Checks:**

1. **Spectrograph check**:
   - If spec NOT operational → Assignment fails immediately
   - All plans in assignment → Failed
   - Plans return to Approved state

2. **Unit allocation**:
   - Each plan attempts to acquire its required quorum of units
   - Units must reach "Guiding" state within `timeout_to_guiding`
   
3. **Assignment viability**:
   - If **zero plans** achieve quorum → Assignment ends, all plans Failed
   - If **at least one plan** achieves quorum → Assignment proceeds

**During Execution:**

**Unit timeout behavior:**
- Unit has `timeout_to_guiding` seconds to reach "Guiding" state
- If timeout expires:
  - Unit removed from operational count for that plan
  - Remaining units recounted
  - If remaining ≥ quorum → plan proceeds with fewer units
  - If remaining < quorum → plan fails

**Spectrograph failure:**
- If spec fails during observation → **all plans in assignment fail immediately**
- Partial observations discarded
- All plans return to Approved state

**Plan-level outcomes within assignment:**
- ✅ **Succeeded**: Units reached guiding, observation completed
- ❌ **Failed (quorum)**: Insufficient units operational at start
- ❌ **Failed (timeout)**: Units didn't reach guiding in time
- ❌ **Failed (spec)**: Spectrograph failure during observation

**Post-Execution:**

For each plan in assignment:
1. Update plan status (Succeeded/Failed)
2. Add assignment ULID to plan's `assignment_history`
3. If succeeded: increment `observations_completed`
4. If failed OR (succeeded but more observations requested): return plan to Approved state
5. Update plan TOML file
6. Log detailed events to MongoDB

### Assignment TOML Structure

**File Pattern**: `ASN_<ULID>.toml`

**Location**: `/data/assignments/<status>/ASN_<ULID>.toml`

```toml
[assignment]
ulid = "01mm6rzhvkve6ta6xj9jm4cjpw"
status = "completed"  # created/inprogress/completed

# Timestamps (execution record)
created = "2024-12-05T22:00:00Z"
scheduled_start = "2024-12-05T22:00:00Z"
actual_start = "2024-12-05T22:00:15Z"
completed = "2024-12-05T22:15:45Z"
duration = 945  # seconds

# Plans included in this assignment
plan_ulids = ["01kk...", "01ll...", "01nn..."]

[spectrograph]
instrument = "deepspec"
operational_at_start = true
failed_during_observation = false
failure_time = null  # timestamp if failed
failure_reason = null  # error message if failed

# Individual plan results
[[plan_result]]
plan_ulid = "01kk..."  # M87
plan_name = "M87 Deep Spectroscopy"
status = "succeeded"
units_assigned = ["wis:w", "ns:2", "ns:5"]
units_reached_guiding = ["wis:w", "ns:2", "ns:5"]
units_timed_out = []
observation_start = "2024-12-05T22:10:30Z"
observation_end = "2024-12-05T22:15:30Z"
quorum_required = 3
quorum_achieved = 3
data_path = "/data/observations/2024-12-05/ASN_01mm/PLN_01kk"

[[plan_result]]
plan_ulid = "01ll..."  # NGC1234
plan_name = "NGC1234 Survey"
status = "succeeded"
units_assigned = ["ns:3", "ns:7"]
units_reached_guiding = ["ns:3", "ns:7"]
units_timed_out = []
observation_start = "2024-12-05T22:05:00Z"
observation_end = "2024-12-05T22:10:00Z"
quorum_required = 2
quorum_achieved = 2
data_path = "/data/observations/2024-12-05/ASN_01mm/PLN_01ll"

[[plan_result]]
plan_ulid = "01nn..."  # Crab Nebula
plan_name = "Crab Nebula Multi-Unit"
status = "failed"
failure_reason = "guiding_timeout"
units_assigned = ["ns:1", "ns:4", "ns:8", "ns:10", "ns:12"]
units_reached_guiding = ["ns:1", "ns:4"]
units_timed_out = ["ns:8", "ns:10", "ns:12"]
timeout_period = 600  # seconds
quorum_required = 5
quorum_achieved = 2
data_path = null  # no data collected
```

---

## Event Logging: Hybrid Approach

### Design Rationale

**Problem**: Should events be stored in TOML files or MongoDB?

**Solution**: Hybrid approach balancing self-contained snapshots with queryable audit trails.

### Storage Strategy

**TOML Files (State Snapshots)**:
- ✅ Store current state, not event history
- ✅ Timestamps for major lifecycle changes
- ✅ Self-contained backups (TOML files include all needed info)
- ✅ Fast UI loading (parse one file)
- ✅ Links to related entities (`assignment_history`)

**MongoDB (Event Stream)**:
- ✅ Store detailed event-by-event history
- ✅ Granular actions (user edits, unit timeouts, spec failures)
- ✅ Cross-entity queries ("What happened today?")
- ✅ Analytics and reporting
- ✅ Real-time monitoring data

### MongoDB Event Schema

```python
# Collection: events
{
  "_id": ObjectId("..."),
  "timestamp": datetime,
  "event_type": str,  # "plan_created", "plan_approved", "unit_timeout", "plan_failed", etc.
  "entity_type": str,  # "plan" or "assignment"
  "entity_ulid": str,
  "actor": str,  # username or "system" or "scheduler"
  "related_entities": {
    "plan_ulid": str,
    "assignment_ulid": str,
    "unit": str
  },
  "details": dict  # Event-specific data
}
```

### Example Events

**Plan created:**
```python
{
  "timestamp": "2024-12-01T10:00:00Z",
  "event_type": "plan_created",
  "entity_type": "plan",
  "entity_ulid": "01kk...",
  "actor": "john.doe",
  "details": {
    "target_name": "M87",
    "instrument": "deepspec",
    "quorum": 3
  }
}
```

**Plan succeeded in assignment:**
```python
{
  "timestamp": "2024-12-05T22:15:30Z",
  "event_type": "plan_succeeded",
  "entity_type": "plan",
  "entity_ulid": "01kk...",
  "actor": "system",
  "related_entities": {
    "plan_ulid": "01kk...",
    "assignment_ulid": "01mm..."
  },
  "details": {
    "units_used": ["wis:w", "ns:2", "ns:5"],
    "observation_duration": 300,
    "data_path": "/data/observations/2024-12-05/ASN_01mm/PLN_01kk"
  }
}
```

**Plan failed (timeout) in assignment:**
```python
{
  "timestamp": "2024-12-05T22:10:00Z",
  "event_type": "plan_failed",
  "entity_type": "plan",
  "entity_ulid": "01nn...",
  "actor": "system",
  "related_entities": {
    "plan_ulid": "01nn...",
    "assignment_ulid": "01mm..."
  },
  "details": {
    "failure_reason": "guiding_timeout",
    "units_assigned": 5,
    "units_guiding": 2,
    "units_timed_out": ["ns:8", "ns:10", "ns:12"],
    "timeout_period": 600
  }
}
```

**Unit timeout during assignment:**
```python
{
  "timestamp": "2024-12-05T22:10:00Z",
  "event_type": "unit_timeout",
  "entity_type": "assignment",
  "entity_ulid": "01mm...",
  "actor": "system",
  "related_entities": {
    "plan_ulid": "01nn...",
    "assignment_ulid": "01mm...",
    "unit": "ns:10"
  },
  "details": {
    "timeout_period": 600,
    "elapsed": 600,
    "last_status": "acquiring",
    "target": "Crab Nebula"
  }
}
```

**Spectrograph failure during assignment:**
```python
{
  "timestamp": "2024-12-05T22:12:30Z",
  "event_type": "spectrograph_failed",
  "entity_type": "assignment",
  "entity_ulid": "01mm...",
  "actor": "system",
  "details": {
    "instrument": "deepspec",
    "error_message": "Communication lost with spec",
    "affected_plans": ["01kk...", "01ll...", "01nn..."],
    "observations_in_progress": 2
  }
}
```

### Implementation Guidelines

**When to write TOML:**
- Plan state changes (created, approved, succeeded, failed, completed)
- Assignment creation and completion
- Metadata updates (`observations_completed`, `merit`, `assignment_history`)

**When to write MongoDB:**
- All granular events (unit timeouts, user actions, edits, approvals)
- Real-time monitoring data
- Audit trail for compliance
- Cross-entity relationships

**Consistency mechanism:**
```python
def update_plan_after_assignment(plan_ulid, assignment_ulid, outcome, details):
    # 1. Update TOML (source of truth for state)
    plan = Plan.from_toml(f"PLN_{plan_ulid}.toml")
    
    if outcome == "succeeded":
        plan.status = "succeeded"
        plan.observations_completed += 1
        # Check if more observations needed
        if (plan.observations_requested is not None and 
            plan.observations_completed >= plan.observations_requested):
            plan.status = "completed"
        else:
            plan.status = "approved"  # Ready for more observations
    else:
        plan.status = "failed"
        # Auto-return to approved
        plan.status = "approved"
        plan.merit += 1  # Raise priority
    
    plan.assignment_history.append(assignment_ulid)
    plan.last_modified = datetime.now()
    plan.to_toml(f"PLN_{plan_ulid}.toml")
    
    # 2. Log detailed event to MongoDB
    mongo.events.insert_one({
        "timestamp": datetime.now(),
        "event_type": f"plan_{outcome}",
        "entity_type": "plan",
        "entity_ulid": plan_ulid,
        "actor": "system",
        "related_entities": {
            "plan_ulid": plan_ulid,
            "assignment_ulid": assignment_ulid
        },
        "details": details
    })
```

---

## Scheduler

### Behavior

**Planning Phase (before observing night):**
- Evaluates all approved plans against forecasted conditions
- Creates time-ordered projection of proposed assignments
- Example: "20:00 Assignment A (Plans 1,2,3), 22:00 Assignment B (Plans 4,5)"
- Projection is a **guideline**, not committed execution

**Real-Time Execution:**
- Only **one assignment in-progress** at a time
- After assignment completes:
  - Updates all plan states (succeeded/failed)
  - Re-evaluates current conditions (weather, seeing, moon)
  - Creates next assignment based on updated constraints
  - May deviate from projected schedule if conditions changed

### Merit System

- **Purpose**: Tiebreaker when multiple plans equally satisfy constraints
- **Initial value**: User-settable (1-10 scale, default=5)
- **Auto-adjustment**: Merit raised (+1) after assignment failure (prioritizes retry)
- **Decay**: Merit may decrease over time if repeatedly scheduled but not executed
- **Not fully defined**: Exact algorithm TBD

### Constraint Evaluation

Plans with optional constraints:
- **Missing constraint** = no restriction (soft)
- **Present constraint** = must satisfy (hard)

Example:
```toml
[constraints]
moon.max_phase = 0.3      # HARD: moon must be < 30% illuminated
airmass.max = 2.0         # HARD: airmass < 2.0 required
# seeing.max not specified # SOFT: any seeing acceptable
```

### Assignment Creation Logic

```python
def create_assignment(eligible_plans, current_conditions):
    # 1. Filter plans by hard constraints
    viable_plans = []
    for plan in eligible_plans:
        if satisfies_constraints(plan, current_conditions):
            viable_plans.append(plan)
    
    # 2. Group by instrument (can't mix deepspec and highspec)
    deepspec_plans = [p for p in viable_plans if p.spec.instrument == "deepspec"]
    highspec_plans = [p for p in viable_plans if p.spec.instrument == "highspec"]
    
    # 3. Select plans with highest merit (tiebreaker)
    selected_plans = select_by_merit(deepspec_plans, max_plans=10)
    
    # 4. Check resource availability
    total_required_units = sum(p.quorum for p in selected_plans)
    if total_required_units > available_units():
        # Reduce plan set
        selected_plans = optimize_plan_set(selected_plans)
    
    # 5. Create assignment
    assignment = Assignment(
        plan_ulids=[p.ulid for p in selected_plans],
        instrument=selected_plans[0].spec.instrument,
        created=datetime.now()
    )
    
    return assignment
```

---

## Plans Page

### UI Structure

**Tabs:**
- **My Plans**: Current user's plans (if has `canManagePlans`)
- **All Plans**: All plans (visible to all with `canView`)
- **Filter dropdowns**: Status, Instrument, Owner, Date range

### Accordion Display

**Collapsed View:**
```
[ULID icon] PLN-01kk... | M87 (12:30:49, +12:23:28) | john.doe | Approved | Merit: 5 | Obs: 1/3
```

**Expanded View:**
```
Plan: M87 Deep Spectroscopy (PLN-01kk...)

━━━ Target Information ━━━
Name: M87
RA: 12:30:49.4
Dec: +12:23:28

━━━ Observation Requirements ━━━
Instrument: deepspec
Exposure: 300s
Quorum: 3 units
Timeout to guiding: 600s
Observations: 1 of 3 completed
Merit: 5

━━━ Constraints ━━━
Moon phase: < 30%
Moon distance: > 30°
Airmass: < 2.0
Seeing: < 2.5"
Time window: 2024-12-01 to 2024-12-31

━━━ Status ━━━
Created: 2024-12-01 10:00 by john.doe
Submitted: 2024-12-01 12:30
Approved: 2024-12-01 14:00 by admin
Last modified: 2024-12-06 23:30

━━━ Assignment History ━━━
• ASN-01mm... (2024-12-05 22:00) - Failed
  Reason: Guiding timeout (2 of 5 units)
  [View Details]
  
• ASN-01nn... (2024-12-06 23:00) - Succeeded
  Units: wis:w, ns:2, ns:5
  Data: /data/observations/2024-12-06/ASN_01nn/PLN_01kk
  [View Data] [View Details]

[Edit] [Delete] [Re-submit for N observations] [Archive]
```

**Buttons (permission-based):**
- **Edit**: Owner or `canManagePlans` (only for Draft/Rejected/Failed plans)
- **Delete**: Owner or `canManagePlans` + confirmation
- **Re-submit**: Owner or `canManagePlans` (for Succeeded/Failed plans)
- **Archive**: Owner or `canManagePlans` (manual completion)

**Re-submission dialog:**
```
Re-submit plan "M87 Deep Spectroscopy" for additional observations:

Current: 1 observation completed

○ 1 additional observation (total: 2)
○ 3 additional observations (total: 4)
○ 10 additional observations (total: 11)
○ Indefinite (continue until manually stopped)

[Submit] [Cancel]
```

### Detailed Event History (Optional Drill-Down)

Clicking "View Details" on assignment loads from MongoDB:

```
━━━ Assignment ASN-01mm Execution Timeline ━━━
22:00:00 | Assignment created by scheduler
22:00:15 | Assignment started
22:00:15 | Plan: M87 - Units assigned: wis:w, ns:2, ns:5, ns:8, ns:10

22:05:30 | Plan: M87 - Unit ns:2 reached guiding
22:06:15 | Plan: M87 - Unit wis:w reached guiding
22:08:45 | Plan: M87 - Unit ns:5 reached guiding
22:10:00 | Plan: M87 - Unit ns:8 timeout (acquiring → timeout)
22:10:00 | Plan: M87 - Unit ns:10 timeout (acquiring → timeout)
22:10:00 | Plan: M87 - Quorum check: 3 of 5 required, 3 achieved ✓
22:10:30 | Plan: M87 - Observation started
22:15:30 | Plan: M87 - Observation completed ✓
22:15:45 | Assignment completed
```

---

## Assignments Page

### UI Structure

**Tabs:**
- **Scheduled**: Created by scheduler, awaiting execution
- **In Progress**: Currently executing (usually 0 or 1)
- **Completed**: Finished (with individual plan results)

**Filter dropdowns**: Date range, Instrument, Success/Partial/Failed

### Accordion Display

**Collapsed View:**
```
[ULID icon] ASN-01mm... | 2024-12-05 22:00 | 3 plans | Completed | Success: 2, Failed: 1
```

**Expanded View:**
```
Assignment: ASN-01mm6rzhvkve6ta6xj9jm4cjpw

━━━ Execution Summary ━━━
Created: 2024-12-05 22:00:00
Started: 2024-12-05 22:00:15
Completed: 2024-12-05 22:15:45
Duration: 15m 30s
Status: Completed

━━━ Spectrograph ━━━
Instrument: deepspec
Status at start: Operational ✓
Status during observation: Operational ✓

━━━ Plan Results ━━━

[✓] M87 Deep Spectroscopy (PLN-01kk...)
    Owner: john.doe
    Units assigned: wis:w, ns:2, ns:5, ns:8, ns:10 (5 total)
    Units guiding: wis:w, ns:2, ns:5 (3 of 3 required)
    Units timeout: ns:8, ns:10
    Observation: 22:10:30 - 22:15:30 (5m 0s)
    Data: /data/observations/2024-12-05/ASN_01mm/PLN_01kk
    [View Plan] [View Data]

[✓] NGC1234 Survey (PLN-01ll...)
    Owner: jane.smith
    Units assigned: ns:3, ns:7 (2 total)
    Units guiding: ns:3, ns:7 (2 of 2 required)
    Observation: 22:05:00 - 22:10:00 (5m 0s)
    Data: /data/observations/2024-12-05/ASN_01mm/PLN_01ll
    [View Plan] [View Data]

[✗] Crab Nebula Multi-Unit (PLN-01nn...)
    Owner: bob.jones
    Failure reason: Guiding timeout
    Units assigned: ns:1, ns:4, ns:8, ns:10, ns:12 (5 total)
    Units guiding: ns:1, ns:4 (2 of 5 required)
    Units timeout: ns:8, ns:10, ns:12
    Timeout period: 600s
    
    → Plan returned to Approved state for rescheduling
    [View Plan]

[View Complete Execution Log]
```

**No edit/delete buttons** - assignments are immutable execution records

### Detailed Execution Log (Optional Drill-Down)

Loads from MongoDB events:

```
━━━ Complete Execution Timeline ━━━
22:00:00 | Assignment created by scheduler
         | Plans included: M87, NGC1234, Crab Nebula
         | Instrument: deepspec
         | Units available: 12 operational

22:00:15 | Assignment execution started
         | Spectrograph status: operational ✓

22:00:15 | Plan: M87 - Unit allocation started
         | Assigned: wis:w, ns:2, ns:5, ns:8, ns:10

22:00:15 | Plan: NGC1234 - Unit allocation started
         | Assigned: ns:3, ns:7

22:00:15 | Plan: Crab Nebula - Unit allocation started
         | Assigned: ns:1, ns:4, ns:8, ns:10, ns:12

[Continues with detailed timeline...]
```

---

## Permissions & Capabilities

### New Capabilities

**`canManagePlans`**:
- **Group**: `PlanManagers`
- **Rights**:
  - Create, edit, delete own plans
  - View all plans
  - Approve/reject submitted plans (if in PlanManagers group)
  - Edit/delete any plan (if in PlanManagers group)
  - Re-submit plans for additional observations

**`canManageAssignments`**:
- **Rights**:
  - View all assignments and detailed execution logs
  - View assignment execution history
  - Future: Manually trigger scheduler
  - No editing of assignment records (immutable history)

### Viewing Rights

**All users with `canView`:**
- View all plans (read-only)
- View all assignments (read-only)
- Cannot create or modify plans/assignments
- Cannot approve/reject plans

---

## File Organization

```
/data/
├── plans/
│   ├── draft/
│   │   └── PLN_<ULID>.toml
│   ├── submitted/
│   │   └── PLN_<ULID>.toml
│   ├── approved/
│   │   └── PLN_<ULID>.toml
│   ├── rejected/
│   │   └── PLN_<ULID>.toml
│   ├── scheduled/
│   │   └── PLN_<ULID>.toml
│   ├── succeeded/
│   │   └── PLN_<ULID>.toml
│   ├── failed/
│   │   └── PLN_<ULID>.toml
│   └── completed/
│       └── PLN_<ULID>.toml
│
├── assignments/
│   ├── scheduled/
│   │   └── ASN_<ULID>.toml
│   ├── inprogress/
│   │   └── ASN_<ULID>.toml (max 1 file at a time)
│   └── completed/
│       └── ASN_<ULID>.toml
│
└── observations/
    └── YYYY-MM-DD/
        └── ASN_<ULID>/
            ├── PLN_<ULID>/
            │   └── [FITS files, logs, etc.]
            └── assignment_summary.json
```

**File movement**: Plans/assignments move between folders as state changes, preserving ULID.

---

## Example Workflows

### Workflow 1: Successful Plan Execution

```
1. User creates plan:
   - Draft: Target M87, quorum=3, observations_requested=3
   - Save → PLN_01kk.toml in /data/plans/draft/
   - MongoDB event: plan_created

2. User submits:
   - Status: Draft → Submitted
   - Move to /data/plans/submitted/
   - MongoDB event: plan_submitted

3. PlanManager approves:
   - Status: Submitted → Approved
   - Move to /data/plans/approved/
   - MongoDB event: plan_approved

4. Night 1 - Scheduler creates assignment:
   - Conditions: airmass=1.8, moon=45° ✓
   - Assignment ASN_01mm: Plan A (M87) + Plan B (NGC1234)
   - Units allocated: wis:w, ns:2, ns:5
   - Plan A status: Approved → Scheduled
   - Move PLN_01kk.toml to /data/plans/scheduled/

5. Assignment executes:
   - Assignment status: Scheduled → InProgress
   - Units acquire targets
   - 3 units reach guiding ✓
   - Observation completes ✓
   - Data saved to /data/observations/2024-12-05/ASN_01mm/PLN_01kk/

6. Post-execution:
   - Plan A status: Scheduled → Succeeded
   - observations_completed: 0 → 1
   - assignment_history: ["01mm..."]
   - Since 1 < 3 requested: Status Succeeded → Approved
   - Move PLN_01kk.toml to /data/plans/approved/ (ready for more)
   - MongoDB events: plan_succeeded, observation_completed
   
7. Night 2 - Plan rescheduled:
   - Scheduler includes Plan A in new assignment
   - Process repeats...
   
8. After 3rd success:
   - observations_completed: 3
   - Since 3 >= 3 requested: Status → Completed
   - Move to /data/plans/completed/ (archived)
```

### Workflow 2: Failed Assignment with Recovery

```
1. Night 1 - Assignment ASN_01nn created:
   - Plan C (Crab, quorum=5)
   - Units allocated: ns:1, ns:4, ns:8, ns:10, ns:12

2. Execution starts:
   - Assignment: Scheduled → InProgress
   - Plan C: Approved → Scheduled
   - 5 units attempt guiding

3. Guiding timeout (600s):
   - Only 2 units reach guiding: ns:1, ns:4
   - 3 units timeout: ns:8, ns:10, ns:12
   - Quorum check: 2 < 5 required ❌

4. Plan C fails:
   - Plan C status: Scheduled → Failed
   - assignment_history: ["01nn..."]
   - MongoDB events: unit_timeout (×3), plan_failed

5. Automatic recovery:
   - Plan C status: Failed → Approved
   - Merit: 5 → 6 (raised priority)
   - Move PLN_01cc.toml to /data/plans/approved/
   - Plan eligible for next assignment

6. Night 2 - Plan C rescheduled:
   - Scheduler creates ASN_01oo
   - Includes Plan C + Plan D
   - Different unit allocation (better seeing conditions)
   - Plan C succeeds ✓
```

### Workflow 3: Spectrograph Failure

```
1. Assignment ASN_01pp executing:
   - Plan E (in progress, 400s of 600s complete)
   - Plan F (in progress, 100s of 300s complete)
   - Plan G (not yet started)

2. Spectrograph fails at t=400s:
   - Communication lost with deepspec
   - MongoDB event: spectrograph_failed

3. Immediate assignment termination:
   - All plans in assignment → Failed
   - Plan E: Failed (incomplete observation)
   - Plan F: Failed (incomplete observation)
   - Plan G: Failed (never started)
   - Partial data discarded

4. Automatic recovery:
   - All 3 plans → Approved state
   - Merit raised for all (not their fault)
   - Plans eligible for rescheduling
   - MongoDB events logged for each plan

5. Next night (after spec repair):
   - Plans E, F, G rescheduled
   - Fresh attempt with operational spec
```

-----

## Safety Page

### Graphs Sub-page

- **Full-page iframe** embedding Grafana dashboard
- Shows weather graphs

### Data Sub-page

- **Collapsible JSON trees** showing:
  - Stations (from safety service API)
  - Sensors with values
- Loaded via HTMX from FastAPI safety service
- Bootstrap accordion for collapsible structure

-----

## Form Controls & Validation

### Visual Design

- **Border radius**: Slightly rounded corners (0.375rem)
- **All controls**: form inputs, selects, buttons

### State-based Borders

- ⚪ **Normal** (unchanged): Default border color
- 🟢 **Valid + Changed**: Green border (#28a745)
- 🔴 **Invalid**: Red border (#dc3545)

### Tooltips

- Show on hover
- Contain field descriptions, hints, valid ranges
- Defined in Pydantic field metadata

### Validation Error Display

- **Position**: Beneath the control
- **Style**: Red text, small font (0.875rem)
- **Multiple errors**: Stacked if needed

### Submit Button Behavior

- **Disabled** while ANY validation errors exist
- **Visual**: Grayed out, `cursor: not-allowed`
- **Re-enables**: When all fields valid

### Client-side Validation

- Real-time validation using Alpine.js
- Checks as user types
- Visual feedback immediate

### Server-side Validation

- Pydantic model validation
- Returns errors to display in form
- Security layer (never trust client)

-----

## Pydantic Form Generation

### Field Metadata Structure

Fields use `json_schema_extra` for UI behavior.  
**UI-related fields are grouped under a `ui` key, and do not use the `ui_` prefix.**

```python
from pydantic import BaseModel, Field

class ComponentConfig(BaseModel):
    # Dropdown selector field
    home_position: str = Field(
        default="Home",
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'select',
                'options': ['Home', 'Fiber', 'ThAr', 'Flat', 'Dark'],
                'tooltip': 'Default home position for stage'
            },
            'required_capability': 'canChangeConfiguration'
        }
    )
    
    # Numeric field
    max_position: int = Field(
        default=10000,
        description="Maximum position",
        ge=0,
        le=50000,
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'number',
                'unit': 'steps',
                'tooltip': 'Maximum allowed position',
                'error_message': 'Position must be 0-50000'
            }
        }
    )
    
    # Boolean checkbox field
    auto_home: bool = Field(
        default=True,
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'checkbox',
                'tooltip': 'Automatically home on startup'
            }
        }
    )

    # Read-only field
    current_position: int = Field(
        default=0,
        json_schema_extra={
            'ui': {
                'editable': False,
                'widget': 'readonly'
            }
        }
    )

    # Hidden field
    internal_id: str = Field(
        json_schema_extra={
            'ui': {
                'hidden': True
            }
        }
    )

    # Admin-only field
    calibration: float = Field(
        json_schema_extra={
            'ui': {
                'editable': True
            },
            'required_capability': 'canChangeAdvancedConfig'
        }
    )
```

### Metadata Fields

- **`ui`**: Dictionary containing all UI-related metadata:
    - **`editable`**: Boolean, whether user can edit
    - **`hidden`**: Boolean, hide from UI entirely
    - **`widget`**: Input control type (see Widget Types below)
    - **`options`**: List of strings for dropdown/select widgets
    - **`unit`**: Display unit (°C, steps, mm/s, etc.)
    - **`format`**: String format for display (e.g., '.1f', '.2f')
    - **`tooltip`**: Help text shown on hover
    - **`error_message`**: Custom validation error message
- **`required_capability`**: MAST capability needed to edit (outside `ui`)

### Widget Types (`widget`)

Alpine.js will render different HTML controls based on `widget`:

**Text Inputs:**
- `'text'` → `<input type="text">`
- `'email'` → `<input type="email">`
- `'password'` → `<input type="password">`
- `'url'` → `<input type="url">`
- `'tel'` → `<input type="tel">`

**Numeric Inputs:**
- `'number'` → `<input type="number">`
- `'range'` → `<input type="range">`

**Date/Time:**
- `'date'` → `<input type="date">`
- `'time'` → `<input type="time">`
- `'datetime-local'` → `<input type="datetime-local">`

**Selection:**
- `'select'` → `<select>` (requires `options` list)
- `'checkbox'` → `<input type="checkbox">`

**Text Area:**
- `'textarea'` → `<textarea>`

**Other:**
- `'color'` → `<input type="color">`
- `'file'` → `<input type="file">`
- `'readonly'` → `<span>`

### Form Field Display Rules

1. **Hidden fields** (`ui['hidden']: True`): Not rendered
2. **Read-only fields** (`ui['editable']: False`): Rendered as plain text
3. **Permission-based**: Check `required_capability` against user
4. **Dropdown fields** (`ui['widget']: 'select'`): Require `ui['options']` list
5. **Validation**: Min/max from Pydantic constraints → HTML attributes

### Example: Complete Configuration Model

```python
from pydantic import BaseModel, Field

class StageConfig(BaseModel):
    # Dropdown selector
    home_position: str = Field(
        default="Home",
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'select',
                'options': ['Home', 'Fiber', 'ThAr', 'Flat', 'Dark'],
                'tooltip': 'Default home position for stage'
            }
        }
    )
    
    # Number input with range
    max_speed: float = Field(
        default=10.0,
        ge=1.0,
        le=50.0,
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'number',
                'unit': 'mm/s',
                'tooltip': 'Maximum stage movement speed'
            }
        }
    )
    
    # Checkbox
    auto_home_on_startup: bool = Field(
        default=True,
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'checkbox',
                'tooltip': 'Automatically home stage when unit starts'
            }
        }
    )
    
    # Multi-line text
    calibration_notes: str = Field(
        default="",
        json_schema_extra={
            'ui': {
                'editable': True,
                'widget': 'textarea',
                'tooltip': 'Notes about stage calibration'
            }
        }
    )
    
    # Read-only
    serial_number: str = Field(
        default="STG-001",
        json_schema_extra={
            'ui': {
                'editable': False,
                'widget': 'readonly'
            }
        }
    )
    
    # Hidden from UI
    internal_calibration_offset: float = Field(
        default=0.0,
        json_schema_extra={
            'ui': {
                'hidden': True
            }
        }
    )
```
