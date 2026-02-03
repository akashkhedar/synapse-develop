"""Middleware to enforce annotator test completion"""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class AnnotatorTestCompletionMiddleware(MiddlewareMixin):
    """
    Middleware to redirect annotators who haven't completed their test
    to the skill test page.
    
    Annotators with status 'pending_test' can ONLY access:
    - Test page
    - Logout
    - Static files
    - API endpoints (for test submission)
    """
    
    EXEMPT_URLS = [
        '/annotators/skill-test/',
        '/annotators/test-submit/',
        '/logout',
        '/user/logout',
        '/static/',
        '/media/',
        '/api/',
        '/sw.js',
        '/sw-fallback.js',
        '/favicon.ico',
    ]
    
    TEST_RESTRICTED_STATUSES = ['pending_test']
    
    def process_request(self, request):
        """Check if annotator needs to complete test"""
        
        # Skip middleware if user is not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip for staff/superusers
        if request.user.is_staff or request.user.is_superuser:
            return None
        
        # Only check annotators (not experts or clients)
        if not request.user.is_annotator or request.user.is_expert:
            return None
        
        # Get current status from profile (source of truth)
        try:
            if hasattr(request.user, 'annotator_profile'):
                current_status = request.user.annotator_profile.status
                
                # Sync user status if out of sync
                if request.user.annotator_status != current_status:
                    request.user.annotator_status = current_status
                    request.user.save(update_fields=['annotator_status'])
            else:
                current_status = request.user.annotator_status
        except Exception:
            current_status = request.user.annotator_status
        
        # If annotator hasn't completed test, restrict access
        if current_status in self.TEST_RESTRICTED_STATUSES:
            path = request.path
            
            # Check if current path is exempted
            for exempt_url in self.EXEMPT_URLS:
                if path.startswith(exempt_url):
                    return None
            
            # Redirect to test page
            return redirect('/annotators/skill-test/')
        
        return None
