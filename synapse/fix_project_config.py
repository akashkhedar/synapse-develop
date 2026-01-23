import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.synapse")
django.setup()

from projects.models import Project

try:
    p = Project.objects.get(id=205)
    print(f"Current Config for Project {p.id}:")
    print(p.label_config)
    
    new_config = """<View>
  <Dicom name="dicom" value="$image" zoom="true" pan="true" />
  <BrushLabels name="tag" toName="dicom">
    <Label value="Tumor" background="#FF0000" />
    <Label value="Tissue" background="#00FF00" />
  </BrushLabels>
</View>"""
    
    p.label_config = new_config
    p.save()
    print("--------------------")
    print("Config Successfully Updated to Dicom Template.")
    print("--------------------")

except Project.DoesNotExist:
    print("Project 205 not found.")
except Exception as e:
    print(f"Error: {e}")
