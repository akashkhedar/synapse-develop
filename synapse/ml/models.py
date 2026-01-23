from django.db import models
from django.conf import settings
from projects.models import Project

class MLModel(models.Model):
    """
    Represents a Machine Learning model architecture/type being trained.
    """
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ml_models')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ModelVersion(models.Model):
    """
    Specific version of a trained model.
    """
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=50) # e.g. "v1.0"
    
    # Path to model artifacts (cloud storage URL)
    artifact_url = models.URLField(blank=True)
    
    is_active = models.BooleanField(default=False, help_text="Is this the currently deployed version?")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model.title} - {self.version_number}"

class ModelTraining(models.Model):
    """
    Tracks a training run.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('training', 'Training'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='training_runs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Metrics
    metrics = models.JSONField(default=dict, help_text="Final metrics like IoU, Accuracy")
    logs = models.TextField(blank=True, help_text="Training logs")

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Run {self.id} ({self.status})"
