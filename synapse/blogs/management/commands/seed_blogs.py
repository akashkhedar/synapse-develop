from django.core.management.base import BaseCommand
from blogs.models import BlogPost
from users.models import User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample blog posts'

    def handle(self, *args, **kwargs):
        # Get a user (admin)
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        self.stdout.write(f'Seeding blogs with author: {user.email}')

        blogs_data = [
            {
                "title": "The Future of Medical AI Annotation",
                "subtitle": "How radiologist-in-the-loop workflows are changing healthcare",
                "content": """
# The Future of Medical AI Annotation

Artificial Intelligence is revolutionizing healthcare, but it relies heavily on high-quality data. In medical imaging, this means annotations must be precise, consistent, and clinically valid.

## The Challenge of scale

Scaling annotation teams while maintaining quality is difficult. Crowdsourcing fails for specialized tasks like tumor segmentation or fracture detection.

## The Synapse Solution

At Synapse, we leverage a network of board-certified radiologists who verify every label. This ensures that your models facilitate better patient outcomes.

![Medical AI](https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=2070)

### Key Benefits
*   HIPAA Compliant
*   SOC 2 Certified
*   Expert Verified
                """,
                "cover_image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=2070",
                "tags": ["AI", "Healthcare", "Radiology"]
            },
            {
                "title": "Scaling Data Pipelines for Pathology",
                "subtitle": "Handling gigapixel whole slide images efficiently",
                "content": """
# Scaling Data Pipelines for Pathology

Digital pathology presents unique challenges due to the massive size of Whole Slide Images (WSIs). A single slide can be several gigabytes.

## Tiling and Streaming

We use advanced tiling strategies to stream image data to our annotators without latency. This allows for rapid segmentation of cells and tissue structures.

![Pathology](https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&q=80&w=2070)

## AI-Assisted Labeling

Our pre-labeling models suggest regions of interest, reducing the time pathologists spend on routine tasks.
                """,
                "cover_image": "https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&q=80&w=2070",
                "tags": ["Pathology", "Big Data", "Engineering"]
            },
            {
                "title": "Securing PHI in the Cloud",
                "subtitle": "Best practices for HIPAA-compliant data handling",
                "content": """
# Securing PHI in the Cloud

Patient trust is paramount. Protecting Protected Health Information (PHI) requires a defense-in-depth strategy.

## Encryption Everywhere

Data is encrypted at rest and in transit. accessible only via secure, audited channels.

![Security](https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?auto=format&fit=crop&q=80&w=2070)

## Role-Based Access Control (RBAC)

Strict RBAC policies ensure that only authorized personnel can access sensitive datasets.
                """,
                "cover_image": "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?auto=format&fit=crop&q=80&w=2070",
                "tags": ["Security", "HIPAA", "Compliance"]
            }
        ]

        for data in blogs_data:
            if not BlogPost.objects.filter(title=data["title"]).exists():
                BlogPost.objects.create(
                    title=data["title"],
                    subtitle=data["subtitle"],
                    content=data["content"],
                    cover_image=data["cover_image"],
                    author=user,
                    is_published=True,
                    published_at=timezone.now(),
                    tags=data["tags"]
                )
                self.stdout.write(self.style.SUCCESS(f'Created blog: {data["title"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Blog already exists: {data["title"]}'))
