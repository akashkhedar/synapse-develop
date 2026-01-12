# Create trust level for annotator
from decimal import Decimal
from annotators.models import AnnotatorProfile, TrustLevel

email = 'azgmxrk@kemail.uk'
print(f"\nCreating trust level for: {email}\n")

profile = AnnotatorProfile.objects.get(user__email=email)

# Check if trust level exists
trust_level = TrustLevel.objects.filter(annotator=profile).first()

if trust_level:
    print(f"✓ Trust level already exists:")
    print(f"  Level: {trust_level.level}")
    print(f"  Multiplier: {trust_level.multiplier}")
else:
    # Create new trust level with "new" level
    trust_level = TrustLevel.objects.create(
        annotator=profile,
        level='new',
        multiplier=Decimal('0.8'),
        tasks_completed=0,
        accuracy_score=0,
        honeypot_pass_rate=0,
    )
    print(f"✓ Created trust level:")
    print(f"  Level: {trust_level.level}")
    print(f"  Multiplier: {trust_level.multiplier}")
    print(f"  Tasks completed: {trust_level.tasks_completed}")

print(f"\n✓ Trust level configured!\n")
