"""
URL Configuration for Telemetry App
"""

from django.urls import path
from . import api

app_name = "telemetry"

urlpatterns = [
    # Event ingestion endpoint
    path("api/telemetry", api.TelemetryIngestAPI.as_view(), name="ingest"),
    # Risk management endpoints (admin)
    path("api/telemetry/risk/", api.UserRiskAPI.as_view(), name="my-risk"),
    path(
        "api/telemetry/risk/<int:user_id>", api.UserRiskAPI.as_view(), name="user-risk"
    ),
    path("api/telemetry/high-risk", api.HighRiskUsersAPI.as_view(), name="high-risk"),
    path(
        "api/telemetry/unfreeze/<int:user_id>",
        api.UnfreezeUserAPI.as_view(),
        name="unfreeze",
    ),
]
