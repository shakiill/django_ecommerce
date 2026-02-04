from django.apps import AppConfig


class EcomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ecom'

    def ready(self):
        import apps.ecom.signals  # noqa
