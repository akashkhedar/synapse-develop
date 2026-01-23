import logging
from .models import SecurityAuditLog

logger = logging.getLogger(__name__)

def log_audit_event(user, log_type, summary, payload=None, ip_address=None, actor=None):
    """
    Helper to log a SecurityAuditLog entry.
    
    Args:
        user: The user associated with the event (e.g., the viewer).
        log_type: One of SecurityAuditLog.LOG_TYPES (e.g., 'access', 'action').
        summary: Human-readable summary.
        payload: Dict of data to be encrypted/stored.
        ip_address: IP address of the request.
        actor: Optional different user who performed the action (default: None).
    """
    if payload is None:
        payload = {}
        
    try:
        log = SecurityAuditLog(
            log_type=log_type,
            user=user,
            actor=actor,
            summary=summary,
            ip_address=ip_address
        )
        log.set_payload(payload)
        log.save()
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
