"""Email verification models and utilities for user registration"""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailVerificationToken(models.Model):
    """Token for email verification during user registration"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_token'
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    @classmethod
    def create_token(cls, user, expiry_hours=24):
        """Create a new verification token for a user"""
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if token is still valid"""
        return (
            not self.is_used and
            not self.verified_at and
            timezone.now() < self.expires_at
        )
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_used', 'verified_at'])





