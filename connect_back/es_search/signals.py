from django_elasticsearch_dsl.signals import BaseSignalProcessor


class DisableSignalProcessor(BaseSignalProcessor):
    """
    Отключает автоматическое обновление индекса Elasticsearch.
    Используется когда Elasticsearch недоступен.
    """
    
    def handle_save(self, sender, instance, **kwargs):
        """Игнорирует сигнал сохранения"""
        pass
    
    def handle_delete(self, sender, instance, **kwargs):
        """Игнорирует сигнал удаления"""
        pass
