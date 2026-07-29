"""
Utility views for HTMX endpoints and common functionality.
"""

from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from common.mast_logging import get_logger

logger = get_logger(__name__)
