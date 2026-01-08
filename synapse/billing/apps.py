from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Billing & Payments'
    
    def ready(self):
        # Import signals when app is ready
        from . import signals





