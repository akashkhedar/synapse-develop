import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.synapse")
django.setup()

from projects.models import Project

try:
    p = Project.objects.get(id=205)
    print(f"Project ID: {p.id}")
    print(f"Title: {p.title}")
    print("--- LABEL CONFIG ---")
    print(p.label_config)
    print("--------------------")
except Project.DoesNotExist:
    # Try fetching the last project if 205 doesn't exist (ID in URL might be task ID or something else, but screenshot says /projects/205/...)
    # Actually screenshot says projects // New Project #2. URL says ?project=205 in network tab.
    # So 205 is likely correct.
    print("Project 205 not found. Listing last 3 projects:")
    for p in Project.objects.order_by('-id')[:3]:
        print(f"ID: {p.id}, Title: {p.title}")
