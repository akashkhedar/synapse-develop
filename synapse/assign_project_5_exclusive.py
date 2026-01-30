from projects.models import Project
from annotators.models import AnnotatorProfile, ProjectAssignment, TaskAssignment
from users.models import User
from tasks.models import Task
from django.db import transaction

def assign_exclusive():
    target_email = "noreply.synapse.ai@gmail.com"
    project_id = 560  # Updated from user context
    
    try:
        # 1. Find Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            print(f"Project ID {project_id} not found. Searching by title...")
            # Try looser search
            project = Project.objects.filter(title__icontains="Project").filter(title__icontains="5").first()
            if not project:
                print("Could not find Project 5 by ID or Title.")
                return

        print(f"--- Processing Project: {project.title} (ID: {project.id}) ---")

        # 2. Find Annotator
        try:
            user = User.objects.get(email=target_email)
            annotator = user.annotator_profile
        except User.DoesNotExist:
            print(f"User {target_email} not found.")
            return
        except AnnotatorProfile.DoesNotExist:
            print(f"User {target_email} has no annotator profile.")
            return

        print(f"Target Annotator: {annotator.user.email}")

        with transaction.atomic():
            # 3. Clear existing project assignments (Pool)
            existing_count = ProjectAssignment.objects.filter(project=project).exclude(annotator=annotator).delete()[0]
            print(f"Removed {existing_count} other annotators from project pool.")

            # Ensure target is in pool
            ProjectAssignment.objects.get_or_create(project=project, annotator=annotator, defaults={'active': True})
            
            # 4. Configure Project for Single Annotator
            project.required_overlap = 1
            project.maximum_annotations = 1
            project.save(update_fields=['required_overlap', 'maximum_annotations'])
            print("Set Project Overlap/Max Annotations to 1.")

            # 5. Assign Tasks
            # Clear existing task assignments for others?
            # User said "only this annotator should get ALL the tasks".
            # Safest to clear all current assignments to ensure clean slate.
            deleted_tasks = TaskAssignment.objects.filter(task__project=project).delete()[0]
            print(f"Cleared {deleted_tasks} existing task assignments.")

            # Assign all tasks to target
            tasks = Task.objects.filter(project=project)
            new_assignments = []
            for task in tasks:
                new_assignments.append(TaskAssignment(
                    annotator=annotator,
                    task=task,
                    status='assigned'
                ))
            
            TaskAssignment.objects.bulk_create(new_assignments)
            print(f"✅ Created {len(new_assignments)} task assignments for {target_email}.")
            
            # Update counters
            Task.objects.filter(project=project).update(target_assignment_count=1)

    except Exception as e:
        print(f"Error: {e}")

assign_exclusive()
