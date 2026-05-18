from django.apps import AppConfig
import os


class EsSearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'es_search'
    path = os.path.dirname(os.path.abspath(__file__))

    def ready(self):
        # Регистрируем все Document классы в django-elasticsearch-dsl registry
        # до запуска management-команд (search_index) и сигналов.
        from . import documents  # noqa: F401
