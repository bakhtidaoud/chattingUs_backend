"""
App configuration for live streaming.
"""

from django.apps import AppConfig


class LiveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live'
    verbose_name = 'Live Streaming'

    def ready(self):
        """Import signals when app is ready."""
        import live.signals
