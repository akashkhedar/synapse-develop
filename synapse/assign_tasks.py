# Trigger task assignment for project
from annotators.assignment_engine import AssignmentEngine
from projects.models import Project
from annotators.models import AnnotatorProfile

project_id = 15
email = 'azgmxrk@kemail.uk'

print(f"\n{'='*60}")
print(f"Assigning tasks for project {project_id}")
print('='*60 + '\n')

project = Project.objects.get(id=project_id)
annotator = AnnotatorProfile.objects.get(user__email=email)

print(f"Project: {project.title}")
print(f"Total tasks: {project.tasks.count()}")
print(f"Annotator: {email}")
print(f"Trust level: {annotator.trust_level.level} ({annotator.trust_level.multiplier}x)")

# Check current assignment
from annotators.models import TaskAssignment
assignments = TaskAssignment.objects.filter(
    annotator=annotator,
    task__project=project
)

print(f"\nCurrent task assignments: {assignments.count()}")

if assignments.count() == 0:
    print("\nNo tasks assigned yet. Triggering assignment...")
    
    # Call assignment engine
    result = AssignmentEngine.assign_tasks_to_annotators(
        project=project,
        force_reassign=True
    )
    
    print(f"\nAssignment result: {result}")
    
    # Check assignments after
    new_assignments = TaskAssignment.objects.filter(
        annotator=annotator,
        task__project=project
    )
    
    print(f"New task assignments: {new_assignments.count()}")
else:
    print(f"\nTasks already assigned:")
    for i, assignment in enumerate(assignments[:5], 1):
        print(f"  {i}. Task {assignment.task.id} - {assignment.status}")
    if assignments.count() > 5:
        print(f"  ... and {assignments.count() - 5} more")

print('\n' + '='*60 + '\n')
