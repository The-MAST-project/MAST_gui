# The Multiple Aperture Spectroscopic Telescope (MAST) 

In the following presentation, I will discuss the Multi Aperture Spectroscopic Telescope (MAST) control system, delving into the motivation behind our implementation, system  architecture, scheduling  and observations planning, safety considerations, system integration, and user interfaces.

## 1. System Overview and Motivation

The Multiple Aperture Spectroscopic Telescope (MAST) project addresses the challenge of coordinating multiple autonomous telescope units performing simultaneous multi-object spectroscopy. The system enables efficient survey observations and time-domain astronomy by distributing targets across multiple telescopes feeding light via optical fibers to centralized spectrographs. The web-based control system provides astronomers with tools for observation planning, automated scheduling, real-time monitoring, and integrated safety management.


## 2. Centralized Architecture Philosophy

### 2.1 Hub-Spoke Control Model

MAST implements a centralized control architecture where all operations route through a Linux-based controller (`mast-{site}-control`) rather than allowing direct communication between GUI and individual components. This design choice addresses critical operational requirements:

**Safety Enforcement**: The controller acts as a safety arbiter, validating all operations against current environmental conditions (weather, seeing, enclosure status) before execution. Enclosure opening commands check wind speed and cloud cover; observation requests verify seeing and airmass constraints. This prevents unsafe operations even if scheduler logic or user commands attempt to override safety limits.

**Coordinated Multi-Unit Operations**: Multi-target observations require atomic coordination across units. The controller manages resource allocation, synchronizes unit states, and handles failure recovery. When one unit fails to reach guiding during multi-unit observation, the controller dynamically rebalances the assignment, removing the failed unit while allowing others to proceed if quorum requirements are still met.

**Multi site observations (planned)**: The system accounts for multiple sites for coordinated observation across multiple sites, e.g. for interferometry tasks.

**State Consistency**: The controller maintains authoritative system state for all units, spectrographs, and safety subsystems. This eliminates distributed state synchronization problems and provides single-point-of-truth for scheduling decisions. GUI queries return consistent state snapshots rather than potentially conflicting data from individual components.

**Transaction-Like Semantics**: Multi-unit assignments execute as coordinated transactions. If critical components fail (spectrograph down, insufficient units operational), the controller aborts the entire assignment atomically, returning all plans to schedulable state with merit priority raised for retry.

**Centralized Logging and Audit**: All commands, responses, and state changes flow through the controller for unified logging. This centralized audit trail supports debugging, performance analysis, and compliance requirements. Operators can reconstruct complete execution history from controller logs alone.

**High availability (planned)**: We have future plans for having one additional controller machine (per site) for active/passive availability and failover.

### 2.2 Alternative Approaches Rejected

Direct GUI-to-unit communication was considered but rejected due to:
- **Safety gaps**: No central validation point for weather/seeing constraints
- **Coordination complexity**: Distributed consensus protocols required for multi-unit operations
- **Authentication burden**: 20+ separate authentication contexts vs. single controller authentication
- **Failure handling**: Complex distributed rollback logic for partial failures
- **Operational overhead**: Monitoring and debugging across distributed components



## 3. Observation Planning and Scheduling

### 3.1 Plans: Scientific Goals Abstraction

The system separates scientific intent (Plans) from execution details (Assignments). A Plan defines:
- **Target**: Single celestial object with RA/Dec coordinates
- **Observational requirements**: Instrument (deepspec/highspec), exposure time, camera settings
- **Resource requirements**: Quorum (minimum operational units needed)
- **Constraints**: Optional moon phase/separation, airmass limits, seeing thresholds, time windows
- **Repetition**: Number of observations requested (numbered or indefinite)

Plans are persistent entities surviving execution failures. A failed observation does not invalidate the scientific goal; the plan returns to the schedulable pool for retry under better conditions.

**Example Plan**: "Observe M87 with deepspec, 300s exposure, requiring 3 operational units, only when moon <30% illuminated and >30° from target, airmass <2.0, during December 2024. Repeat 10 times."

### 3.2 Assignments: Execution Bundles

Assignments are transient execution wrappers created by the scheduler, bundling multiple compatible plans that satisfy current conditions. One assignment may include multiple plans targeting different objects, with specific unit-to-target allocations.  The goal is to maximize resources and observe as many targets in parallel as possible.

**Key insight**: Plans are reusable; assignments are single-use. The same plan may participate in multiple assignments over time as conditions permit. Failed plans from one assignment can be rescheduled into different assignments with alternative resource allocations.

**Example Assignment**: "At 22:00, observe Plan A (M87) with units wis:w, ns:2, ns:5; Plan B (NGC1234) with units ns:3, ns:7; Plan C (Crab) with units ns:1, ns:4, ns:8, ns:10, ns:12. All using deepspec, total duration ~15 minutes."

### 3.3 Constraint-Based Scheduling

**Constraint Model**: Plans specify optional constraints treated as hard requirements when present. Missing constraints impose no restrictions (soft). This enables mixed scheduling priorities:
- Time-critical transients: Tight time windows, relaxed quality constraints
- Survey programs: Loose time windows, strict quality constraints (seeing, airmass)
- Calibration observations: Specific conditions (moon phase, sky brightness)

**Scheduler Two-Phase Operation**:

#### Phase 1 - Planning (pre-night)
Scheduler projects entire observing night by:
1. Loading all approved plans from MongoDB
2. Forecasting conditions (moon ephemeris, astronomical twilight, weather predictions)
3. Computing visibility windows for each target (altitude, airmass, moon separation)
4. Grouping compatible plans sharing instrument and constraint overlaps
5. Generating time-ordered assignment proposals optimizing merit, duration, and transitions

This projection provides operators with expected schedule but is not committed execution.

#### Phase 2 - Real-Time Execution
Only one assignment executes at any time. After completion:
1. Update plan states (succeeded/failed) and observations_completed counters
2. Query safety service for current conditions (weather, seeing, sky brightness)
3. Re-evaluate approved plans against actual conditions
4. Create next assignment dynamically based on current state
5. May deviate from projected schedule if conditions changed

This adaptive approach handles unpredictable weather, equipment failures, and seeing variations. If projected assignment targets become unobservable (clouds, high airmass), scheduler selects alternative plans satisfying current conditions.

**Merit-Based Prioritization**: Plans include merit field (1-10) serving as tiebreaker when multiple plans equally satisfy constraints. Merit is user-settable initially and auto-adjusted:
- Increased after failures (prioritizes retry, compensates for lost observing time)
- Decreased for repeatedly scheduled but not executed plans (prevents queue monopolization)
- Boosted for time-critical targets approaching end of visibility window

### 3.4 Resource Allocation and Quorum Management

Each plan specifies quorum: minimum operational units required. During assignment creation, scheduler:
1. Queries unit operational status from controller
2. Allocates units to plans ensuring quorum satisfaction
3. Avoids oversubscription (one unit per plan per assignment)
4. Balances load across available units

During execution, units must reach "Guiding" state within timeout (default 600s). Units failing to guide are removed from operational count. If remaining units ≥ quorum, observation proceeds; if < quorum, plan fails but assignment continues with other plans.

**Example**: Plan requires 5 units, 7 allocated. 2 units timeout during guiding acquisition. Remaining 5 ≥ quorum, observation proceeds. This tolerance handles transient unit issues without aborting entire assignment.



## 4. Safety Integration

### 4.1 Multi-Layered Safety Architecture

Safety monitoring operates at multiple levels:

**Environmental Monitoring**: Dedicated safety service (port 8001) aggregates data from weather stations:
- Wind speed and gusts (anemometer)
- Temperature and humidity (thermohygrometer)
- Cloud cover and sky brightness (cloud sensor)
- Rain detection (rain sensor)
- Seeing estimation (DIMM or image analysis)

Safety service exposes FastAPI endpoints providing real-time sensor readings and historical trends. Grafana dashboard embedded in GUI displays time-series graphs for all parameters.

**Controller-Level Safety Validation**: Before executing any operation affecting hardware:
1. Query safety service for current conditions
2. Check operation against safety limits (e.g., wind speed <30 mph for dome open)
3. Verify plan constraints satisfied (seeing, cloud cover)
4. Abort if any safety check fails, log reason

**Assignment-Level Safety Checks**: When scheduler creates assignment:
1. Forecast conditions for assignment duration (5-20 minutes)
2. Verify all included plans' constraints will be satisfied
3. Only schedule if high confidence in condition stability
4. Monitor conditions during execution, abort if deterioration

**Unit-Level Safety Interlocks**: Each unit implements local safety logic:
- Enclosures close automatically on wind gust >35 mph
- Telescope parks if communication with controller lost >60s
- Camera warming initiated if loss of cooling
- Mount halts motion if encoder errors detected

### 4.2 Enclosure Control Integration

The currently in-progress installation comprizes two rolling-roof enclosures and a proof-of-concept clamshell.

Each of the rolling roofs house ten telescope units and will be controlled by an enclosure controller machine (north and south).

Observational assignments may include units in either one or both enclosures.  Upon start of assignment the site controller may
decide to close an unused enclosure.

**Opening Sequence**:
1. Site controller queries safety service: wind, clouds, rain
2. All checks pass → controller sends "open enclosure" command to enclosure controller(s)
3. Enclosure controller executes motor sequence with position feedback
4. Site controller polls enclosure(s) status until fully open confirmed

**Emergency Closure**:
- Safety service detects unsafe condition (wind gust, rain)
- Broadcasts emergency closure request to controller
- Controller immediately aborts in-progress assignments
- Sends abort an park commands to all currently operating units
- Sends close commands (in parallel) to enclosure controllers
- All assignments fail, plans return to approved state

**Weather Hold**: If conditions marginal (e.g., wind 25 mph, limit 30 mph):
- Scheduler enters "weather hold" mode
- No new assignments created
- In-progress assignment allowed to complete if safe
- GUI displays weather hold status and conditions
- Automatically resumes when conditions improve

### 4.3 Seeing-Based Scheduling

Seeing quality significantly affects observation efficiency:
- Excellent seeing (<1.0"): Schedule high-priority targets requiring sharp images
- Good seeing (1.0-2.0"): Schedule standard survey observations
- Poor seeing (>2.0"): Schedule seeing-insensitive programs or skip observations

Scheduler incorporates seeing forecasts and real-time measurements:
1. Cyclops seeing monitor provides updates every 5-10 minutes
2. Scheduler evaluates plan constraints against current seeing
3. Plans with strict seeing limits (<1.5") deferred if conditions inadequate
4. Flexible plans scheduled during poor seeing, maximizing telescope utilization



## 5. Execution Flow Example

**Complete workflow** from plan creation through successful observation:

### Planning
Astronomer creates plan via GUI:
- Target: Supernova in NGC 4536
- Constraints: Time window (next 7 nights), airmass <2.0, moon >45° separation
- Requirements: 3 units, deepspec, 600s exposure
- Priority: Merit 8 (high, time-critical transient)
- Submits for approval

### Review
PlanManager reviews:
- Verifies target coordinates, checks for scheduling conflicts
- Confirms resource availability (deepspec, sufficient units)
- Approves plan → status changes to "Approved", enters scheduler queue

### Projection
Scheduler runs on-demand planning for the next night:
- Computes target visibility: Rises at 20:45, sets at 03:15, best airmass 22:30
- Checks weather forecast: Clear, winds <15 mph, seeing ~1.5"
- Groups with compatible plans (3 other approved targets)
- Projects assignment at 22:15: 4 plans bundled, 35-minute duration
- Operators see projection in GUI, prepare for observing

### Execution
- **22:10**: Real-time scheduler evaluates conditions (confirm forecast accuracy)
- **22:12**: Creates Assignment ASN_01mm containing 4 plans including supernova
- **22:13**: Allocates units: Supernova → wis:w, ns:2, ns:5; others → remaining units
- **22:14**: Controller verifies safety (weather OK, seeing 1.4"), begins assignment
- **22:14:30**: Units slew to targets, begin acquisition and guiding
- **22:15-22:20**: All units reach guiding state (under 600s timeout)
- **22:20**: Spectrograph activated, all observations start simultaneously
- **22:30**: Supernova exposure completes (600s), data saved
- **22:35**: All observations complete, assignment ends
- **22:36**: Scheduler evaluates next assignment based on updated conditions

### Post-Observation
- Supernova plan: Status updated to "Succeeded", observations_completed = 1
- Data pipeline processes FITS files, stores in `/data/observations/2024-12-15/`
- Plan available for re-observation if astronomer requests follow-up
- MongoDB events record complete timeline: creation, approval, scheduling, execution, success


## 6. User Interface Design for Operations

### 6.1 Dashboard: System Overview

Landing page provides at-a-glance status:
- **Units grid**: 20 unit cards grouped by building, color-coded status (operational/warning/offline/planned)
- **Spectrographs**: deepspec and highspec status indicators
- **Current assignment**: In-progress observation with target names, units allocated, time remaining
- **Weather panel**: Real-time wind speed, cloud cover, seeing, trend arrows
- **Tonight's schedule**: Projected assignments with target names and execution times

### 6.2 Plans Management Interface

Researchers interact with plans through tabbed interface:
- **My Plans**: User's own plans with create/edit/submit buttons
- **All Plans**: System-wide plan list, filterable by status/owner/target
- **Accordion display**: Collapsed view shows target name, coordinates, status, merit; expanded shows complete constraints, assignment history, and execution results

### 6.3 Assignments Monitoring

Operators monitor execution through assignments page:
- **In Progress**: Current assignment with live unit status (acquiring/guiding/observing)
- **Completed**: Recent assignments with per-plan success/failure breakdown
- **Detailed logs**: Drill-down shows unit-by-unit guiding timeline, timeout events, data paths

### 6.4 Safety Dashboard

Dedicated safety page with:
- **Grafana iframe**: Embedded dashboard showing 24-hour weather trends
- **Current conditions**: Large indicators for wind, clouds, seeing with color-coded thresholds
- **Enclosure status**: Dome positions, motor states, recent open/close events
- **Alerts**: Active warnings (approaching wind limits, seeing degradation)


## 7. Data Management and Persistence

### 7.1 Hybrid Storage Strategy

Configuration and operational data use complementary storage:

**MongoDB**: Configuration database for users, groups, sites, units, spectrographs, services. Common/override pattern minimizes duplication. Fast queries support real-time scheduling decisions.

**TOML Files**: Plans and assignments stored as human-readable TOML with ULID identifiers. Files move between status directories as state changes (`/data/plans/{draft,approved,succeeded,completed}/`). Self-contained for archival; complete assignments include all execution metadata.

**MongoDB Events**: Detailed audit trail in events collection. Every significant action (plan created, unit timeout, assignment failed) generates event document. Enables cross-entity queries, analytics, debugging.

### 7.2 Observation Data Pipeline

FITS files saved in structured hierarchy:
```
/data/observations/YYYY-MM-DD/ASN_<ULID>/PLN_<ULID>/
  - science_frame_001.fits
  - science_frame_002.fits
  - calibration_flat.fits
  - metadata.json
```

Assignment TOML links to data directories. Plans maintain list of successful observation data paths. Researchers access data through GUI with direct download or API queries.



## 8. Scalability and Multi-Site Deployment

Current deployment: WIS site (development) with one prototype unit. Planned: NS site (production) with 20 units across two buildings (North, South). Architecture supports:

**Site Independence**: Each site runs dedicated controller with local MongoDB. Sites operate autonomously; network outages don't affect other sites.

**Cross-Site Coordination** (future): Plans can specify multi-site observations. Scheduler at each site publishes available resources; meta-scheduler allocates plans across sites for coordinated campaigns.

**Horizontal Scaling**: Adding units requires configuration update (MongoDB entry, power switch setup, network configuration). No code changes; GUI auto-discovers units from configuration.



## 9. Operational Benefits

The centralized architecture with integrated planning/scheduling delivers measurable advantages:

**Observer Efficiency**: Astronomers submit plans days in advance; scheduler handles nightly execution. No manual queue management or real-time decisions required.

**Telescope Utilization**: Adaptive scheduling maximizes clear-sky usage. Marginal conditions utilize seeing-insensitive programs; excellent seeing reserved for high-priority targets.

**Safety Assurance**: Centralized validation with multi-layered checks prevents unsafe operations. Weather holds and emergency closures protect equipment without human intervention.

**Failure Recovery**: Failed observations automatically retry with adjusted merit. Partial assignment successes (some plans succeed, others fail) preserve completed data while rescheduling failures.

**Audit and Compliance**: Complete event history supports troubleshooting, performance analysis, and publication verification (observers can prove observation dates/conditions).



## 10. Technology Stack

**Backend**:
- Django 4.2+ (web framework)
- FastAPI (control endpoints)
- MongoDB (configuration database)
- Python 3.12+

**Frontend**:
- HTMX (dynamic updates without JavaScript complexity)
- Bootstrap 5 (UI framework)
- Alpine.js (client-side reactivity)
- Grafana (weather/safety visualization)

**Data Formats**:
- TOML (plans, assignments)
- FITS (observation data)
- JSON (API responses, events)

**Networking**:
- HTTP/REST APIs (component communication)
- WebSocket (real-time notifications)
- MongoDB wire protocol (configuration queries)

**Acquisition and guiding**
- Plate solving based acquisition (local astrometry.net) with mount corrections (PlaneWave)
- PHD2 guiding (via JSONRPC)

## 11. Third party coopertion

We were very blessed with cordial and timely cooperations from our vendors and external developers.
- The PlaneWave software team supported and implemented our suggestions for shared-memory between our controlling software and their plate solving solution, drastically cutting down acquisition-correction cycles
- Mr. Andy Gallaso of PHD2 Guiding has and actively is adjusting their software for better JSON-RPC based control

It would be great if we could transfer our acquired images via shared-memory with the local astrometry.net instance, to cut down
file I/O traffic.

## 11. Conclusion

MAST's network-based control system demonstrates that complex multi-telescope coordination can be achieved through centralized architecture emphasizing safety, automated scheduling, and adaptive execution. The separation of persistent plans from transient assignments enables robust failure recovery. Integrated weather/seeing monitoring with controller-enforced safety checks protects equipment while maximizing observing efficiency. The system is near-production-ready for 20-unit deployment supporting time-domain astronomy and spectroscopic surveys.
