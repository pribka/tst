from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from .models import ChangeHistoryModel


def create_initial(instance_id, action_date, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=instance_id,
        action_id='created',
        action_date=action_date,
        description=description,
    )


def create_update_datetime(instance_id, action_date, object_property_id,  before, after, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=instance_id,
        action_id='updated',
        object_property_id=object_property_id,
        before=str(before) if before is not None else '',
        after=str(after) if after is not None else '',
        action_date=action_date,
        description=description,
    )


def create_update_boolean(instance_id, action_date, object_property_id, after,):
    ChangeHistoryModel.objects.create(
        related_object_id=instance_id,
        action_id='updated',
        object_property_id=object_property_id,
        before='Нет' if after else 'Да',
        after='Да' if after else 'Нет',
        action_date=action_date,
    )


def create_update_str(instance_id, action_date, object_property_id, before, after, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=instance_id,
        action_id='updated',
        object_property_id=object_property_id,
        before=before if before is not None else '',
        after=after if after is not None else '',
        action_date=action_date,
        description=description,
    )


def create_update_profile_fk(instance_id, action_date, object_property_id, before_id, after_id, description=''):
    profile_model = apps.get_model('users', 'ProfileModel')
    if before_id:
        try:
            before_instance = profile_model.objects.get(pk=before_id)
            before = before_instance.full_name
            before_pk = before_instance.pk
        except ObjectDoesNotExist:
            before = ''
            before_pk = ''
    else:
        before = ''
        before_pk = ''
    if after_id:
        try:
            after_instance = profile_model.objects.get(pk=after_id)
            after = after_instance.full_name
            after_pk = after_instance.pk
        except ObjectDoesNotExist:
            after = ''
            after_pk = ''
    else:
        after = ''
        after_pk = ''
    ChangeHistoryModel.objects.create(
        related_object_id=instance_id,
        action_id='updated',
        object_property_id=object_property_id,
        before=before,
        after=after,
        before_data=before_pk,
        after_data=after_pk,
        action_date=action_date,
        description=description,
    )


def create_update_catalog_code(instance, code_before, attr_model, attr_name, track_prefix, action_date, description=''):
    if code_before:
        before_id = attr_model.objects.get(code=code_before).pk
    else:
        before_id = None
    after_instance = getattr(instance, attr_name)
    if after_instance:
        after_id = after_instance.pk
    else:
        after_id = None
    create_update_catalog_fk(
        instance.pk,
        action_date,
        f'{track_prefix}__{attr_name}',
        before_id,
        after_id,
        description=description,
    )


def create_update_catalog_fk(related_object_id, action_date, object_property_id, before_id, after_id, description=''):
    base_model = apps.get_model('common', 'BaseModel')
    if before_id:
        try:
            before_instance = base_model.objects.super_get(pk=before_id)
            before = before_instance.name
            before_pk = before_instance.pk
        except ObjectDoesNotExist:
            before = ''
            before_pk = ''
    else:
        before = ''
        before_pk = ''
    if after_id:
        try:
            after_instance = base_model.objects.super_get(pk=after_id)
            after = after_instance.name
            after_pk = after_instance.pk
        except ObjectDoesNotExist:
            after = ''
            after_pk = ''
    else:
        after = ''
        after_pk = ''
    ChangeHistoryModel.objects.create(
        related_object_id=related_object_id,
        action_id='updated',
        object_property_id=object_property_id,
        before=before,
        after=after,
        before_data=before_pk,
        after_data=after_pk,
        action_date=action_date,
        description=description,
    )


def create_add_m2m(related_object_id, action_date, object_property_id, str_view, pk_set, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=related_object_id,
        action_id='added',
        action_date=action_date,
        object_property_id=object_property_id,
        after=str_view,
        after_data=list(pk_set),
        description=description,
    )


def create_update_m2m(related_object_id, action_date, object_property_id, before_str, after_str, pk_set, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=related_object_id,
        action_id='updated',
        action_date=action_date,
        object_property_id=object_property_id,
        before=before_str,
        after=after_str,
        after_data=list(pk_set),
        description=description,
    )


def create_remove_m2m(related_object_id, action_date, object_property_id, str_view, pk_set, description=''):
    ChangeHistoryModel.objects.create(
        related_object_id=related_object_id,
        action_id='removed',
        action_date=action_date,
        object_property_id=object_property_id,
        before=str_view,
        before_data=list(pk_set),
        description=description,
    )


def create_delete_m2m(related_object_id, action_date, object_property_id, str_view, pk_set):
    ChangeHistoryModel.objects.create(
        related_object_id=related_object_id,
        action_id='deleted',
        action_date=action_date,
        object_property_id=object_property_id,
        before=str_view,
        before_data=list(pk_set)
    )