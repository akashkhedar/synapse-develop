from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import APIKey

# don't allow token management from admin console
admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API Keys."""
    
    list_display = ['name', 'user', 'organization', 'key_prefix', 'is_active', 'last_used_at', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['name', 'description', 'user__email', 'key_prefix']
    readonly_fields = ['key', 'key_prefix', 'created_at', 'updated_at', 'last_used_at']
    raw_id_fields = ['user', 'organization']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'organization', 'name', 'description')
        }),
        ('Key Details', {
            'fields': ('key', 'key_prefix', 'is_active', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )





