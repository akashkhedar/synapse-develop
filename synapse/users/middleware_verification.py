"""Middleware to enforce email verification for authenticated users"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class EmailVerificationMiddleware(MiddlewareMixin):
    """
    Middleware to redirect unverified users to verification pending page
    
    Exempted URLs:
    - Logout
    - Verification pages
    - Static/media files
    - API endpoints
    - Public pages (landing, services, etc.)
    """
    
    EXEMPT_URLS = [
        '/logout',
        '/user/verification-pending',
        '/user/verify-email',
        '/user/resend-verification',
        '/user/login',
        '/user/signup',
        '/user/account',
        '/login',
        '/signup-client',
        '/register-annotator',
        '/static/',
        '/media/',
        '/api/',
        '/admin/',
        '/sw.js',
        '/sw-fallback.js',
        '/favicon.ico',
        '/',  # Landing page
        '/services',
        '/about',
        '/contact',
        '/security',
        '/careers',
        '/blog',
        '/docs',
    ]
    
    def process_request(self, request):
        """Check if user needs email verification"""
        
        # Skip middleware if user is not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip for staff/superusers
        if request.user.is_staff or request.user.is_superuser:
            return None
        
        # Skip for verified users
        if request.user.email_verified:
            return None
        
        # Check if current path is exempted
        path = request.path
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return None
        
        # Redirect to verification pending page
        return redirect(reverse('verification-pending'))





