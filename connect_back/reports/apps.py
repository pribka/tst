from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'

    def ready(self):
        import os
        from django.conf import settings
        report_templates_root = getattr(settings, 'REPORT_TEMPLATES_ROOT', None)
        if report_templates_root and not os.path.exists(report_templates_root):
            os.makedirs(report_templates_root, exist_ok=True)
