# MAST: Modern API Control for Multi-Aperture Spectroscopy

The *Multiple Aperture Spectroscopic Telescope* (**MAST**) presents a scalable control system managing multiple telescope units for multi-object spectroscopy. Each acquires and tracks targets, feeding light via optical fibers to centralized spectrographs.

Our FastAPI-based centralized control ensures coordinated operations with safety enforcement.

_Architecture highlights_: MongoDB configuration with common/override patterns; capability-based permissions; WebSocket activity notifications; integrated weather and resources monitoring; TOML-based observation plans/tasks/assignments with Pydantic validation.

The system separates concerns:
- Windows IoT units handle individual telescopes
- A Windows machine manages the two spectroscopes
- A Linux controller manages planning, scheduling and operations orchestration (observatory startup/shutdown, safety monitoring, target acquisition, science data acquisition, pipeline)
- The Django/HTMX based web GUI provides multi site access.

_Key technologies_: Python (FastAPI/Django), HTMX, Bootstrap 5 UI, MongoDB, WebSocket for real-time updates. Design emphasizes maintainability through server-side rendering and Pydantic-driven forms.

Deployed at Weizmann Institute with one prototype unit; expansion planned for Neot Smadar with 20 production units supporting time-domain astronomy and transient surveys.