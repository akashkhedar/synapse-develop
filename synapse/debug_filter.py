"""Debug script to trace filter_by_requirements step by step"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.db import models
from projects.models import Project
from annotators.models import AnnotatorProfile, AnnotatorExpertise

project = Project.objects.get(title='Image Classification Test')
print(f"Project: {project.title} (ID: {project.id})")
print()

# Starting annotators
annotators = AnnotatorProfile.objects.filter(
    status='approved',
    user__is_active=True,
).select_related("user", "trust_level")
print(f"Base annotators: {annotators.count()}")
for a in annotators:
    print(f"  - {a.user.email} (ID: {a.id})")

# Check minimum trust level
print()
min_trust = getattr(project, "min_trust_level", None)
print(f"min_trust_level: {min_trust}")
if min_trust and min_trust != "new":
    levels_order = ["new", "junior", "regular", "senior", "expert"]
    min_index = levels_order.index(min_trust)
    allowed_levels = levels_order[min_index:]
    print(f"Filtering to allowed levels: {allowed_levels}")
    annotators = annotators.filter(trust_level__level__in=allowed_levels)
    print(f"After trust level filter: {annotators.count()}")
else:
    print("Skipping trust level filter (min is 'new' or None)")

# Filter out suspended or high fraud flags
print()
print("Applying fraud/suspended filter...")
annotators = annotators.filter(
    models.Q(trust_level__isnull=True)
    | models.Q(trust_level__fraud_flags__lt=3, trust_level__is_suspended=False)
)
print(f"After fraud filter: {annotators.count()}")

# Check quality requirements
print()
quality_req = getattr(project, "quality_requirement", 0) or 0
print(f"quality_requirement: {quality_req}")
if quality_req >= 0.95:  # critical quality
    print("Filtering for critical quality...")
    annotators = annotators.filter(
        accuracy_score__gte=95, trust_level__level__in=["senior", "expert"]
    )
    print(f"After critical quality filter: {annotators.count()}")
elif quality_req >= 0.9:  # high quality
    print("Filtering for high quality...")
    annotators = annotators.filter(
        accuracy_score__gte=90,
        trust_level__level__in=["regular", "senior", "expert"],
    )
    print(f"After high quality filter: {annotators.count()}")
else:
    print("Skipping quality filter (quality_requirement < 0.9)")

# Expertise filtering
print()
expertise_required = getattr(project, "expertise_required", False)
required_category = getattr(project, "required_expertise_category", None)
required_specialization = getattr(project, "required_expertise_specialization", None)
print(f"expertise_required: {expertise_required}")
print(f"required_category: {required_category}")
print(f"required_specialization: {required_specialization}")

if expertise_required and (required_category or required_specialization):
    print("Expertise filter enabled!")
    
    expertise_query = AnnotatorExpertise.objects.filter(status='verified')
    print(f"All verified expertise: {expertise_query.count()}")
    
    if required_specialization:
        expertise_query = expertise_query.filter(specialization=required_specialization)
        print(f"After specialization filter: {expertise_query.count()}")
    elif required_category:
        expertise_query = expertise_query.filter(category=required_category)
        print(f"After category filter: {expertise_query.count()}")
    
    eligible_annotator_ids = list(expertise_query.values_list('annotator_id', flat=True))
    print(f"Eligible annotator IDs: {eligible_annotator_ids}")
    
    print(f"Annotators before expertise filter: {annotators.count()}")
    annotators = annotators.filter(id__in=eligible_annotator_ids)
    print(f"Annotators after expertise filter: {annotators.count()}")
else:
    print("Expertise filter NOT enabled")

print()
print(f"Final result: {annotators.count()} annotators")
for a in annotators:
    print(f"  - {a.user.email}")
