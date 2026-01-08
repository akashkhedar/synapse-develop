"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

from django.urls import include, path

from . import api, views
from annotators import assignment_api

app_name = "projects"

# reverse for projects:name
_urlpatterns = [
    path("", views.project_list, name="project-index"),
    path(
        "<int:pk>/settings/",
        views.project_settings,
        name="project-settings",
        kwargs={"sub_path": ""},
    ),
    path(
        "<int:pk>/settings/<sub_path>",
        views.project_settings,
        name="project-settings-anything",
    ),
]

# reverse for projects:api:name
_api_urlpatterns = [
    # CRUD
    path("", api.ProjectListAPI.as_view(), name="project-list"),
    path("<int:pk>/", api.ProjectAPI.as_view(), name="project-detail"),
    path("counts/", api.ProjectCountsListAPI.as_view(), name="project-counts-list"),
    # Get next task
    path("<int:pk>/next/", api.ProjectNextTaskAPI.as_view(), name="project-next"),
    # Label stream history
    path(
        "<int:pk>/label-stream-history/",
        api.LabelStreamHistoryAPI.as_view(),
        name="label-stream-history",
    ),
    # Validate label config in general
    path(
        "validate/", api.LabelConfigValidateAPI.as_view(), name="label-config-validate"
    ),
    # Validate label config for project
    path(
        "<int:pk>/validate/",
        api.ProjectLabelConfigValidateAPI.as_view(),
        name="project-label-config-validate",
    ),
    # Project summary
    path("<int:pk>/summary/", api.ProjectSummaryAPI.as_view(), name="project-summary"),
    # Project summary
    path(
        "<int:pk>/summary/reset/",
        api.ProjectSummaryResetAPI.as_view(),
        name="project-summary-reset",
    ),
    # Project import
    path(
        "<int:pk>/imports/<int:import_pk>/",
        api.ProjectImportAPI.as_view(),
        name="project-imports",
    ),
    # Project reimport
    path(
        "<int:pk>/reimports/<int:reimport_pk>/",
        api.ProjectReimportAPI.as_view(),
        name="project-reimports",
    ),
    # Tasks list for the project: get and destroy
    path(
        "<int:pk>/tasks/", api.ProjectTaskListAPI.as_view(), name="project-tasks-list"
    ),
    # Generate sample task for this project
    path(
        "<int:pk>/sample-task/",
        api.ProjectSampleTask.as_view(),
        name="project-sample-task",
    ),
    # List available model versions
    path(
        "<int:pk>/model-versions/",
        api.ProjectModelVersions.as_view(),
        name="project-model-versions",
    ),
    # List all annotators for project
    path(
        "<int:pk>/annotators/",
        api.ProjectAnnotatorsAPI.as_view(),
        name="project-annotators",
    ),
    # Assignment Management APIs
    path(
        "<int:project_id>/assign-annotators/",
        assignment_api.ProjectAssignAnnotatorsAPI.as_view(),
        name="assign-annotators",
    ),
    path(
        "<int:project_id>/auto-assign/",
        assignment_api.ProjectAutoAssignAPI.as_view(),
        name="auto-assign",
    ),
    path(
        "<int:project_id>/assignment-status/",
        assignment_api.ProjectAssignmentStatusAPI.as_view(),
        name="assignment-status",
    ),
    path(
        "<int:project_id>/assignment-config/",
        assignment_api.ProjectAssignmentConfigAPI.as_view(),
        name="assignment-config",
    ),
    path(
        "<int:project_id>/reassign-tasks/",
        assignment_api.ProjectReassignTasksAPI.as_view(),
        name="reassign-tasks",
    ),
]

_api_urlpatterns_templates = [
    path("", api.TemplateListAPI.as_view(), name="template-list"),
]


urlpatterns = [
    path("projects/", include(_urlpatterns)),
    path("api/projects/", include((_api_urlpatterns, app_name), namespace="api")),
    path(
        "api/templates/",
        include((_api_urlpatterns_templates, app_name), namespace="api-templates"),
    ),
]





