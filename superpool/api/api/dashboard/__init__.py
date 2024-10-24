"""
Internal API endpoints consumed by the dashboard frontend.

Architecture flow:
    This Django app -> Dashboard Backend (Django) -> Dashboard Frontend (React)

This module provides API endpoints that are consumed by a separate Django
backend service, which in turn serves the React dashboard frontend. All
requests require API key authentication between the two backend services.
"""