from django.db import models, transaction

from haystack.signals import BaseSignalProcessor
from haystack.exceptions import NotHandled
from haystack.utils import get_identifier

from django_q.tasks import async_task

from .indexes import DjangoQSearchIndex
from .utils import run_task


class DjangoQSignalProcessor(BaseSignalProcessor):

    def setup(self):
        models.signals.post_save.connect(self.enqueue_save)
        models.signals.post_delete.connect(self.enqueue_delete)

    def teardown(self):
        models.signals.post_save.disconnect(self.enqueue_save)
        models.signals.post_delete.disconnect(self.enqueue_delete)

    def enqueue_save(self, sender, instance, **kwargs):
        return self.enqueue('update', instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)

    def enqueue(self, action, instance, sender, **kwargs):
        using_backends = self.connection_router.for_write(instance=instance)

        for using in using_backends:
            try:
                connection = self.connections[using]
                index = connection.get_unified_index().get_index(sender)
            except NotHandled:
                continue  # Check next backend

            if isinstance(index, DjangoQSearchIndex):
                if action == 'update' and not index.should_update(instance):
                    continue
                identifier = get_identifier(instance)
                transaction.on_commit(lambda: async_task(run_task, action, identifier))










