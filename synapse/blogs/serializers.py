from rest_framework import serializers
from .models import BlogPost
from users.serializers import UserSerializer  # Assuming UserSerializer exists

class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    # If you want full author details:
    # author = UserSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'subtitle', 'content', 'cover_image',
            'author', 'author_name',
            'created_at', 'published_at', 'is_published', 'tags'
        ]
        read_only_fields = ['id', 'created_at', 'slug', 'author']
