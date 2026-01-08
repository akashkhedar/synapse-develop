"""Email verification utilities"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_verification_email(user, token, request=None):
    """
    Send email verification link to user
    
    Args:
        user: User instance
        token: EmailVerificationToken instance
        request: HttpRequest instance (optional, for building absolute URL)
    """
    try:
        print(f"\n{'='*80}")
        print(f"SENDING VERIFICATION EMAIL TO: {user.email}")
        print(f"{'='*80}\n")
        
        # Build verification URL
        verification_path = reverse('verify-email', kwargs={'token': token.token})
        
        if request:
            verification_url = request.build_absolute_uri(verification_path)
        else:
            # Fallback to settings.HOSTNAME
            hostname = settings.HOSTNAME.rstrip('/')
            verification_url = f"{hostname}{verification_path}"
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': 24,
            'site_name': 'Synapse',
        }
        
        # Render email templates
        subject = 'Verify your email address - Synapse'
        html_message = render_to_string('users/emails/verify_email.html', context)
        text_message = render_to_string('users/emails/verify_email.txt', context)
        
        # Send email
        print(f"Email Backend: {settings.EMAIL_BACKEND}")
        print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
        print(f"To Email: {user.email}")
        print(f"Verification URL: {verification_url}\n")
        
        logger.info(f"Attempting to send verification email to {user.email}")
        logger.info(f"Email backend: {settings.EMAIL_BACKEND}")
        logger.info(f"Verification URL: {verification_url}")
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✓ Email sent successfully to {user.email}\n")
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def resend_verification_email(user, request=None):
    """
    Resend verification email to user
    
    Args:
        user: User instance
        request: HttpRequest instance (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    from users.models_verification import EmailVerificationToken
    
    # Invalidate old tokens
    EmailVerificationToken.objects.filter(
        user=user,
        is_used=False
    ).update(is_used=True)
    
    # Create new token
    token = EmailVerificationToken.create_token(user)
    
    # Send email
    return send_verification_email(user, token, request)





