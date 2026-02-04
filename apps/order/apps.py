from django.apps import AppConfig


class OrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.order'

    def ready(self):
        # Import signals to ensure they are registered
        import apps.order.signals  # noqa
