"""Annotators app for managing annotation workforce"""

from django.apps import AppConfig


class AnnotatorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "annotators"
    verbose_name = "Annotators Management"

    def ready(self):
        """Connect signals when app is ready"""
        from django.db.models.signals import post_save
        from annotators.signals import (
            auto_assign_on_project_update,
            auto_assign_on_task_created,
        )

        # Import models here to avoid circular imports
        try:
            from projects.models import Project
            from tasks.models import Task

            # Connect project signal for when project is published
            post_save.connect(
                auto_assign_on_project_update,
                sender=Project,
                dispatch_uid="annotators_auto_assign_on_project_update",
            )

            # Connect task signal for when tasks are created
            post_save.connect(
                auto_assign_on_task_created,
                sender=Task,
                dispatch_uid="annotators_auto_assign_on_task_created",
            )
        except Exception as e:
            pass  # Models may not be ready during initial migration





