"""
Script to fix task assignments for a project where tasks were incorrectly assigned
with only 1 annotator instead of the required overlap.

Usage:
    python manage.py shell < fix_task_assignments.py

Or in Django shell:
    exec(open('fix_task_assignments.py').read())
"""

import os
import django

# Setup Django if running standalone
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "synapse.settings.synapse"
    )
    django.setup()

from django.db.models import Count, Q
from annotators.models import ProjectAssignment, TaskAssignment
from annotators.adaptive_assignment_engine import AdaptiveAssignmentEngine
from projects.models import Project
from tasks.models import Task


def fix_project_assignments(project_id):
    """
    Fix task assignments for a project to ensure each task has the correct
    number of annotators based on the adaptive overlap calculation.
    """
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        print(f"❌ Project {project_id} not found")
        return

    print(f"\n🔧 Fixing assignments for Project {project_id}: {project.title}")

    # Get active annotators
    active_assignments = list(
        ProjectAssignment.objects.filter(project=project, active=True).select_related(
            "annotator", "annotator__user"
        )
    )

    if not active_assignments:
        print("❌ No active annotators for this project")
        return

    annotators = [pa.annotator for pa in active_assignments]
    print(f"📊 Active annotators: {len(annotators)}")
    for a in annotators:
        print(f"   - {a.user.email}")

    # Calculate required overlap
    required_overlap, total_annotators, _ = (
        AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
    )
    print(
        f"📊 Required overlap: {required_overlap} (based on {total_annotators} annotators)"
    )

    # Get tasks that need more assignments
    tasks_needing_fix = (
        Task.objects.filter(project=project)
        .annotate(
            current_assignments=Count(
                "annotator_assignments",
                filter=Q(
                    annotator_assignments__status__in=[
                        "assigned",
                        "in_progress",
                        "completed",
                    ]
                ),
            )
        )
        .filter(current_assignments__lt=required_overlap)
        .order_by("id")
    )

    print(f"📋 Tasks needing more assignments: {tasks_needing_fix.count()}")

    fixed_count = 0

    for task in tasks_needing_fix:
        # Get existing assignments for this task
        existing_annotator_ids = set(
            TaskAssignment.objects.filter(task=task).values_list(
                "annotator_id", flat=True
            )
        )

        needed = required_overlap - len(existing_annotator_ids)

        if needed <= 0:
            continue

        print(
            f"\n  Task {task.id}: has {len(existing_annotator_ids)}, needs {required_overlap}"
        )

        # Assign annotators who haven't been assigned yet
        for annotator in annotators:
            if annotator.id in existing_annotator_ids:
                continue

            if needed <= 0:
                break

            TaskAssignment.objects.create(
                annotator=annotator,
                task=task,
                status="assigned",
                amount_paid=0,
            )
            print(f"    ✅ Added {annotator.user.email}")
            fixed_count += 1
            needed -= 1
            existing_annotator_ids.add(annotator.id)

    print(f"\n✅ Fixed {fixed_count} assignments")
    print(f"   Each task should now have {required_overlap} annotators assigned")


def show_project_status(project_id):
    """Show current assignment status for a project"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        print(f"❌ Project {project_id} not found")
        return

    print(f"\n📊 Project {project_id}: {project.title}")

    # Count by assignment count
    from django.db.models import Count

    tasks_with_counts = (
        Task.objects.filter(project=project)
        .annotate(assignment_count=Count("annotator_assignments"))
        .values("assignment_count")
        .annotate(task_count=Count("id"))
        .order_by("assignment_count")
    )

    print("\nTasks by number of assignments:")
    for row in tasks_with_counts:
        print(f"  {row['assignment_count']} assignments: {row['task_count']} tasks")

    # Show annotator workload
    active_assignments = ProjectAssignment.objects.filter(
        project=project, active=True
    ).select_related("annotator", "annotator__user")

    print("\nAnnotator workload:")
    for pa in active_assignments:
        assigned = TaskAssignment.objects.filter(
            annotator=pa.annotator, task__project=project, status="assigned"
        ).count()
        in_progress = TaskAssignment.objects.filter(
            annotator=pa.annotator, task__project=project, status="in_progress"
        ).count()
        completed = TaskAssignment.objects.filter(
            annotator=pa.annotator, task__project=project, status="completed"
        ).count()
        print(
            f"  {pa.annotator.user.email}: assigned={assigned}, in_progress={in_progress}, completed={completed}"
        )


if __name__ == "__main__":
    # Get project ID from command line or use default
    import sys

    if len(sys.argv) > 1:
        project_id = int(sys.argv[1])
    else:
        # Default to project 87 based on the error logs
        project_id = 87

    print("=" * 60)
    print("Task Assignment Fixer")
    print("=" * 60)

    # Show current status
    show_project_status(project_id)

    # Ask for confirmation
    response = input(f"\n\nFix assignments for project {project_id}? (y/n): ")
    if response.lower() == "y":
        fix_project_assignments(project_id)
        print("\n" + "=" * 60)
        print("After fix:")
        show_project_status(project_id)
    else:
        print("Cancelled")





