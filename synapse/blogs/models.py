from django.db import models
from django.conf import settings
from django.utils.text import slugify

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    content = models.TextField(help_text="Markdown content")
    cover_image = models.URLField(blank=True, null=True, help_text="URL to cover image")
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_posts")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    
    tags = models.JSONField(default=list, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']
