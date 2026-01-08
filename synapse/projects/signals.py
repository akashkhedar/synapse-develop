from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, m2m_changed
import logging

logger = logging.getLogger(__name__)


class ProjectSignals:
    """
    Signals for project: implements observer pattern for custom signals.
    Example:

    # publisher
    ProjectSignals.my_signal.send(sender=self, project=project)

    # observer
    @receiver(ProjectSignals.my_signal)
    def my_observer(sender, **kwargs):
        ...
    """

    post_label_config_and_import_tasks = Signal()


# ============================================================================
# AUTOMATIC TASK ASSIGNMENT SIGNAL HANDLERS
# ============================================================================


@receiver(post_save, sender="projects.Project")
def auto_assign_on_project_publish(sender, instance, created, **kwargs):
    """
    Automatically assign annotators and tasks when a project is published.

    Triggers when:
    - Project is_published changes from False to True
    - Project has tasks
    """
    from annotators.tasks import trigger_auto_assignment

    # Only trigger if project was just published
    if instance.is_published:
        # Check if we should trigger (avoid repeated triggers)
        if created:
            # New project, wait for tasks to be added
            logger.info(
                f"New project {instance.id} created and published, waiting for tasks"
            )
            return

        # Check if project has tasks
        task_count = instance.tasks.count()
        if task_count == 0:
            logger.info(f"Project {instance.id} has no tasks, skipping auto-assignment")
            return

        # Check if auto-assignment is enabled
        if not getattr(instance, "auto_assign", True):
            logger.info(f"Auto-assignment disabled for project {instance.id}")
            return

        # Check if already has annotators assigned
        from annotators.models import ProjectAssignment

        existing_assignments = ProjectAssignment.objects.filter(
            project=instance, active=True
        ).count()

        if existing_assignments > 0:
            logger.info(
                f"Project {instance.id} already has {existing_assignments} annotators assigned"
            )
            return

        # Trigger async task assignment
        logger.info(
            f"Triggering auto-assignment for project {instance.id} with {task_count} tasks"
        )
        trigger_auto_assignment(instance.id)


@receiver(ProjectSignals.post_label_config_and_import_tasks)
def auto_assign_on_tasks_import(sender, project, **kwargs):
    """
    Automatically assign annotators when tasks are imported to a published project.

    Triggers when:
    - Tasks are imported via API or bulk upload
    - Project is already published
    """
    from annotators.tasks import trigger_auto_assignment

    if not project.is_published:
        logger.info(f"Project {project.id} not published yet, skipping auto-assignment")
        return

    if not getattr(project, "auto_assign", True):
        logger.info(f"Auto-assignment disabled for project {project.id}")
        return

    # Get task count
    task_count = project.tasks.count()
    logger.info(f"Tasks imported to project {project.id}, total tasks: {task_count}")

    # Trigger assignment
    trigger_auto_assignment(project.id)





