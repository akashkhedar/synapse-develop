from rest_framework import viewsets, permissions, filters
from .models import BlogPost
from .serializers import BlogPostSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'tags']

    def get_queryset(self):
        if self.request.user.is_staff:
            return BlogPost.objects.all()
        return BlogPost.objects.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
