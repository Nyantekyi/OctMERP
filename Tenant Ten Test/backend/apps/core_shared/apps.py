from django.apps import AppConfig


class CoreSharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_shared"
    label = "core_shared"
