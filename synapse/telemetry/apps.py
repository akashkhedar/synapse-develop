from django.apps import AppConfig


class TelemetryConfig(AppConfig):
    name = "telemetry"
    verbose_name = "Behavioral Telemetry"

    def ready(self):
        # Import signals if needed
        pass
