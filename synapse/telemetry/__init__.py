"""
Telemetry App - Behavioral Surveillance System

This app provides:
- TelemetryEvent model for storing user behavior signals
- UserRiskProfile for tracking cumulative risk scores
- API endpoints for event ingestion
- Rule engine for pattern detection
- Action engine for automated responses
"""

default_app_config = "telemetry.apps.TelemetryConfig"
