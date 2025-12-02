# MAST_gui Design Guidelines

## Project Overview

**Project Name:** MAST_gui 
**Full Name:** Multiple Aperture Spectroscopic Telescope - Web GUI 
**Motto:** MASTers of Spectra 
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
- GUI uses `common/api.py` ControlApi class
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
- **Left side**: Weizmann Institute logo
- **Right side**: MAST logo + “MASTers of Spectra” motto
- **Background**: Gradient (gray)

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

- **Width**: 260px (expanded), 70px (collapsed)
- **Position**: Left side, always present on all pages
- **Color**: Dark background (#1e1e2d)
- **Behavior**:
  - Collapsible via toggle button
  - State persists during navigation
  - Sub-items collapse when sidebar collapses

#### Sidebar Menu Structure

1. **Units**
1. **Specs**
1. **Safety** (collapsible)
- Graphs (Grafana iframe)
- Data (API queries → collapsible JSON trees)
1. **Assignments**
1. **Plans**

**Note**: All sidebar entries with sub-entries appear initially as collapsed

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

- **Layout**: List/grid of 8 power sockets
- **Each socket shows**:
  - Socket name
  - ON/OFF indicator (green=ON, gray=OFF)
- **Interaction**:
  - If `canUseControls`: clickable to toggle
  - Otherwise: read-only

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
  - Stage: position
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

## Plans Page

### Overview

The Plans page displays and manages observation tasks stored as TOML files. Tasks are categorized into containers:
- **Pending**: Submitted tasks awaiting assignment
- **Assigned**: Tasks assigned to units but not yet executing
- **In Progress**: Currently executing task (max 1)
- **Completed**: Successfully finished tasks
- **Failed**: Failed task executions

### Pydantic Models

Tasks are built from several Pydantic models in `common/`:

**Primary Model:**
- `TaskModel` (common/tasks/models.py) - Main task container

**Supporting Models:**
- `TaskSettingsModel` (common/models/assignments.py) - Task metadata
- `TargetModel` (common/models/assignments.py) - RA/Dec coordinates
- `SpectrographModel` (common/models/spectrographs.py) - Spec configuration
- `ConstraintsModel` (common/models/constraints.py) - Observing constraints
- `EventModel` (common/tasks/models.py) - Audit events

**Key Fields from TaskSettingsModel:**
```python
name: str                    # Human-readable task name
ulid: str                    # Auto-generated unique ID
file: str                    # Auto-set file path
quorum: int | None          # Minimum units required (default: 1)
timeout_to_guiding: int     # Seconds to wait for guiding (default: 300)
production: bool            # Production vs debug mode
```

### Task Structure

Tasks are stored as TOML files following the pattern `TSK_<ULID>.toml` with the following sections:

#### [task] Section (Metadata)

```toml
[task]
name = 'Sample deepspec assigned task'  # Human-readable name
quorum = 1                               # Minimum units required
ulid = "01jj6rzhvkve6ta6xj9jm4cjpw"    # Unique identifier
file = "/path/to/task.toml"             # Absolute file path
```

#### [unit.X] Sections (Unit Assignments)

**Single Unit Notation:**
```toml
[unit.w]              # Unit 'w' at local site
ra = '12:34:56.789'   # Sexagesimal notation (HH:MM:SS.sss)
dec = -23.45          # Decimal degrees
```

**Multi-Unit Notation:**
```toml
[unit.'wis:w ns:north:2 ns:2-5,7,8-10 nam:17']
ra = '12 34 56.789'   # Space-separated sexagesimal
dec = '+45.67'        # Decimal with sign
```

**Coordinate Formats:**
- **RA**: Sexagesimal with `:` or space separators (`12:34:56.789` or `12 34 56.789`) OR decimal degrees
- **Dec**: Decimal degrees with optional `+`/`-` sign (-90 to +90)

**Unit Spec Syntax:**
- `unit_name` → Local site unit
- `site:unit` → Unit at specific site
- `site:building:unit` → Unit at site in building
- `site:2-5,7,8-10` → Range and list notation

#### [spec] Section (Spectrograph Settings)

**Common Fields:**
```toml
[spec]
instrument = 'deepspec'  # or 'highspec'
exposure = 12.5          # seconds
```

#### [spec.camera] Section (Camera Configuration)

**HighSpec (Single Camera):**
```toml
[spec.camera]
binning = { x=1, y=2 }
temperature = { set_point = -15 }        # Celsius
shutter = { opening_time=20, closing_time=30 }  # milliseconds
em_gain = 150
pre_amp_gain = 0
```

**DeepSpec (Multi-Band Camera):**
```toml
[spec.camera]
binning = { x=2, y=3 }    # Default for all bands

[spec.camera.U]            # Band-specific override
binning = { x=1 }
crop = { col=200, line=100 }

[spec.camera.X]            # Another band
binning = { x=1, y=2 }
```

**DeepSpec Bands**: U, B, V, R, I, X (6 bands total)

#### [spec.calibration] Section

```toml
[spec.calibration]
lamp_on = true
filter = 'ND1000'    # or 'ND4000', etc.
```

#### [event] Section (Audit Trail)

```toml
[event]
when = "2025-02-12T17:49:42.641525"  # ISO 8601 timestamp
what = "created"                      # Event type
```

### Layout

- **Tabbed interface**: One tab per container (Pending, Assigned, In Progress, Failed, Completed)
- **Accordion list** within each tab
- Tasks sorted by creation date (newest first)

### Task Accordion Item

**Collapsed view:**
```
┌─────────────────────────────────────────────────┐
│ ▶ Sample deepspec assigned task                │
│   Units: w | Instrument: deepspec | Exp: 12.5s │
│   Created: 2025-02-12 17:49                    │
└─────────────────────────────────────────────────┘
```

**Expanded - View Mode:**
```
┌─────────────────────────────────────────────────┐
│ ▼ Sample deepspec assigned task                │
│                                                  │
│ ┌─ Task Information ──────────────────────────┐ │
│ │ Name: Sample deepspec assigned task         │ │
│ │ ULID: 01jj6r...                             │ │
│ │ Quorum: 1 unit(s)                           │ │
│ │ File: /path/to/task.toml                    │ │
│ │ Created: 2025-02-12 17:49:42                │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─ Unit Assignments ──────────────────────────┐ │
│ │ • Unit w                                     │ │
│ │   RA: 12:34:56.789                          │ │
│ │   Dec: -23.45°                              │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─ Spectrograph ──────────────────────────────┐ │
│ │ Instrument: deepspec                         │ │
│ │ Exposure: 12.5 seconds                      │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─ Camera (Default) ──────────────────────────┐ │
│ │ Binning: 2×3                                │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─ Camera Overrides ──────────────────────────┐ │
│ │ Band U: binning 1×3, crop 200×100          │ │
│ │ Band X: binning 1×2                         │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─ Calibration ───────────────────────────────┐ │
│ │ Lamp: ON                                    │ │
│ │ Filter: ND1000                              │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ [Edit] [Delete] [Execute]                       │
└─────────────────────────────────────────────────┘
```

**Button Visibility:**
- **Edit**: Requires `canChangeConfiguration`
- **Delete**: Requires `canChangeConfiguration` + confirmation dialog
- **Execute**: Only for Assigned tasks, requires `canUseControls`

**Expanded - Edit Mode:**

Form generation process:

1. **Load task from TOML** → `TaskModel.from_toml_file()`
2. **Extract Pydantic models** → `task.task`, `task.unit`, `task.model_extra['spec']`
3. **Generate Django forms** → One per section
4. **Render with HTMX** → In-place editing
5. **Validate on submit** → Server-side Pydantic validation
6. **Update TOML file** → `tomlkit` preserves structure

**Form Sections:**

```python
# utils/forms.py
class TaskMetadataForm(forms.Form):
    """Generated from TaskSettingsModel"""
    name = forms.CharField(max_length=200)
    quorum = forms.IntegerField(min_value=1, initial=1)
    # ULID and file are read-only

class UnitAssignmentFormSet(forms.BaseFormSet):
    """Dynamic formset for multiple units"""
    # Each form has: unit_spec, ra, dec

class SpectrographForm(forms.Form):
    """Generated from SpectrographModel, instrument-dependent"""
    instrument = forms.ChoiceField(choices=[('highspec', 'HighSpec'), ('deepspec', 'DeepSpec')])
    exposure = forms.FloatField(min_value=0.001)
    # Additional fields loaded dynamically based on instrument

class CameraSettingsForm(forms.Form):
    """Instrument-dependent, generated from camera models"""
    # For highspec: single set of fields
    # For deepspec: tabbed with common + per-band overrides
```

**HTMX pattern for instrument switching:**
```html
<select name="instrument" 
        hx-get="{% url 'load_camera_form' %}"
        hx-target="#camera-settings"
        hx-trigger="change">
  <option value="highspec">HighSpec</option>
  <option value="deepspec">DeepSpec</option>
</select>

<div id="camera-settings">
  <!-- Camera form loaded here via HTMX -->
</div>
```

### Form Validation

**Client-side (Alpine.js):**

```javascript
{
  // ...existing validation code...
  
  instrument_changed() {
    // Clear instrument-specific fields
    // Trigger HTMX to load new form
  },
  
  band_override_changed(band) {
    // Toggle visibility of band-specific fields
  }
}
```

**Server-side Process:**

```python
# views.py
def save_task(request, ulid):
    # 1. Load existing task
    task = TaskModel.from_toml_file(task_path)
    
    # 2. Validate forms
    metadata_form = TaskMetadataForm(request.POST)
    unit_formset = UnitAssignmentFormSet(request.POST)
    spec_form = SpectrographForm(request.POST)
    
    if all([f.is_valid() for f in [metadata_form, unit_formset, spec_form]]):
        # 3. Update TOML structure
        toml_doc = tomlkit.load(task_path)
        
        # 4. Update sections
        toml_doc['task']['name'] = metadata_form.cleaned_data['name']
        # ... update other sections ...
        
        # 5. Validate with Pydantic (full model)
        try:
            updated_task = TaskModel(**toml_doc)
        except ValidationError as e:
            # Return errors to form
            return render_errors(e)
        
        # 6. Write back to file
        with open(task_path, 'w') as f:
            f.write(tomlkit.dumps(toml_doc))
        
        return redirect('task_detail', ulid=ulid)
```

**Validation Errors Display:**

```html
<!-- Per-field errors -->
{% if form.field.errors %}
  <div class="invalid-feedback d-block">
    {{ form.field.errors|join:", " }}
  </div>
{% endif %}

<!-- Global errors from Pydantic -->
{% if pydantic_errors %}
  <div class="alert alert-danger">
    <ul>
      {% for error in pydantic_errors %}
        <li>{{ error.loc|join:" → " }}: {{ error.msg }}</li>
      {% endfor %}
    </ul>
  </div>
{% endif %}
```

### Multi-Unit Spec Parser

For advanced users, provide text area for multi-unit specs:

```
Input: wis:w ns:north:2 ns:2-5,7,8-10 nam:17

Parsed Result:
✓ wis:w → Unit w at site WIS
✓ ns:north:2 → Unit 2 in North building at NS  
✓ ns:2-5 → Units 2, 3, 4, 5 at NS
✓ ns:7 → Unit 7 at NS
✓ ns:8-10 → Units 8, 9, 10 at NS
✓ nam:17 → Unit 17 at site NAM

Total: 11 units
```

**Toggle modes:**
- Simple mode: Dropdown selectors
- Advanced mode: Text input with parser

### Task State Transitions

```
Created → Pending → Assigned → In Progress → Completed
                                          ↘ Failed
```

**File Movement:**
- Task moves between folders as state changes
- ULID remains constant
- Original file moved, not copied

### Required Models to Review

To complete form generation, need Pydantic models from `common/`:

1. **`common/models/assignments.py`**:
   - `TaskSettingsModel` - Task metadata fields
   - `TargetModel` - RA/Dec with validators
   - `UnitAssignmentModel` - Unit-specific data
   - `SpectrographAssignmentModel` - Spec assignment data

2. **`common/models/spectrographs.py`**:
   - `SpectrographModel` - Top-level spec model
   - Camera settings models (highspec vs deepspec)
   - Band-specific models for deepspec

3. **`common/models/constraints.py`**:
   - `ConstraintsModel` - Observing constraints (optional)

4. **`common/spec.py`**:
   - `DeepspecBands` - TypeAlias for band names

These models should have `json_schema_extra` metadata for:
- `editable`: bool
- `ui_widget`: str
- `ui_group`: str
- `tooltip`: str
- `ui_unit`: str
- `required_capability`: str

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

Fields use `json_schema_extra` for UI behavior:

```python
from pydantic import BaseModel, Field

class ComponentConfig(BaseModel):
    # Editable field
    max_position: int = Field(
        default=10000,
        description="Maximum position",
        ge=0,
        le=50000,
        json_schema_extra={
            'editable': True,
            'ui_widget': 'number',
            'ui_group': 'Limits',
            'ui_unit': 'steps',
            'tooltip': 'Maximum allowed position',
            'error_message': 'Position must be 0-50000'
        }
    )

    # Read-only field
    current_position: int = Field(
        default=0,
        json_schema_extra={
            'editable': False,
            'ui_widget': 'readonly'
        }
    )

    # Hidden field
    internal_id: str = Field(
        json_schema_extra={
            'ui_hidden': True
        }
    )

    # Admin-only field
    calibration: float = Field(
        json_schema_extra={
            'editable': True,
            'required_capability': 'canChangeAdvancedConfig',
            'ui_group': 'Advanced'
        }
    )
```

### Metadata Fields

- `editable`: Boolean, whether user can edit
- `ui_hidden`: Boolean, hide from UI entirely
- `ui_widget`: ‘text’, ‘number’, ‘readonly’, etc.
- `ui_group`: Group name for organizing fields
- `ui_unit`: Display unit (°C, steps, etc.)
- `ui_format`: String format for display (e.g., ‘.1f’)
- `required_capability`: MAST capability needed to edit
- `tooltip`: Help text shown on hover
- `error_message`: Custom validation error message

### Form Field Display Rules

1. **Hidden fields** (`ui_hidden: True`): Not rendered
1. **Read-only fields** (`editable: False`): Rendered as plain text
1. **Permission-based**: Check `required_capability` against user
1. **Grouped**: Fields organized by `ui_group`
1. **Validation**: Min/max from Pydantic constraints → HTML attributes

-----

## Authentication & Authorization

### User Authentication

- **Method**: Email-based authentication
- **Options**:
  - Local account (email + password)
  - Social auth (Google, Facebook, Apple)
- **Rule**: User has EITHER social OR local (not both)

### User Identity

- **Primary identifier**: Unique username (string)
- **Username generation**: Initially derived from email (e.g., `john.doe` from `john.doe@example.com`)
- **Username changes**: User can change username if new value is unique across all users
- **Email changes**: User can change email address; username remains constant
- **Display name**: Full name used in UI; username used internally

### User Storage

- **MongoDB**: MAST configuration database
- **Django**: Session management only
- **Username**: Primary key/identifier (unique, immutable for system purposes)
- **Email**: Authentication credential (can be changed)

### User Data Structure

```json
{
  "name": "john.doe",                // unique username (primary identifier)
  "email": "user@example.com",       // current email (can be changed)
  "full_name": "John Doe",
  "password": "hashed_pw" or null,   // null for social auth
  "groups": ["admin", "operator"],
  "picture": {...}                   // from social or uploaded
}
```

**Note**: When a user changes their email:
- The `email` field is updated
- The `name` (username) remains unchanged
- MongoDB references by username remain valid
- Re-authentication required with new email

### Groups & Capabilities

```json
{
  "name": "admin",
  "members": ["user@example.com"],
  "capabilities": [
    "canChangeConfiguration",
    "canUseControls",
    "canChangeUsers",
    "canOwnTasks"
  ]
}
```

**Special group**: `everybody` - all users belong to this group

### Capability System

- **canView**: View-only access
- **canChangeConfiguration**: Edit configurations
- **canUseControls**: Operate units/components
- **canChangeUsers**: Manage users/groups
- **canOwnTasks**: Create/own observation tasks

### Profile Pictures

- **Social auth**: Fetched from provider, stored in MongoDB
- **Local account**: Manually uploaded or default avatar

-----

## API Structure

### Base Path

All MAST_control API endpoints use the base path: `/mast/control/v1/`

### Response Format

All API endpoints return a `CanonicalResponse` object (defined in `common/canonical.py`):

```python
class CanonicalResponse(BaseModel):
    succeeded: bool           # True if operation succeeded
    errors: list[str] | None  # Error messages if failed
    value: Any | None         # Response data if succeeded
```

### Endpoint Categories

#### Control Endpoints

**Tag**: `Control`

- `GET /mast/control/v1/status` - Get overall system status
  - Returns: `{spec: dict, units: dict, date: str}`
- `GET /mast/control/v1/startup` - Start controller operations
- `GET /mast/control/v1/shutdown` - Stop controller operations

#### Configuration Endpoints

**Tag**: `Config`

- `GET /mast/control/v1/config/world` - Get sites, buildings, units configuration
- `GET /mast/control/v1/config/users` - Get all users
- `GET /mast/control/v1/config/user?user_name={username}` - Get specific user
- `GET /mast/control/v1/config/get_unit/{unit_name}` - Get unit configuration
  - Returns: Merged common + unit-specific config
- `POST /mast/control/v1/config/set_unit/{unit_name}` - Set unit configuration
  - Body: `UnitConfig` (Pydantic model)
  - Stores only delta from common config
- `GET /mast/control/v1/config/get_thar_filters` - Get ThAr filter wheel configuration

#### Unit Endpoints

**Tag**: `Unit`

- `GET /mast/control/v1/unit/{unit_name}/status` - Get unit status
  - Returns: `{powered: bool, detected: bool, operational: bool, ...}`
- `GET /mast/control/v1/unit/{unit_name}/power_switch/status` - Get power switch status
  - Returns: Status of all 8 outlets
- `GET /mast/control/v1/unit/{unit_name}/power_switch/get_outlet?outlet={id}` - Get outlet state
  - Params: `outlet` (OutletId enum)
  - Returns: `'on'` or `'off'`
- `POST /mast/control/v1/unit/{unit_name}/power_switch/set_outlet` - Set outlet state
  - Params: `outlet` (OutletId), `state` ('on'|'off'|'toggle')

#### Task Endpoints

**Tag**: `Tasks`

- `GET /mast/control/v1/get_tasks` - Get all tasks
  - Optional params: `ulid`, `name`
  - Returns: `TasksResponse` with categorized task lists
    - `assigned`: Tasks assigned to units
    - `pending`: Tasks waiting for assignment
    - `failed`: Failed tasks
    - `in_progress`: Currently executing tasks
- `POST /mast/control/v1/execute_assigned_task?ulid={task_ulid}` - Execute a task
- `PUT /mast/control/v1/task_acquisition_path_notification` - Receive task file locations
  - Body: `TaskAcquisitionPathNotification`
  - Creates symlinks in task run folder
- `PUT /mast/control/v1/activity_notification` - Receive activity notifications
  - Body: `ActivityNotification`
  - Broadcasts to WebSocket clients

#### WebSocket Endpoints

- `WS /mast/control/v1/activity_notification` - WebSocket for real-time activity updates
  - Push notifications for activity start/end events
  - Used by GUI for live status updates

### Task Management

**Task Containers** (file-based with filesystem watchers):

- **pending/**: Submitted tasks waiting for scheduling
- **assigned/**: Tasks assigned to units but not started
- **in-progress/**: Currently executing task (max 1)
- **failed/**: Failed task executions
- **completed/**: Successfully completed tasks

**Task File Pattern**: `TSK_*.toml` (ULID-based naming)

**File Operations**:
- Create: Task added to list
- Modify: Task updated in list (by ULID)
- Delete: Task removed from list

### Power Switch Control

**Outlet IDs**: Enum-based (OutletId)
- Computer (unit computer)
- Mount, Camera, Focuser, Stage, Dome
- Additional accessories

**Operations**:
- Get status of all outlets
- Get individual outlet state
- Set outlet: `on`, `off`, or `toggle`

### Activity Notifications

**ActivityNotification Model**:
```python
{
  "initiator": str,          # Component name
  "activity": int,           # Activity ID
  "activity_verbal": str,    # Human-readable activity name
  "started": bool,           # True=start, False=end
  "duration": str | None     # Duration in seconds (on end)
}
```

**Flow**:
1. Unit/Spec/Controller emits activity notification
2. Controller receives via PUT endpoint
3. Controller broadcasts to all WebSocket clients (GUIs)
4. GUI displays notification card

-----

## Logging

### Structure

- **Base directory**: `/var/log/mast/`
- **Daily directories**: `/var/log/mast/<yyyy-mm-dd>/`
- **UI log file**: `ui.log` (same name in each daily directory)
- **Rollover**: Midnight UTC
- **Other logs**: Can coexist in same daily directories

### Example

```
/var/log/mast/
├── 2024-12-01/
│   ├── ui.log
│   ├── control.log
│   └── spec.log
├── 2024-12-02/
│   ├── ui.log
│   └── ...
```

-----

## Technology Choices

### Backend

- **Framework**: Django 4.2+
- **Dynamic updates**: HTMX (no page reloads)
- **Real-time**: WebSocket (Django Channels)
- **Database**: MongoDB (configuration) + SQLite (Django internal)

### Frontend

- **UI Framework**: Bootstrap 5
- **Design style**: Material Design (Mantis-inspired)
- **Icons**: Bootstrap Icons
- **Client reactivity**: Alpine.js (for validation)
- **FITS viewer**: JS9

### Why HTMX?

- Server-side simplicity (Django templates)
- No complex JavaScript state management
- Progressive enhancement
- Perfect for dashboard/monitoring UIs
- Native feel without SPA complexity

-----

## Special UI Patterns

### Editable Accordion Pattern

Used for: Plans, Unit configs, Specs configs

**States:**

1. **Collapsed**: Summary only
1. **Expanded - View mode**: Full details, Edit button
1. **Expanded - Edit mode**: In-place form, Submit/Cancel buttons

**Permissions:**

- View: `canView`
- Edit: `canChangeConfiguration`
- Delete: `canChangeConfiguration` (with confirmation)

### Collapsible JSON Trees

Used for: Safety data (initial implementation)

**Library**: Bootstrap accordion or custom component
**Future**: Format into proper tables/cards

### Traffic Light Indicators

Used for: Unit status, component status, specs status

**Colors:**

- 🟢 Green: Operational/good
- 🟡 Yellow: Warning/maintenance
- 🔴 Red: Error/offline
- ⚪ Gray: Planned/unknown

-----

## Development Guidelines

### Code Organization

- **One concern per file**: Separate views, forms, utilities
- **Pydantic for validation**: Single source of truth
- **Minimal JavaScript**: Use HTMX + Alpine.js
- **Server-side rendering**: Django templates
- **Reusable components**: Template includes

### Performance

- **Lazy loading**: Load accordion content on expand
- **Caching**: Use Django cache for MongoDB queries
- **HTMX polling**: Only for real-time data (5-10s intervals)
- **WebSocket**: For push notifications only

### Security

- **Capability checks**: Every view, every action
- **CSRF protection**: Django middleware
- **Email verification**: Optional in dev, mandatory in production
- **Secret key**: Never commit, use .env
- **MongoDB auth**: Via MAST_common Config class
- **API endpoint whitelist**: Backend endpoints marked with `@gui_endpoint` decorator
  - Decorator location: `common/decorators.py` (in MAST_common submodule)
  - Each endpoint specifies required capability inline
  - GUI views use `@proxy_backend` decorator for automatic validation
  - Unmarked endpoints are automatically blocked from GUI access
  - No separate registry file needed - decoration is self-documenting

-----

## File Structure

```
MAST_gui/
├── common/                  # MAST_common submodule
├── MAST_gui/               # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── logging_handlers.py
│   └── ...
├── accounts/               # Authentication
├── dashboard/              # Main dashboard
├── units/                  # Unit management
├── specs/                  # Spectrograph control
├── safety/                 # Safety monitoring
├── assignments/            # Task assignments
├── plans/                  # Observation plans
├── utils/                  # Shared utilities
│   ├── form_helpers.py    # Pydantic → Django forms
│   ├── permissions.py     # Capability decorators
│   └── ...
├── templates/
│   ├── base.html          # Main layout
│   └── components/        # Reusable components
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── manage.py
```

-----

## Future Enhancements

### Planned Features

- **Endpoint decoration review**: Systematic review of all backend endpoints to determine which should be GUI-accessible
  - Review MAST_control endpoints and add `@gui_endpoint` decorators
  - Review MAST_unit endpoints (if any need direct GUI access)
  - Review MAST_spec endpoints (if any need direct GUI access)
  - Document capability requirements for each decorated endpoint
- Specs page implementation
- Assignments page implementation
- Advanced plan editing
- Real-time unit status updates
- JS9 FITS viewer integration
- Safety service API integration
- WebSocket activity notifications
- User management interface

### Potential Additions

- Historical data viewing
- Alert system
- Custom dashboards per user
- Mobile responsive optimizations
- Dark mode toggle
- Export/import configurations
- Audit logging
- API documentation (Swagger/OpenAPI)

-----

## Design Principles

1. **User-centric**: Easy for astronomers, not developers
1. **Progressive disclosure**: Show what’s needed, hide complexity
1. **Consistent patterns**: Same interaction models across features
1. **Real-time awareness**: Live updates without page refresh
1. **Permission-aware**: UI adapts to user capabilities
1. **Fault-tolerant**: Graceful degradation, clear error messages
1. **Performance**: Fast loading, lazy loading, caching
1. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation

-----

**Document Version**: 1.0 
**Last Updated**: December 2024 
**Project Repository**: github.com/The-MAST-project/MAST_gui
