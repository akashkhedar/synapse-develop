#!/usr/bin/env python
"""Debug why assignment is not creating any assignments"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, AnnotatorExpertise, ProjectAssignment, TaskAssignment
from annotators.assignment_engine import AssignmentEngine
from tasks.models import Task

print("="*60)
print("Debugging Assignment Engine")
print("="*60)

# Get project
project = Project.objects.get(title='Image Classification Test')
print(f"\nProject: {project.title}")
print(f"Required expertise category: {project.required_expertise_category}")
print(f"Assignment strategy: {project.assignment_strategy}")
print(f"Task count: {project.tasks.count()}")

# Check for matching annotators
print("\n--- Matching Expertise Entries ---")
matching = AnnotatorExpertise.objects.filter(
    category=project.required_expertise_category, 
    status='verified'
)
print(f"Found {matching.count()} matching expertise entries")

for exp in matching:
    annotator = exp.annotator
    print(f"\n  Annotator: {annotator.user.email}")
    print(f"    Status: {annotator.status}")
    print(f"    Trust Level: {annotator.trust_level}")
    
    # Check project assignment exists for this annotator
    pa = ProjectAssignment.objects.filter(project=project, annotator=annotator).first()
    if pa:
        print(f"    ProjectAssignment: active={pa.active}, assigned_tasks={pa.assigned_tasks}")
    else:
        print(f"    -- No ProjectAssignment for this project --")

# Check existing task assignments for this project
print("\n--- Existing Task Assignments ---")
existing_assignments = TaskAssignment.objects.filter(task__project=project)
print(f"Total: {existing_assignments.count()}")

# Check annotator capacities
print("\n--- Annotator Capacities (before distribution) ---")
for exp in matching:
    annotator = exp.annotator
    capacity = AssignmentEngine.check_annotator_capacity(annotator)
    # Get breakdown by project
    all_assignments = TaskAssignment.objects.filter(
        annotator=annotator, 
        status__in=["assigned", "in_progress"]
    )
    print(f"  {annotator.user.email}: current={capacity['current']}, max={capacity['maximum']}, available={capacity['available']}")
    print(f"    Total active assignments across all projects: {all_assignments.count()}")

# Run assignment 
print("\n--- Running AssignmentEngine ---")
print("Calling assign_annotators_to_project...")
result = AssignmentEngine.assign_annotators_to_project(
    project=project,
    required_overlap=project.required_overlap or 1
)
print(f"Result: {result}")

# Check assignments after
print("\n--- Post-Assignment Check ---")
new_assignments = TaskAssignment.objects.filter(task__project=project)
print(f"Total assignments now: {new_assignments.count()}")
