from projects.models import Project
from annotators.models import ProjectAssignment, TaskAssignment, AnnotatorProfile
from users.models import User
from django.db.models import Count, F

def fix_counters():
    email = "noreply.synapse.ai@gmail.com"
    project_id = 560
    
    try:
        user = User.objects.get(email=email)
        annotator = user.annotator_profile
        project = Project.objects.get(id=project_id)
        
        # Calculate actual assignments
        actual_count = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project
        ).count()
        
        print(f"Actual Task Assignments: {actual_count}")
        
        # Update ProjectAssignment counter
        pa = ProjectAssignment.objects.get(project=project, annotator=annotator)
        print(f"Current Counter value: {pa.assigned_tasks}")
        
        if pa.assigned_tasks != actual_count:
            pa.assigned_tasks = actual_count
            pa.save()
            print(f"✅ Updated ProjectAssignment counter to {actual_count}")
        else:
            print("Counter is already correct.")
            
    except Exception as e:
        print(f"Error: {e}")

fix_counters()
