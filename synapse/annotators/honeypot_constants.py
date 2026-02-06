"""
Honeypot System v2.0 - Constants and Configuration

SYSTEM-CONTROLLED: These values are NOT configurable by clients.
All honeypot injection and evaluation is managed by the platform.
"""

# Pool requirements
MIN_GOLDEN_STANDARDS_PER_PROJECT = 10      # Minimum to enable honeypots
RECOMMENDED_GOLDEN_STANDARDS = 50           # Recommended for variety
MAX_USES_BEFORE_RETIREMENT = 100            # Retire after 100 uses

# Injection rates (system-controlled, NO client override)
INJECTION_RATE = 0.05                       # 5% = 1 honeypot per 20 tasks
MIN_INTERVAL_TASKS = 10                     # Minimum 10 tasks between honeypots
MAX_INTERVAL_TASKS = 30                     # Maximum 30 tasks between honeypots

# Evaluation
DEFAULT_TOLERANCE = 0.85                    # 85% match required to pass
ROLLING_WINDOW_SIZE = 50                    # Rolling accuracy based on last 50 honeypots

# Warning thresholds (based on ROLLING accuracy)
THRESHOLD_HEALTHY = 80                      # 80%+ = good
THRESHOLD_SOFT_WARNING = 70                 # 70-79% = soft warning
THRESHOLD_FORMAL_WARNING = 60               # 60-69% = formal warning
THRESHOLD_FINAL_WARNING = 50                # 50-59% = final warning
THRESHOLD_SUSPENSION = 40                   # <40% = suspension

# Warning cooldowns (prevent spamming warnings)
COOLDOWN_SOFT_WARNING_DAYS = 7
COOLDOWN_FORMAL_WARNING_DAYS = 14
COOLDOWN_FINAL_WARNING_DAYS = 7

# Recovery requirements
RECOVERY_THRESHOLD = 80                     # Must reach 80% rolling accuracy
RECOVERY_WINDOW = 20                        # Based on 20 honeypots after warning


# Compiled config dictionary for easy access
HONEYPOT_CONFIG = {
    # Pool
    'MIN_GOLDEN_STANDARDS_PER_PROJECT': MIN_GOLDEN_STANDARDS_PER_PROJECT,
    'RECOMMENDED_GOLDEN_STANDARDS': RECOMMENDED_GOLDEN_STANDARDS,
    'MAX_USES_BEFORE_RETIREMENT': MAX_USES_BEFORE_RETIREMENT,
    
    # Injection
    'INJECTION_RATE': INJECTION_RATE,
    'MIN_INTERVAL_TASKS': MIN_INTERVAL_TASKS,
    'MAX_INTERVAL_TASKS': MAX_INTERVAL_TASKS,
    
    # Evaluation
    'DEFAULT_TOLERANCE': DEFAULT_TOLERANCE,
    'ROLLING_WINDOW_SIZE': ROLLING_WINDOW_SIZE,
    
    # Thresholds
    'THRESHOLD_HEALTHY': THRESHOLD_HEALTHY,
    'THRESHOLD_SOFT_WARNING': THRESHOLD_SOFT_WARNING,
    'THRESHOLD_FORMAL_WARNING': THRESHOLD_FORMAL_WARNING,
    'THRESHOLD_FINAL_WARNING': THRESHOLD_FINAL_WARNING,
    'THRESHOLD_SUSPENSION': THRESHOLD_SUSPENSION,
    
    # Cooldowns
    'COOLDOWN_SOFT_WARNING_DAYS': COOLDOWN_SOFT_WARNING_DAYS,
    'COOLDOWN_FORMAL_WARNING_DAYS': COOLDOWN_FORMAL_WARNING_DAYS,
    'COOLDOWN_FINAL_WARNING_DAYS': COOLDOWN_FINAL_WARNING_DAYS,
    
    # Recovery
    'RECOVERY_THRESHOLD': RECOVERY_THRESHOLD,
    'RECOVERY_WINDOW': RECOVERY_WINDOW,
}
