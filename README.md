# MAST_gui - Django Web Interface for MAST Control System

**MASTers of Spectra** - Web-based control and monitoring interface for the Multiple Aperture Spectroscopic Telescope.

## Features

- 🌍 Multi-site support (WIS, NS)
- 📊 Real-time unit status monitoring with traffic light indicators
- ⚙️ Component configuration management (Mount, Camera, Focuser, Stage)
- 📅 Observation plan management
- 🛡️ Safety monitoring integration (Grafana + API)
- 🔐 User authentication (local + social: Google, Facebook, Apple)
- 🔔 WebSocket-based activity notifications
- 🎨 Material Design UI (Mantis-inspired)
- ⚡ HTMX for dynamic updates without page reloads
- 🖼️ JS9 FITS image viewer integration

## Quick Start

## Requirements

- Python 3.12+

### 1. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```

### 4. Create log directory
```bash
sudo mkdir -p /var/log/mast
sudo chown $USER /var/log/mast
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create superuser
```bash
python manage.py createsuperuser
```

### 7. Run development server
```bash
python manage.py runserver
```

### 8. Access the application
Open browser to: http://localhost:8000

## Technology Stack

- **Backend**: Django 4.2+
- **Dynamic Updates**: HTMX
- **UI Framework**: Bootstrap 5 with Material Design
- **Client Interactivity**: Alpine.js
- **FITS Viewer**: JS9
- **Real-time**: WebSocket (Django Channels)
- **Database**: MongoDB (via MAST_common) + SQLite (Django internal)
- **Authentication**: django-allauth

## Project Structure

```
MAST_gui/
├── MAST_gui/          # Project settings
├── accounts/          # Authentication & user management
├── dashboard/         # Main dashboard
├── units/             # Unit management & control
├── specs/             # Spectrograph control
├── safety/            # Safety monitoring
├── assignments/       # Task assignments
├── plans/             # Observation plans
├── utils/             # Shared utilities
├── templates/         # Shared templates
└── static/            # CSS, JS, images
```

## API Endpoints

All API endpoints use the prefix: `mast/api/v1/`

- `/mast/api/v1/units/` - Unit management
- `/mast/api/v1/specs/` - Spectrograph control
- `/mast/api/v1/safety/` - Safety data
- `/mast/api/v1/plans/` - Observation plans
- `/mast/api/v1/assignments/` - Task assignments

## Development

See `docs/DEVELOPMENT.md` for development guidelines.

## License

[Your License Here]

## Contact

[Your Contact Information]
