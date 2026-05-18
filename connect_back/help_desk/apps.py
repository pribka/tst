from django.apps import AppConfig


class HelpDeskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'help_desk'

    def ready(self):
        import help_desk.signals  # noqa
