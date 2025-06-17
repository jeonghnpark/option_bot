from django.apps import AppConfig


class ApiAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api_auth"

    def ready(self):
        from .auth import api_manager

        api_manager.initialize()
