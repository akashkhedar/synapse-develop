"""
Test Script 2: Project Setup
Creates test projects with different configurations.

Run with:
    python manage.py shell < tests/integration/test_02_project_setup.py
"""

import os
import json
import glob

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from organizations.models import Organization
from projects.models import Project
from tasks.models import Task
from annotators.models import ExpertiseCategory, ExpertiseSpecialization

# Get the workspace root (parent of synapse directory)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
IMAGES_DIR = os.path.join(WORKSPACE_ROOT, 'images')

User = get_user_model()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def log_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def log_section(msg):
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{msg}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")


# Label configurations for different project types
LABEL_CONFIGS = {
    'image_classification': '''
<View>
  <Image name="image" value="$image"/>
  <Choices name="choice" toName="image" showInline="true">
    <Choice value="Cat"/>
    <Choice value="Dog"/>
    <Choice value="Bird"/>
    <Choice value="Other"/>
  </Choices>
</View>
''',
    'text_sentiment': '''
<View>
  <Text name="text" value="$text"/>
  <Choices name="sentiment" toName="text">
    <Choice value="Positive"/>
    <Choice value="Negative"/>
    <Choice value="Neutral"/>
  </Choices>
</View>
''',
    'audio_transcription': '''
<View>
  <Audio name="audio" value="$audio"/>
  <TextArea name="transcription" toName="audio" 
            placeholder="Enter transcription..." 
            maxSubmissions="1" editable="true"/>
</View>
''',
}

# Project configurations
def get_image_files(limit=100):
    """Get list of image files from the images directory"""
    if not os.path.exists(IMAGES_DIR):
        log_info(f"Images directory not found: {IMAGES_DIR}")
        return []
    
    images = sorted(glob.glob(os.path.join(IMAGES_DIR, '*.png')))[:limit]
    log_info(f"Found {len(images)} images in {IMAGES_DIR}")
    return images


PROJECTS = [
    {
        'title': 'Image Classification Test',
        'description': 'Test project for image classification with Computer Vision expertise',
        'expertise_category': 'computer-vision',
        'expertise_specialization': None,  # Only require category, not specialization
        'label_config': LABEL_CONFIGS['image_classification'],
        'task_price': Decimal('0.10'),
        'required_overlap': 2,
        'honeypot_enabled': True,
        'honeypot_percentage': 5,
        'task_count': 50,
        'task_template': {'image': '/data/local-files/?d=images/{filename}'},
        'use_real_images': True,
    },
    {
        'title': 'Text Sentiment Analysis',
        'description': 'Test project for sentiment analysis with NLP expertise',
        'expertise_category': 'natural-language-processing',
        'expertise_specialization': None,  # Only require category, not specialization
        'label_config': LABEL_CONFIGS['text_sentiment'],
        'task_price': Decimal('0.15'),
        'required_overlap': 1,
        'honeypot_enabled': True,
        'honeypot_percentage': 5,
        'task_count': 30,
        'task_template': {'text': 'Sample text for sentiment analysis task {i}'},
    },
    {
        'title': 'Audio Transcription Test',
        'description': 'Test project for audio transcription - NO MATCHING ANNOTATORS',
        'expertise_category': 'audiospeech-processing',
        'expertise_specialization': None,  # Only require category, not specialization
        'label_config': LABEL_CONFIGS['audio_transcription'],
        'task_price': Decimal('0.20'),
        'required_overlap': 1,
        'honeypot_enabled': False,
        'honeypot_percentage': 0,
        'task_count': 20,
        'task_template': {'audio': 'https://example.com/audio_{i}.mp3'},
    },
]


def get_admin_user():
    """Get admin user"""
    try:
        return User.objects.get(email='admin@test.com')
    except User.DoesNotExist:
        log_error("Admin user not found. Run test_01_user_setup.py first!")
        return None


def get_organization():
    """Get test organization"""
    try:
        return Organization.objects.get(title='Test Organization')
    except Organization.DoesNotExist:
        log_error("Organization not found. Run test_01_user_setup.py first!")
        return None


@transaction.atomic
def create_project(admin, org, config):
    """Create a project with configuration"""
    
    # Check for existing project
    existing = Project.objects.filter(title=config['title']).first()
    if existing:
        log_info(f"Project already exists: {config['title']} (deleting and recreating)")
        existing.delete()
    
    # Get expertise category and specialization
    category = None
    specialization = None
    
    try:
        category = ExpertiseCategory.objects.get(slug=config['expertise_category'])
    except ExpertiseCategory.DoesNotExist:
        log_error(f"Category not found: {config['expertise_category']}")
    
    if category and config.get('expertise_specialization'):
        try:
            specialization = ExpertiseSpecialization.objects.get(
                category=category,
                slug=config['expertise_specialization']
            )
        except ExpertiseSpecialization.DoesNotExist:
            log_info(f"Specialization not found: {config['expertise_specialization']}, using category only")
    
    # Create project
    project = Project.objects.create(
        title=config['title'],
        description=config['description'],
        organization=org,
        created_by=admin,
        label_config=config['label_config'],
        # Expertise requirements
        expertise_required=True,
        required_expertise_category=category,
        required_expertise_specialization=specialization,
        # Overlap/consensus
        maximum_annotations=config['required_overlap'],
        required_overlap=config['required_overlap'],
        # Honeypot config
        honeypot_enabled=config['honeypot_enabled'],
        honeypot_injection_rate=Decimal(str(config['honeypot_percentage'])) / 100,  # Convert percent to rate
    )
    
    log_success(f"Created project: {config['title']} (ID: {project.id})")
    
    return project


@transaction.atomic
def create_tasks(project, config):
    """Create tasks for a project"""
    
    task_count = config['task_count']
    template = config['task_template']
    use_real_images = config.get('use_real_images', False)
    
    # Get real images if configured
    image_files = []
    if use_real_images:
        image_files = get_image_files(limit=task_count)
        if image_files:
            log_info(f"Using {len(image_files)} real images for tasks")
    
    tasks_created = 0
    for i in range(1, task_count + 1):
        # Generate task data from template
        data = {}
        for key, value in template.items():
            if isinstance(value, str):
                if '{i}' in value:
                    data[key] = value.format(i=i)
                elif '{filename}' in value and use_real_images and image_files:
                    # Use real image file
                    img_idx = (i - 1) % len(image_files)
                    filename = os.path.basename(image_files[img_idx])
                    data[key] = value.format(filename=filename)
                else:
                    data[key] = value
            else:
                data[key] = value
        
        Task.objects.create(
            project=project,
            data=data,
        )
        tasks_created += 1
    
    log_success(f"Created {tasks_created} tasks for: {project.title}")
    
    return tasks_created


def create_honeypot_tasks(project, config):
    """Create honeypot tasks with ground truth"""
    
    if not config['honeypot_enabled']:
        log_info(f"Honeypots disabled for: {project.title}")
        return 0
    
    # Create 5 honeypot tasks per project
    honeypot_count = 5
    honeypots_created = 0
    use_real_images = config.get('use_real_images', False)
    
    # Get real images for honeypots (offset from regular tasks)
    honeypot_images = []
    if use_real_images:
        all_images = get_image_files(limit=config['task_count'] + honeypot_count)
        honeypot_images = all_images[config['task_count']:]  # Use images after regular tasks
    
    for i in range(1, honeypot_count + 1):
        template = config['task_template']
        data = {}
        for key, value in template.items():
            if isinstance(value, str):
                if '{i}' in value:
                    data[key] = value.format(i=f"honeypot_{i}")
                elif '{filename}' in value and use_real_images and honeypot_images:
                    img_idx = (i - 1) % len(honeypot_images)
                    filename = os.path.basename(honeypot_images[img_idx])
                    data[key] = value.format(filename=filename)
                else:
                    data[key] = value
            else:
                data[key] = value
        
        # Create ground truth based on project type
        if 'image' in template:
            ground_truth = [{"type": "choices", "value": {"choices": ["Cat"]}, "from_name": "choice", "to_name": "image"}]
        elif 'text' in template:
            ground_truth = [{"type": "choices", "value": {"choices": ["Positive"]}, "from_name": "sentiment", "to_name": "text"}]
        else:
            ground_truth = []
        
        # Create a regular task first
        task = Task.objects.create(
            project=project,
            data=data,
        )
        
        # Then create the GoldenStandardTask to link the ground truth
        from annotators.models import GoldenStandardTask
        
        GoldenStandardTask.objects.create(
            task=task,
            project=project,
            ground_truth=ground_truth,
            source='admin',
            tolerance=Decimal('0.85'),
        )
        honeypots_created += 1
    
    log_success(f"Created {honeypots_created} honeypot tasks for: {project.title}")
    
    return honeypots_created


def print_project_summary(projects_data):
    """Print summary of created projects"""
    log_section("Projects Summary")
    
    print(f"\n{'Title':<30} {'Category':<25} {'Tasks':<8} {'Overlap':<8} {'Honeypots'}")
    print("-" * 90)
    
    for data in projects_data:
        project = data['project']
        config = data['config']
        print(f"{project.title:<30} {config['expertise_category']:<25} "
              f"{data['tasks']:<8} {config['required_overlap']:<8} "
              f"{'Yes' if config['honeypot_enabled'] else 'No'}")
    
    print("\n")


def run():
    """Main test execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}       SYNAPSE PLATFORM - PROJECT SETUP TEST{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Get prerequisites
    admin = get_admin_user()
    if not admin:
        return False
    
    org = get_organization()
    if not org:
        return False
    
    log_section("Phase 2.1: Creating Projects")
    
    projects_data = []
    
    for config in PROJECTS:
        project = create_project(admin, org, config)
        if project:
            tasks = create_tasks(project, config)
            honeypots = create_honeypot_tasks(project, config)
            
            projects_data.append({
                'project': project,
                'config': config,
                'tasks': tasks,
                'honeypots': honeypots,
            })
    
    print_project_summary(projects_data)
    
    log_section("Project Setup Complete!")
    log_success(f"Created {len(projects_data)} projects with tasks")
    
    # Test expertise matching
    log_section("Phase 2.2: Testing Expertise Requirements")
    
    from annotators.models import AnnotatorProfile, AnnotatorExpertise
    
    for data in projects_data:
        project = data['project']
        config = data['config']
        
        # Find matching annotators
        category = project.required_expertise_category
        if category:
            matching = AnnotatorExpertise.objects.filter(
                category=category,
                status='verified'
            ).count()
            
            if matching > 0:
                log_success(f"{project.title}: {matching} annotators with matching expertise")
            else:
                log_info(f"{project.title}: NO matching annotators (tasks will queue)")
    
    return True


if __name__ == '__main__':
    run()
elif not os.environ.get('SYNAPSE_TEST_IMPORT'):
    # Auto-run when loaded via Django shell (not when imported)
    run()
