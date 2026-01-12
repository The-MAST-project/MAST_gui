"""
Utility views for HTMX endpoints and common functionality.
"""
import logging
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('mast.utils.views')
