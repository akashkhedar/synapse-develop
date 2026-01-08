# core/rbac.py

from annotators.models import AnnotatorProfile


def resolve_actor(request):
    """
    Resolve the current actor making the request.

    Returns:
        (role, user, annotator_profile, expert_profile)

    role:
        - "annotator"
        - "expert"
        - "client"
        - None (unauthenticated)
    """

    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return None, None, None, None

    # Check for expert profile first (experts can also be annotators)
    expert_profile = None
    try:
        from annotators.models import ExpertProfile

        expert_profile = user.expert_profile
    except:
        pass

    # Check for annotator profile
    annotator_profile = None
    try:
        annotator_profile = user.annotator_profile
    except AnnotatorProfile.DoesNotExist:
        pass

    # Determine primary role
    # If user is staff/admin, they're a client
    if user.is_staff:
        return "client", user, annotator_profile, expert_profile

    # If user has expert profile and is accessing expert endpoints, treat as expert
    if expert_profile and getattr(user, "is_expert", False):
        return "expert", user, annotator_profile, expert_profile

    # If user has annotator profile, treat as annotator
    if annotator_profile:
        return "annotator", user, annotator_profile, expert_profile

    # Default to client
    return "client", user, None, None





