"""
Background tasks for annotator assignment using django-rq

These tasks handle:
- Automatic annotator assignment to projects
- Bulk task assignment
- Periodic reassignment of stale tasks
- Workload balancing
"""

import logging
from django_rq import job
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@job("default", timeout=600)
def auto_assign_annotators_to_project(project_id):
    """
    Background job to automatically assign annotators to a project.

    This is the main entry point for automatic assignment with FIXED OVERLAP=3.

    Args:
        project_id: Project ID to assign annotators to
    """
    from projects.models import Project
    from annotators.enhanced_assignment_engine import EnhancedAssignmentEngine

    try:
        project = Project.objects.get(id=project_id)
        logger.info(
            f"🚀 Starting ENHANCED auto-assignment for project {project.id}: {project.title}"
        )
        logger.info(f"🎯 Using FIXED OVERLAP = 3 (hard-coded)")

        # Run the enhanced assignment algorithm
        result = EnhancedAssignmentEngine.auto_assign_project_tasks(project)

        if result.get("success"):
            logger.info(
                f"✅ Enhanced auto-assignment complete for project {project.id}:\n"
                f"  - Total assignments: {result.get('total_assignments', 0)}\n"
                f"  - Fully assigned tasks: {result.get('tasks_fully_assigned', 0)}\n"
                f"  - Partially assigned: {result.get('tasks_partially_assigned', 0)}\n"
                f"  - Waiting: {result.get('tasks_waiting', 0)}"
            )
        else:
            logger.error(
                f"❌ Assignment failed: {result.get('error', 'Unknown error')}"
            )

        return result

    except Project.DoesNotExist:
        logger.error(f"❌ Project {project_id} not found")
        return {"success": False, "error": f"Project {project_id} not found"}
    except Exception as e:
        logger.exception(f"❌ Error in auto-assignment for project {project_id}: {e}")
        return {"success": False, "error": str(e)}


def trigger_auto_assignment(project_id, async_mode=True):
    """
    Trigger automatic assignment for a project.

    Args:
        project_id: Project ID
        async_mode: If True, run as background job. If False, run synchronously.
    """
    if async_mode:
        # Queue the job
        job = auto_assign_annotators_to_project.delay(project_id)
        logger.info(f"📋 Queued auto-assignment job {job.id} for project {project_id}")
        return job
    else:
        # Run synchronously (useful for testing)
        return auto_assign_annotators_to_project(project_id)


@job("default", timeout=300)
def assign_tasks_to_annotator(project_id, annotator_id, batch_size=5):
    """
    Assign a batch of tasks to a specific annotator.

    Args:
        project_id: Project ID
        annotator_id: Annotator profile ID
        batch_size: Number of tasks to assign
    """
    from projects.models import Project
    from annotators.models import AnnotatorProfile
    from annotators.assignment_engine import AssignmentEngine

    try:
        project = Project.objects.get(id=project_id)
        annotator = AnnotatorProfile.objects.get(id=annotator_id)

        logger.info(
            f"Assigning {batch_size} tasks from project {project.id} "
            f"to annotator {annotator.user.email}"
        )

        # Get required overlap
        required_overlap = getattr(project, "required_overlap", 1)

        # Assign tasks
        assignments = AssignmentEngine.bulk_assign_tasks(
            project, annotator, batch_size=batch_size, required_overlap=required_overlap
        )

        logger.info(f"✅ Assigned {len(assignments)} tasks to {annotator.user.email}")

        return {"success": True, "tasks_assigned": len(assignments)}

    except Exception as e:
        logger.exception(f"Error assigning tasks: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def reassign_stale_tasks(project_id):
    """
    Reassign tasks that have been idle for too long.

    Should be run periodically (e.g., daily via cron).

    Args:
        project_id: Project ID to check for stale tasks
    """
    from projects.models import Project
    from annotators.assignment_engine import AssignmentEngine

    try:
        project = Project.objects.get(id=project_id)

        logger.info(f"Checking project {project.id} for stale task assignments")

        reassigned = AssignmentEngine.reassign_incomplete_tasks(project)

        logger.info(f"✅ Reassigned {reassigned} stale tasks in project {project.id}")

        return {"success": True, "reassigned_count": reassigned}

    except Exception as e:
        logger.exception(f"Error reassigning stale tasks: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def reassign_incomplete_tasks_job(project_id):
    """
    Reassign incomplete tasks (< 3 annotators) when capacity becomes available.

    This is called:
    - When new annotators join a project
    - When annotators complete tasks (capacity freed)
    - Periodically to fill assignment gaps

    Args:
        project_id: Project ID to check for incomplete tasks
    """
    from projects.models import Project
    from annotators.enhanced_assignment_engine import EnhancedAssignmentEngine

    try:
        project = Project.objects.get(id=project_id)

        logger.info(f"🔄 Checking project {project.id} for incomplete task assignments")

        result = EnhancedAssignmentEngine.reassign_incomplete_tasks(project)

        logger.info(
            f"✅ Reassignment complete: {result.get('reassigned', 0)} new assignments created, "
            f"{result.get('tasks_completed', 0)} tasks now fully assigned"
        )

        return result

    except Exception as e:
        logger.exception(f"Error reassigning incomplete tasks: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def balance_project_workload(project_id):
    """
    Rebalance task distribution across annotators.

    Should be run periodically to ensure fair workload distribution.

    Args:
        project_id: Project ID to balance
    """
    from projects.models import Project
    from annotators.assignment_engine import AssignmentEngine

    try:
        project = Project.objects.get(id=project_id)

        logger.info(f"Balancing workload for project {project.id}")

        rebalanced = AssignmentEngine.balance_workload(project)

        logger.info(f"✅ Rebalanced {rebalanced} tasks in project {project.id}")

        return {"success": True, "rebalanced_count": rebalanced}

    except Exception as e:
        logger.exception(f"Error balancing workload: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=1800)
def periodic_assignment_maintenance():
    """
    Periodic maintenance task for all active projects.

    Should be run daily via cron or scheduler.

    Tasks performed:
    1. Reassign stale tasks
    2. Balance workload
    3. Assign more tasks to annotators who completed their batch
    """
    from projects.models import Project
    from annotators.models import ProjectAssignment
    from annotators.assignment_engine import AssignmentEngine

    logger.info("🔄 Starting periodic assignment maintenance")

    # Get all active projects with auto-assignment enabled
    active_projects = Project.objects.filter(
        is_published=True,
    ).exclude(
        # Exclude if all tasks are complete
        tasks__is_labeled=False
    )

    results = {
        "projects_processed": 0,
        "tasks_reassigned": 0,
        "tasks_rebalanced": 0,
        "new_assignments": 0,
    }

    for project in active_projects:
        try:
            # Skip if auto-assignment disabled
            if not getattr(project, "auto_assign", True):
                continue

            logger.info(f"Processing project {project.id}: {project.title}")

            # 1. Reassign stale tasks
            reassigned = AssignmentEngine.reassign_incomplete_tasks(project)
            results["tasks_reassigned"] += reassigned

            # 2. Balance workload
            rebalanced = AssignmentEngine.balance_workload(project)
            results["tasks_rebalanced"] += rebalanced

            # 3. Assign more tasks to annotators who need them
            annotators = ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator")

            for assignment in annotators:
                # Check capacity
                capacity = AssignmentEngine.check_annotator_capacity(
                    assignment.annotator
                )

                # If annotator has capacity, assign more tasks
                if capacity["available"] >= 2:
                    # Assign up to 3 new tasks
                    batch_size = min(3, capacity["available"])
                    new_assignments = AssignmentEngine.bulk_assign_tasks(
                        project,
                        assignment.annotator,
                        batch_size=batch_size,
                        required_overlap=getattr(project, "required_overlap", 1),
                    )
                    results["new_assignments"] += len(new_assignments)

            results["projects_processed"] += 1

        except Exception as e:
            logger.exception(f"Error processing project {project.id}: {e}")
            continue

    logger.info(f"✅ Periodic maintenance complete: {results}")

    return results


@job("default", timeout=300)
def notify_annotator_new_tasks(annotator_id, project_id, task_count):
    """
    Send notification to annotator about new task assignments.

    This is a placeholder - implement actual notification logic here.
    Could send email, push notification, or in-app notification.

    Args:
        annotator_id: Annotator profile ID
        project_id: Project ID
        task_count: Number of tasks assigned
    """
    from annotators.models import AnnotatorProfile
    from projects.models import Project

    try:
        annotator = AnnotatorProfile.objects.get(id=annotator_id)
        project = Project.objects.get(id=project_id)

        logger.info(
            f"📧 Notification: {task_count} new tasks assigned to "
            f"{annotator.user.email} for project {project.title}"
        )

        # TODO: Implement actual notification logic
        # - Send email
        # - Create in-app notification
        # - Send push notification

        return {"success": True, "message": "Notification sent"}

    except Exception as e:
        logger.exception(f"Error sending notification: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def process_daily_leaderboard_bonuses():
    """
    Process daily leaderboard bonuses.

    Should be run daily after midnight to distribute bonuses
    for the previous day's top performers.
    """
    from annotators.payment_service import GamificationService

    logger.info("🏆 Processing daily leaderboard bonuses...")

    try:
        result = GamificationService.distribute_daily_leaderboard_bonuses()
        logger.info(f"✅ Leaderboard bonuses distributed: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error distributing leaderboard bonuses: {e}")
        return {"error": str(e)}


@job("default", timeout=300)
def process_task_completion_gamification(task_assignment_id):
    """
    Process gamification effects after task completion.

    This is triggered after an annotator submits an annotation.

    Args:
        task_assignment_id: TaskAssignment ID
    """
    from annotators.models import TaskAssignment
    from annotators.payment_service import GamificationService

    logger.info(f"🎮 Processing gamification for task assignment {task_assignment_id}")

    try:
        task_assignment = TaskAssignment.objects.get(id=task_assignment_id)
        result = GamificationService.process_task_completion(task_assignment)

        logger.info(
            f"✅ Gamification processed for {task_assignment.annotator.user.email}: "
            f"Streak bonus: ₹{result['streak_bonus']}, "
            f"Achievements: {len(result['achievement_bonuses'])}, "
            f"Total bonus: ₹{result['total_bonus']}"
        )

        return {
            "success": True,
            "task_assignment_id": task_assignment_id,
            "bonuses": {
                "streak_bonus": float(result["streak_bonus"]),
                "achievement_count": len(result["achievement_bonuses"]),
                "skill_bonus": float(result["skill_bonus"]),
                "total_bonus": float(result["total_bonus"]),
            },
        }
    except TaskAssignment.DoesNotExist:
        logger.error(f"TaskAssignment {task_assignment_id} not found")
        return {"success": False, "error": "Task assignment not found"}
    except Exception as e:
        logger.exception(f"Error processing gamification: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# EXPERT ASSIGNMENT TASKS
# ============================================================================

@job("default", timeout=600)
def process_expert_review_timeouts(project_id=None):
    """
    Process timed out expert reviews.
    
    Checks for reviews that have exceeded the timeout threshold and:
    - Extends timeout if expert was recently active
    - Releases and reassigns if expert is inactive
    - Marks expert as inactive if absence exceeds threshold
    
    Should be run hourly via scheduler.
    
    Args:
        project_id: Optional project ID to limit processing
    """
    from annotators.expert_assignment_engine import ExpertAssignmentEngine
    
    try:
        logger.info(f"🕐 Processing expert review timeouts (project: {project_id or 'all'})")
        
        if project_id:
            from projects.models import Project
            project = Project.objects.get(id=project_id)
            result = ExpertAssignmentEngine.check_and_process_timeouts(project=project)
        else:
            result = ExpertAssignmentEngine.check_and_process_timeouts()
        
        logger.info(
            f"✅ Expert timeout processing complete: "
            f"{result['extended']} extended, "
            f"{result['released']} released, "
            f"{result['marked_inactive']} marked inactive"
        )
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.exception(f"Error processing expert timeouts: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def process_annotator_assignment_timeouts(project_id=None):
    """
    Process timed out annotator task assignments.
    
    Checks for assignments that have exceeded the timeout threshold and:
    - Extends timeout if annotator was recently active
    - Releases and reassigns if annotator is inactive
    - Marks annotator as inactive if absence exceeds threshold
    
    Should be run hourly via scheduler.
    
    Args:
        project_id: Optional project ID to limit processing
    """
    from annotators.assignment_engine import DynamicAssignmentEngine
    
    try:
        logger.info(f"🕐 Processing annotator assignment timeouts (project: {project_id or 'all'})")
        
        if project_id:
            from projects.models import Project
            project = Project.objects.get(id=project_id)
            DynamicAssignmentEngine.check_and_process_timeouts(project=project)
        else:
            DynamicAssignmentEngine.check_and_process_timeouts()
        
        logger.info("✅ Annotator timeout processing complete")
        
        return {"success": True}
        
    except Exception as e:
        logger.exception(f"Error processing annotator timeouts: {e}")
        return {"success": False, "error": str(e)}


@job("default", timeout=600)
def batch_assign_pending_expert_reviews(project_id=None, max_assignments=50):
    """
    Batch assign pending tasks to available experts.
    
    Called to process tasks that are waiting for expert review.
    Useful when new experts become available.
    
    Args:
        project_id: Optional project ID to limit assignments
        max_assignments: Maximum assignments to make
    """
    from annotators.expert_assignment_engine import ExpertAssignmentEngine
    
    try:
        logger.info(
            f"📋 Batch assigning expert reviews (project: {project_id or 'all'}, "
            f"max: {max_assignments})"
        )
        
        if project_id:
            from projects.models import Project
            project = Project.objects.get(id=project_id)
            result = ExpertAssignmentEngine.batch_assign_pending_tasks(
                project=project,
                max_assignments=max_assignments
            )
        else:
            result = ExpertAssignmentEngine.batch_assign_pending_tasks(
                max_assignments=max_assignments
            )
        
        logger.info(
            f"✅ Expert batch assignment complete: "
            f"{result['assignments_made']} assigned, "
            f"{result.get('skipped', 0)} skipped"
        )
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.exception(f"Error in batch expert assignment: {e}")
        return {"success": False, "error": str(e)}


def trigger_expert_timeout_processing(project_id=None, async_mode=True):
    """
    Trigger expert timeout processing.
    
    Args:
        project_id: Optional project ID
        async_mode: If True, run as background job
    """
    if async_mode:
        job = process_expert_review_timeouts.delay(project_id)
        logger.info(f"📋 Queued expert timeout job {job.id}")
        return job
    else:
        return process_expert_review_timeouts(project_id)


def trigger_annotator_timeout_processing(project_id=None, async_mode=True):
    """
    Trigger annotator timeout processing.
    
    Args:
        project_id: Optional project ID
        async_mode: If True, run as background job
    """
    if async_mode:
        job = process_annotator_assignment_timeouts.delay(project_id)
        logger.info(f"📋 Queued annotator timeout job {job.id}")
        return job
    else:
        return process_annotator_assignment_timeouts(project_id)





