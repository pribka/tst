from django_q.tasks import async_task

from django.db import transaction, IntegrityError
from django.db.models import Q

from rest_framework import exceptions as drf_exceptions

from common.catalogs.models import ContractorProfileModel, ContractorRelationModel

from . import models, notifications


def get_invite(request):
    invite_id = request.data.get('id')
    not_found_exception = drf_exceptions.ValidationError({"message": "Приглашение не найдено."})
    if not invite_id:
        raise not_found_exception
    user = request.user.profile
    i_am_director = list(ContractorProfileModel.objects.filter(
        is_active=True, director=True, user=user
    ).values_list('contractor', flat=True))
    try:
        invite = models.ContractorInviteModel.objects.filter(
            Q(contractor_id__in=i_am_director) | Q(contractor_parent_id__in=i_am_director),
            is_active=True,
            status_id='new',
        ).exclude(
            contractor_owner_id__in=i_am_director
        ).get(
            pk=invite_id
        )
    except models.ContractorInviteModel.DoesNotExist:
        raise not_found_exception
    return invite


def accept_invite(invite: models.ContractorInviteModel):
    with transaction.atomic():
        relation = ContractorRelationModel()
        relation.contractor = invite.contractor
        relation.contractor_parent = invite.contractor_parent
        relation.relation_type = invite.relation_type
        try:
            relation.save()
        except IntegrityError:
            raise drf_exceptions.ValidationError({"message": "Связь между организациями уже существует."})
        invite.status_id = 'approved'
        invite.save(update_fields=('status_id',),)
    async_task(notifications.notify_about_accept_invite, invite)
    return invite


def reject_invite(invite):
    invite.status_id = 'rejected'
    invite.save(update_fields=('status_id',), )
    async_task(notifications.notify_about_reject_invite, invite)
    return invite
