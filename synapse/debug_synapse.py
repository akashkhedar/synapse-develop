import os, sys, django
# Add project root to sys.path
sys.path.append(os.getcwd())
# Add parent directory if needed
sys.path.append(os.path.dirname(os.getcwd()))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from data_import.models import FileUpload
from users.models import User
from django.conf import settings

print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"UPLOAD_DIR: {settings.UPLOAD_DIR}")

# Get the last uploaded file
f = FileUpload.objects.last()
if f:
    print(f"ID: {f.id}") 
    print(f"File Name (DB): {f.file.name}")
    print(f"URL: {f.url}")
    print(f"User: {f.user.email}")
    print(f"Project: {f.project.id}")
    
    # Check permissions
    # We need a user context. Let's use the file owner.
    print(f"Has permission (owner): {f.has_permission(f.user)}")

    if f.url.startswith('/data/upload/'):
        filename = f.url.replace('/data/upload/', '')
        
        # This logic mimics UploadedFileResponse
        constructed_file = settings.UPLOAD_DIR + ("/" if not settings.UPLOAD_DIR.endswith("/") else "") + filename
        print(f"Constructed file path: {constructed_file}")
        
        comparison = (constructed_file == f.file.name)
        print(f"Match? {comparison}")
        
        if not comparison:
            print(f"Mismatch! '{constructed_file}' vs '{f.file.name}'")

        # Query check
        match = FileUpload.objects.filter(file=constructed_file).last()
        print(f"Query search result: {match}")
else:
    print("No files found.")
