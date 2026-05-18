from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from django_q.tasks import async_task

from tags.models import TagRelatedObjectThrough
from .models import CustomerCardModel, ContactPersonModel
from .utils import update_customer_card_index


@receiver(post_save, sender=TagRelatedObjectThrough)
def reindex_on_tag_add(sender, instance, created, **kwargs):
    """
    Переиндексируем CustomerCardModel когда добавляется тег.
    """
    related_object = instance.related_object
    customer_card_ct = ContentType.objects.get_for_model(CustomerCardModel)
    
    if related_object.ct == customer_card_ct:
        try:
            customer_card = CustomerCardModel.objects.get(pk=related_object.pk)
            card_id = str(customer_card.pk)
            transaction.on_commit(
                lambda: async_task(update_customer_card_index, card_id)
            )
        except CustomerCardModel.DoesNotExist:
            pass


@receiver(post_delete, sender=TagRelatedObjectThrough)
def reindex_on_tag_remove(sender, instance, **kwargs):
    """
    Переиндексируем CustomerCardModel когда удаляется тег.
    """
    related_object = instance.related_object
    customer_card_ct = ContentType.objects.get_for_model(CustomerCardModel)
    
    if related_object.ct == customer_card_ct:
        try:
            customer_card = CustomerCardModel.objects.get(pk=related_object.pk)
            card_id = str(customer_card.pk)
            transaction.on_commit(
                lambda: async_task(update_customer_card_index, card_id)
            )
        except CustomerCardModel.DoesNotExist:
            pass


@receiver(post_save, sender=ContactPersonModel)
def reindex_on_contact_person_change(sender, instance, created, **kwargs):
    """
    Переиндексируем CustomerCardModel когда изменяется ContactPersonModel.
    В шаблоне индекса используется contact.name, contact.email, contact.phone.
    """
    if instance.customer_card_id:
        card_id = str(instance.customer_card_id)
        transaction.on_commit(
            lambda: async_task(update_customer_card_index, card_id)
        )


@receiver(post_delete, sender=ContactPersonModel)
def reindex_on_contact_person_delete(sender, instance, **kwargs):
    """
    Переиндексируем CustomerCardModel когда удаляется ContactPersonModel.
    """
    if instance.customer_card_id:
        card_id = str(instance.customer_card_id)
        transaction.on_commit(
            lambda: async_task(update_customer_card_index, card_id)
        )

