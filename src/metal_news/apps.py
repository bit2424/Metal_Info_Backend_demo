"""
Django app configuration for Metal News.
"""
from django.apps import AppConfig


class MetalNewsConfig(AppConfig):
    """Configuration for the metal_news app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "metal_news"
    verbose_name = "Metal News"

    def ready(self):
        """Import tasks and signals when the app is ready."""
        # Import tasks to ensure they are registered with Celery
        import metal_news.tasks  # noqa: F401
        # Import signals to ensure they are registered
        import metal_news.signals  # noqa: F401
