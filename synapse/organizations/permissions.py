"""
Organization-specific permissions for annotation restrictions
"""

from organizations.models import OrganizationMember
from rest_framework.exceptions import PermissionDenied


def check_annotation_permission(user, task=None, project=None):
    """
    Check if user has permission to annotate based on unified role system.
    Only annotators can create/modify annotations. Clients cannot annotate.

    Args:
        user: User instance
        task: Task instance (optional)
        project: Project instance (optional)

    Returns:
        bool: True if user can annotate, False otherwise

    Raises:
        PermissionDenied: If user is a client attempting to annotate
    """
    # Check if user is a client (clients cannot annotate)
    if hasattr(user, "is_client") and user.is_client:
        raise PermissionDenied(
            "Clients cannot annotate data. "
            "Only annotators can create or modify annotations. "
            "You can manage projects and view results but cannot annotate tasks."
        )

    # Annotators and experts can annotate
    if hasattr(user, "is_annotator") and user.is_annotator:
        return True

    if hasattr(user, "is_expert") and user.is_expert:
        return True

    # Superusers can do anything
    if user.is_superuser:
        return True

    # Default fallback for backward compatibility
    return True


def can_user_annotate(user, task=None, project=None):
    """
    Non-raising version of check_annotation_permission.
    Returns boolean instead of raising exception.

    Args:
        user: User instance
        task: Task instance (optional)
        project: Project instance (optional)

    Returns:
        bool: True if user can annotate, False if they're an org member
    """
    # Get the organization from task/project
    org = None
    if task and hasattr(task, "project"):
        org = task.project.organization
    elif project:
        org = project.organization
    elif hasattr(user, "active_organization"):
        org = user.active_organization

    if not org:
        # If no organization context, allow annotation
        return True

    # Check if user is a member of this organization
    is_org_member = OrganizationMember.objects.filter(
        user=user, organization=org, deleted_at__isnull=True
    ).exists()

    # Organization members CANNOT annotate
    return not is_org_member





