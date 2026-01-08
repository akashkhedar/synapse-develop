from typing import TYPE_CHECKING, Mapping, Optional

from core.redis import start_job_async_or_sync
from django.db.models import QuerySet
from django.utils.functional import cached_property
from projects.functions.utils import get_unique_ids_list

if TYPE_CHECKING:
    from users.models import User


class ProjectMixin:
    def rearrange_overlap_cohort(self):
        """
        Async start rearrange overlap depending on annotation count in tasks
        """
        start_job_async_or_sync(self._rearrange_overlap_cohort)

    def update_tasks_counters_and_is_labeled(self, tasks_queryset, from_scratch=True):
        """
        Async start updating tasks counters and than is_labeled
        :param tasks_queryset: Tasks to update queryset
        :param from_scratch: Skip calculated tasks
        """
        # get only id from queryset to decrease data size in job
        task_ids = get_unique_ids_list(tasks_queryset)
        start_job_async_or_sync(
            self._update_tasks_counters_and_is_labeled,
            task_ids,
            from_scratch=from_scratch,
        )

    def update_tasks_counters_and_task_states(
        self,
        tasks_queryset,
        maximum_annotations_changed,
        overlap_cohort_percentage_changed,
        tasks_number_changed,
        from_scratch=True,
        recalculate_stats_counts: Optional[Mapping[str, int]] = None,
    ):
        """
        Async start updating tasks counters and than rearrange
        :param tasks_queryset: Tasks to update queryset
        :param maximum_annotations_changed: If maximum_annotations param changed
        :param overlap_cohort_percentage_changed: If cohort_percentage param changed
        :param tasks_number_changed: If tasks number changed in project
        :param from_scratch: Skip calculated tasks
        """
        # get only id from queryset to decrease data size in job
        task_ids = get_unique_ids_list(tasks_queryset)
        start_job_async_or_sync(
            self._update_tasks_counters_and_task_states,
            task_ids,
            maximum_annotations_changed,
            overlap_cohort_percentage_changed,
            tasks_number_changed,
            from_scratch=from_scratch,
            recalculate_stats_counts=recalculate_stats_counts,
        )

    def update_tasks_states(
        self,
        maximum_annotations_changed,
        overlap_cohort_percentage_changed,
        tasks_number_changed,
    ):
        """
        Async start updating tasks states after settings change
        :param maximum_annotations_changed: If maximum_annotations param changed
        :param overlap_cohort_percentage_changed: If cohort_percentage param changed
        :param tasks_number_changed: If tasks number changed in project
        """
        start_job_async_or_sync(
            self._update_tasks_states,
            maximum_annotations_changed,
            overlap_cohort_percentage_changed,
            tasks_number_changed,
        )

    def has_permission(self, user):
        """
        Check if user has permission to access this project
        - Superusers always have access
        - Experts must have active ExpertProjectAssignment
        - Annotators must be project members
        - Clients/regular users check org membership
        """
        user.project = self  # link for activity log

        # Superusers always have access
        if user.is_superuser:
            return True

        # Experts must have active project assignment for review
        if hasattr(user, "is_expert") and user.is_expert:
            try:
                from annotators.models import ExpertProjectAssignment

                return ExpertProjectAssignment.objects.filter(
                    expert=user.expert_profile, project=self, is_active=True
                ).exists()
            except Exception:
                return False

        # Annotators must be project members
        if hasattr(user, "is_annotator") and user.is_annotator:
            return self.has_collaborator_enabled(user)

        # For clients and regular users, check organization membership
        # This preserves existing Synapse access control
        if hasattr(self, "organization") and self.organization:
            return self.organization.has_user(user)

        # If no organization, allow access (for standalone projects)
        return True

    def _can_use_overlap(self):
        """
        Returns if we can use overlap for is_labeled calculation
        :return:
        """
        return True

    @cached_property
    def all_members(self) -> QuerySet["User"]:
        """
        Returns all users of project
        :return: QuerySet[User]
        """
        from users.models import User

        return User.objects.filter(
            id__in=self.organization.members.values_list("user__id")
        )





