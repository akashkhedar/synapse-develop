"""Email notification utilities for organization events"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_organization_invite_email(email, organization, inviter, invite_url, request=None):
    """
    Send invitation email to join an organization
    
    Args:
        email: Email address to send invitation to
        organization: Organization instance
        inviter: User instance who sent the invite
        invite_url: Full URL for accepting the invitation
        request: HttpRequest instance (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        logger.info(f"Sending organization invite email to {email} for {organization.title}")
        
        # Email context
        context = {
            'organization': organization,
            'inviter': inviter,
            'invite_url': invite_url,
            'email': email,
            'site_name': getattr(settings, 'SITE_NAME', 'Synapse'),
        }
        
        # Render email templates
        subject = f'{inviter.email} invited you to join {organization.title}'
        html_message = render_to_string('organizations/emails/organization_invite.html', context)
        text_message = render_to_string('organizations/emails/organization_invite.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Organization invite email sent successfully to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send organization invite email to {email}: {e}")
        return False


def send_admin_promotion_email(user, organization, promoted_by):
    """
    Send email to user when they are promoted to admin
    
    Args:
        user: User instance who was promoted
        organization: Organization instance
        promoted_by: User instance who promoted them
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        logger.info(f"Sending admin promotion email to {user.email} for {organization.title}")
        
        # Email context
        context = {
            'user': user,
            'organization': organization,
            'promoted_by': promoted_by,
            'site_name': getattr(settings, 'SITE_NAME', 'Synapse'),
            'dashboard_url': settings.HOSTNAME.rstrip('/') + '/projects',
        }
        
        # Render email templates
        subject = f'You are now an Admin of {organization.title}'
        html_message = render_to_string('organizations/emails/admin_promotion.html', context)
        text_message = render_to_string('organizations/emails/admin_promotion.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Admin promotion email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin promotion email to {user.email}: {e}")
        return False


def send_project_created_email(project, organization, creator):
    """
    Send email to all organization members when a new project is created
    
    Args:
        project: Project instance that was created
        organization: Organization instance
        creator: User instance who created the project
    
    Returns:
        bool: True if emails were sent successfully
    """
    try:
        logger.info(f"Sending project created emails for {project.title} in {organization.title}")
        
        # Get all active organization members except the creator
        from organizations.models import OrganizationMember
        members = OrganizationMember.objects.filter(
            organization=organization,
            deleted_at__isnull=True
        ).exclude(user=creator).select_related('user')
        
        if not members.exists():
            logger.info("No other members to notify about project creation")
            return True
        
        # Email context
        context = {
            'project': project,
            'organization': organization,
            'creator': creator,
            'site_name': getattr(settings, 'SITE_NAME', 'Synapse'),
            'project_url': settings.HOSTNAME.rstrip('/') + f'/projects/{project.id}',
        }
        
        # Render email templates
        subject = f'New Project Created: {project.title}'
        html_message = render_to_string('organizations/emails/project_created.html', context)
        text_message = render_to_string('organizations/emails/project_created.txt', context)
        
        # Send to all members
        recipient_list = [member.user.email for member in members]
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Project created emails sent to {len(recipient_list)} members")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send project created emails: {e}")
        return False





