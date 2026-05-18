import requests
import json
import re
from datetime import date, datetime, timedelta
import pytz

from urllib.parse import quote, urlparse, parse_qs
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.dateparse import parse_datetime, parse_date
from django.conf import settings

from rest_framework import exceptions as drf_exceptions

from randomcolor import RandomColor

from common.models import BaseModel
from common.utils import get_datetime_param, html_description_to_plain
from users.models import GoogleTokenModel, GoogleOAuthClientIDsModel

from . import models
from .models import EventCalendarModel, CalendarModel


def _extract_google_drive_file_id(url):
    parsed = urlparse(url or '')
    host = (parsed.netloc or '').lower()
    if 'drive.google.com' not in host:
        return None

    path = parsed.path or ''
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', path)
    if match:
        return match.group(1)

    query_params = parse_qs(parsed.query or '')
    ids = query_params.get('id') or []
    if ids and ids[0]:
        return ids[0]

    return None


def _normalize_external_record_url(record_url, storage_provider):
    normalized_url = (record_url or '').strip()
    if storage_provider != 'google_drive':
        return normalized_url

    file_id = _extract_google_drive_file_id(normalized_url)
    if not file_id:
        return normalized_url

    return f'https://drive.google.com/file/d/{file_id}/preview'


def get_custom_set(request):
    user = request.user.profile

    all_records = models.CalendarCustomSetModel.objects.filter(author=user, is_active=True)
    page_name = request.query_params.get('page_name', '')

    all_records = all_records.filter(page_name=page_name)

    custom_set = all_records.order_by('-created_at').first()
    if not custom_set:
        custom_set = models.CalendarCustomSetModel()
        custom_set.page_name = page_name
        custom_set.personal_calendars = 'all'
        custom_set.group_calendars = 'all'
    return custom_set


def get_calendar_group(related_object) -> models.CalendarGroupModel:
    if not isinstance(related_object, BaseModel):
        raise drf_exceptions.NotFound()
    label = related_object.get_label()
    if label == 'tasks.TaskModel':
        calendar_group_code = getattr(related_object, 'task_type_id', '')
    elif label == 'workgroups.WorkgroupModel' or label == 'consolidation.ConsolidationModel':
        calendar_group_code = 'groups_projects'
    else:
        raise drf_exceptions.NotFound()
    try:
        calendar_group = models.CalendarGroupModel.objects.get(is_active=True, code=calendar_group_code)
    except models.CalendarGroupModel.DoesNotExist:
        raise drf_exceptions.NotFound()
    return calendar_group


def get_personal_calendar_qs(request, personal_calendars):
    user = request.user.profile
    qs = models.EventCalendarModel.objects.filter(
        Q(calendar__author=user) | Q(members=user),
        is_active=True,
        calendar__is_active=True
    ).distinct()
    if personal_calendars == 'all':
        qs = qs.filter(calendar__related_object__isnull=True, calendar__author=user)
    elif not personal_calendars:
        qs = qs.none()
    else:
        qs = qs.filter(
            calendar_id__in=personal_calendars,
            calendar__author=user,
            calendar__related_object__isnull=True,
        )
    qs = filter_event_queryset(qs, request)
    return qs


def get_group_calendar_qs(request, group_calendars):
    if not group_calendars:
        return models.CalendarGroupModel.objects.none()
    if isinstance(group_calendars, str) and group_calendars == 'all':
        group_calendars = list(
            models.CalendarGroupModel.objects.filter(is_active=True).values_list('code', flat=True)
        )
    user = request.user.profile
    lookup = Q(calendar__related_object__isnull=False, calendar__calendar_group_id__in=group_calendars)
    if 'members' in group_calendars:
        lookup = lookup | Q(members=user, calendar__related_object__isnull=True)
    qs = models.EventCalendarModel.objects.filter(
        Q(author=user) | Q(members=user),
        lookup,
        is_active=True,
    )
    qs = filter_event_queryset(qs, request)
    return qs


def filter_event_queryset(queryset, request):
    """Фильтрует queryset событий по временному диапазону и поиску по имени."""
    start = get_datetime_param(request, 'start')
    if start:
        queryset = queryset.filter(Q(start_at__gte=start) | Q(end_at__gte=start))
    end = get_datetime_param(request, 'end')
    if end:
        queryset = queryset.filter(Q(start_at__lte=end) | Q(end_at__lte=end))

    text = request.query_params.get('search')
    if text:
        queryset = queryset.filter(Q(name_ru__icontains=text) | Q(name_kk__icontains=text))

    return queryset


def get_or_create_related_calendar(request, related_object_id, calling_from_frontend=True, author=None):
    """
    Возвращает календарь по related_object_id (проект, задача и т.д.).
    request=None — вызов без запроса (сигналы, фоновый код), проверка прав не выполняется.
    author — при создании нового календаря без request задаёт автора календаря.
    """
    try:
        related_object = BaseModel.objects.super_get(pk=related_object_id)
    except BaseModel.DoesNotExist:
        raise drf_exceptions.NotFound()
    if request is not None and calling_from_frontend and not related_object.get_detail_permission(request):
        raise drf_exceptions.NotFound()
    instance = models.CalendarModel.objects.filter(
        related_object_id=related_object_id
    ).order_by('-created_at').first()
    if not instance:
        calendar_group = get_calendar_group(related_object)
        instance = models.CalendarModel()
        instance.calendar_group = calendar_group
        instance.name = related_object.__str__()
        instance.color = RandomColor().generate()[0]
        instance.related_object = related_object
        if author is not None:
            instance.author = author
    instance.is_active = True
    instance.save()
    return instance


def sync_related_calendar_name(related_object_id):
    """
    Синхронизирует имя всех календарей, связанных с объектом,
    используя его строковое представление (как при создании календаря).
    """
    if not related_object_id:
        return
    try:
        related_object = BaseModel.objects.super_get(pk=related_object_id)
    except BaseModel.DoesNotExist:
        return
    models.CalendarModel.objects.filter(
        related_object_id=related_object_id
    ).update(name=str(related_object))


def get_or_create_personal_calendar(author):
    """Возвращает первый личный календарь пользователя. Создаёт календарь при отсутствии."""
    calendar = models.CalendarModel.objects.filter(
        author=author,
        related_object__isnull=True,
        is_active=True,
    ).order_by('created_at').first()
    if not calendar:
        calendar = models.CalendarModel.objects.create(
            author=author,
            name=author.full_name,
            color=RandomColor().generate()[0],
        )
    return calendar


def create_calendar_event_for_meeting(meeting, request=None):
    """
    Создаёт событие календаря для собрания (при создании собрания).
    Календарь: проект (если meeting.project_id) или личный автора.
    """
    if meeting.project_id:
        calendar = get_or_create_related_calendar(
            request, meeting.project_id,
            calling_from_frontend=(request is not None),
            author=meeting.author if request is None else None,
        )
    else:
        calendar = get_or_create_personal_calendar(meeting.author)
    start_at = meeting.date_begin
    end_at = start_at + timedelta(minutes=meeting.duration)
    notify_at = start_at - timedelta(minutes=30)
    members_list = list(meeting.members.all())
    from .serializers import EventCalendarModelCreateSerializer
    serializer = EventCalendarModelCreateSerializer(
        context={
            'request': request,
            'author': meeting.author,
            'from_meeting': True,
        }
    )
    validated_data = {
        'calendar': calendar,
        'meeting': meeting,
        'name': meeting.name,
        'description': meeting.description or '',
        'start_at': start_at,
        'end_at': end_at,
        'notify_at': notify_at,
        'event_type_id': 'meeting',
        'privacy_id': 'public',
        'color': calendar.color,
        'members': members_list,
    }
    event = serializer.create(validated_data)
    return event


def get_project_from_calendar(calendar):
    """Возвращает проект (WorkgroupModel) по календарю, если календарь привязан к проекту; иначе None."""
    from bpms.workgroups.models import WorkgroupModel
    if not calendar.related_object_id:
        return None
    related = calendar.related_object
    if related is None:
        return None
    obj = related.original_object
    if isinstance(obj, WorkgroupModel):
        return obj
    return None


def create_meeting_for_calendar_event(event, request=None):
    """Создаёт связанное собрание для существующего события календаря."""
    from bpms.meetings.serializers import PlannedMeetingCreateSerializer
    from users.models import ProfileModel

    if event.meeting_id is not None:
        raise drf_exceptions.ValidationError('У события уже есть связанное собрание.')

    delta = event.end_at - event.start_at
    duration_minutes = int(delta.total_seconds() / 60)
    project = get_project_from_calendar(event.calendar)

    member_ids = set(event.members.values_list('pk', flat=True))
    member_ids.add(event.author.pk)
    members_data = [
        {'user': ProfileModel.objects.get(pk=uid), 'is_moderator': (uid == event.author.pk)}
        for uid in member_ids
    ]
    validated_data = {
        'name': event.name,
        'description': html_description_to_plain(event.description or ''),
        'date_begin': event.start_at,
        'duration': duration_minutes,
        'project': project,
        'members': members_data,
    }
    serializer = PlannedMeetingCreateSerializer(
        context={'request': request, 'from_event': True},
    )
    with transaction.atomic():
        meeting = serializer.create(validated_data)
        event.meeting = meeting
        event.save(update_fields=['meeting_id'])
    return meeting


def create_external_meeting_record_for_event(
        event,
        record_url=None,
        storage_provider='',
        record_file=None,
        request=None,
):
    """
    Create (or reuse) a meeting for event and add an external meeting record.
    """
    from bpms.meetings import models as meeting_models

    if not record_url and not record_file:
        raise drf_exceptions.ValidationError({'external_meeting_url': _('This field is required.')})
    if record_url and storage_provider not in dict(meeting_models.MeetingRecordsModel.STORAGE_PROVIDER_CHOICES):
        raise drf_exceptions.ValidationError({'external_meeting_storage_provider': _('Invalid value.')})
    normalized_record_url = _normalize_external_record_url(record_url, storage_provider) if record_url else ''
    own_file = bool(record_file)

    with transaction.atomic():
        meeting = event.meeting
        if meeting is None:
            meeting = create_meeting_for_calendar_event(event, request=request)
            event.refresh_from_db(fields=['meeting_id'])
        if own_file:
            from common.serializers import AppFileSerializer

            normalized_record_url = AppFileSerializer(record_file).data.get('path') or ''
            storage_provider = ''

        # Sync meeting members with event members.
        event_member_ids = set(event.members.values_list('id', flat=True))
        event_member_ids.add(event.author_id)
        meeting_member_qs = meeting_models.MeetingMemberModel.objects.filter(meeting=meeting)
        meeting_members_map = {member.user_id: member for member in meeting_member_qs}
        members_to_create = []
        members_to_update = []
        for member_id in event_member_ids:
            member_obj = meeting_members_map.get(member_id)
            if member_obj is None:
                members_to_create.append(
                    meeting_models.MeetingMemberModel(
                        meeting=meeting,
                        user_id=member_id,
                        is_moderator=(member_id == meeting.author_id),
                    )
                )
                continue
            needs_update = False
            if not member_obj.is_active:
                member_obj.is_active = True
                if hasattr(member_obj, 'deleted_at'):
                    member_obj.deleted_at = None
                needs_update = True
            if member_id == meeting.author_id and not member_obj.is_moderator:
                member_obj.is_moderator = True
                needs_update = True
            if needs_update:
                members_to_update.append(member_obj)

        if members_to_create:
            meeting_models.MeetingMemberModel.objects.bulk_create(members_to_create)
        if members_to_update:
            meeting_models.MeetingMemberModel.objects.bulk_update(
                members_to_update,
                ['is_active', 'deleted_at', 'is_moderator'],
            )

        duration_delta = event.end_at - event.start_at
        if duration_delta.total_seconds() < 0:
            duration_delta = timedelta(0)
        duration_minutes = int(duration_delta.total_seconds() / 60)

        meeting_update_fields = []
        if not meeting.is_external:
            meeting.is_external = True
            meeting_update_fields.append('is_external')
        if not meeting.has_record:
            meeting.has_record = True
            meeting_update_fields.append('has_record')
        if meeting.status != 'ended':
            meeting.status = 'ended'
            meeting_update_fields.append('status')
        if meeting.date_begin != event.start_at:
            meeting.date_begin = event.start_at
            meeting_update_fields.append('date_begin')
        if meeting.duration != duration_minutes:
            meeting.duration = duration_minutes
            meeting_update_fields.append('duration')
        if meeting_update_fields:
            meeting.save(update_fields=meeting_update_fields)

        sections_qs = meeting_models.MeetingSectionModel.objects.filter(
            meeting=meeting,
        ).order_by('created_at')
        section = sections_qs.first()
        if section is None:
            section = meeting_models.MeetingSectionModel.objects.create(
                meeting=meeting,
                name=meeting.name,
                status='ended',
                date_start=event.start_at,
                date_end=event.end_at,
                duration=duration_delta,
            )
        else:
            section_update_fields = []
            if not section.is_active:
                section.is_active = True
                section_update_fields.append('is_active')
                if hasattr(section, 'deleted_at'):
                    section.deleted_at = None
                    section_update_fields.append('deleted_at')
            if section.status != 'ended':
                section.status = 'ended'
                section_update_fields.append('status')
            if section.date_start != event.start_at:
                section.date_start = event.start_at
                section_update_fields.append('date_start')
            if section.date_end != event.end_at:
                section.date_end = event.end_at
                section_update_fields.append('date_end')
            if section.duration != duration_delta:
                section.duration = duration_delta
                section_update_fields.append('duration')
            if section.name != meeting.name:
                section.name = meeting.name
                section_update_fields.append('name')
            if section_update_fields:
                section.save(update_fields=section_update_fields)

        # Для внешней встречи оставляем только одну актуальную секцию.
        extra_sections_qs = sections_qs.exclude(pk=section.pk).filter(is_active=True)
        if extra_sections_qs.exists():
            extra_update_kwargs = {'is_active': False}
            if hasattr(meeting_models.MeetingSectionModel, 'deleted_at'):
                extra_update_kwargs['deleted_at'] = timezone.now()
            extra_sections_qs.update(**extra_update_kwargs)

        section_member_qs = meeting_models.MeetingSectionMemberModel.objects.filter(section=section)
        section_members_map = {member.user_id: member for member in section_member_qs}
        target_member_ids = set(meeting.members.values_list('id', flat=True))
        section_members_to_create = []
        section_members_to_update = []
        for member_id in target_member_ids:
            member_obj = section_members_map.get(member_id)
            if member_obj is None:
                section_members_to_create.append(
                    meeting_models.MeetingSectionMemberModel(
                        section=section,
                        user_id=member_id,
                        duration=duration_delta,
                    )
                )
                continue
            needs_update = False
            if not member_obj.is_active:
                member_obj.is_active = True
                if hasattr(member_obj, 'deleted_at'):
                    member_obj.deleted_at = None
                needs_update = True
            if member_obj.duration != duration_delta:
                member_obj.duration = duration_delta
                needs_update = True
            if needs_update:
                section_members_to_update.append(member_obj)

        if section_members_to_create:
            meeting_models.MeetingSectionMemberModel.objects.bulk_create(section_members_to_create)
        if section_members_to_update:
            meeting_models.MeetingSectionMemberModel.objects.bulk_update(
                section_members_to_update,
                ['is_active', 'deleted_at', 'duration'],
            )

        meeting_external_records_qs = meeting_models.MeetingRecordsModel.objects.filter(
            meeting=meeting,
            is_external=True,
        ).order_by('-created_at')
        if own_file:
            existing_record = meeting_models.MeetingRecordsModel.objects.filter(
                meeting=meeting,
                is_external=True,
                own_file=True,
                record_file=record_file,
            ).order_by('-created_at').first()
        else:
            existing_record = meeting_models.MeetingRecordsModel.objects.filter(
                meeting=meeting,
                url=normalized_record_url,
            ).order_by('-created_at').first()
        if existing_record is None:
            existing_record = meeting_external_records_qs.first()

        if existing_record:
            update_fields = []
            if not existing_record.is_active:
                existing_record.is_active = True
                update_fields.append('is_active')
                if hasattr(existing_record, 'deleted_at'):
                    existing_record.deleted_at = None
                    update_fields.append('deleted_at')
            if not existing_record.is_external:
                existing_record.is_external = True
                update_fields.append('is_external')
            if existing_record.own_file != own_file:
                existing_record.own_file = own_file
                update_fields.append('own_file')
            if existing_record.url != normalized_record_url:
                existing_record.url = normalized_record_url
                update_fields.append('url')
            new_record_file_id = record_file.pk if own_file else None
            if existing_record.record_file_id != new_record_file_id:
                existing_record.record_file = record_file if own_file else None
                update_fields.append('record_file')
            if existing_record.storage_provider != storage_provider:
                existing_record.storage_provider = storage_provider
                update_fields.append('storage_provider')
            if existing_record.status != 'done':
                existing_record.status = 'done'
                update_fields.append('status')
            if existing_record.section_id != section.id:
                existing_record.section = section
                update_fields.append('section')
            initial_data = {'source': 'external'}
            if own_file:
                initial_data['record_file_id'] = str(record_file.pk)
            else:
                initial_data['url'] = normalized_record_url
                initial_data['storage_provider'] = storage_provider
            if existing_record.initial_data != initial_data:
                existing_record.initial_data = initial_data
                update_fields.append('initial_data')
            if update_fields:
                existing_record.save(update_fields=update_fields)
            target_record = existing_record
        else:
            target_record = meeting_models.MeetingRecordsModel.objects.create(
                meeting=meeting,
                section=section,
                url=normalized_record_url,
                initial_data=(
                    {
                        'source': 'external',
                        'record_file_id': str(record_file.pk),
                    } if own_file else {
                        'source': 'external',
                        'url': normalized_record_url,
                        'storage_provider': storage_provider,
                    }
                ),
                is_external=True,
                own_file=own_file,
                record_file=record_file if own_file else None,
                storage_provider=storage_provider,
                status='done',
            )

        # Для внешней встречи оставляем только одну актуальную запись.
        extra_records_qs = meeting_models.MeetingRecordsModel.objects.filter(
            meeting=meeting,
            is_external=True,
            is_active=True,
        ).exclude(pk=target_record.pk)
        if extra_records_qs.exists():
            extra_records_update_kwargs = {'is_active': False}
            if hasattr(meeting_models.MeetingRecordsModel, 'deleted_at'):
                extra_records_update_kwargs['deleted_at'] = timezone.now()
            extra_records_qs.update(**extra_records_update_kwargs)

        return target_record


def create_first_personal_calendar(request):
    user = request.user.profile
    with transaction.atomic():
        get_or_create_personal_calendar(user)
        custom_set = get_custom_set(request)
        custom_set.personal_calendars = 'all'
        custom_set.save()


def set_sync_for_absent_google_calendar_choices(calendars, external_calendar):
    """
    Снимает галку о синхронизации для календарей, которые пользователь не выбрал
    """
    calendars_to_sync = []
    for google_calendar in calendars:
        calendars_to_sync.append(google_calendar['id'])

    models.CalendarModel.objects.filter(
        external_calendar_type=external_calendar
    ).exclude(external_calendar_id__in=calendars_to_sync).update(synchronize=False)


def create_or_update_google_calendars(calendars, external_calendar):
    for google_calendar in calendars:
        calendar = models.CalendarModel.objects.filter(external_calendar_id=google_calendar['id']).first()
        if calendar:
            calendar.synchronize = True
            calendar.color = google_calendar['backgroundColor']
            calendar.name = google_calendar['summary']
            calendar.is_active = True
            calendar.save()
        else:
            models.CalendarModel.objects.create(
                external_calendar_type=external_calendar,
                external_calendar_id=google_calendar['id'],
                synchronize=True,
                color=google_calendar['backgroundColor'],
                name=google_calendar['summary']
            )


def create_or_update_google_event(google_event=None, calendar_to_sync=None):

    if google_event.get('status') == 'cancelled':
        event = EventCalendarModel.objects.filter(external_calendar_event_id=google_event.get('id')).first()
        event.is_active = False
        event.synchronized = True
        event.save()
        return

    start_at, end_at = GoogleTokenModel.parse_event_date_time(google_event)
    summary = google_event.get('summary', '')
    description = google_event.get('description', '')

    if calendar_to_sync:
        data = {
            'start_at': start_at,
            'end_at': end_at,
            'name': summary,
            'calendar': calendar_to_sync,
            'external_calendar_event_id': google_event['id'],
            'description': description,
            'synchronized': True,
        }

        event = EventCalendarModel.objects.filter(external_calendar_event_id=data['external_calendar_event_id']).first()
        if event:
            for key in data.keys():
                setattr(event, key, data[key])
            event.save()
        else:
            EventCalendarModel.objects.create(
                **data
            )


def get_google_events_query_params(next_page_token=None,
                                   next_sync_token=None,
                                   max_results=250):
    query_params = {}
    # https://developers.google.com/calendar/api/v3/reference/events/list?hl=en
    # По умолчанию гугл дает 250 записей. Максимум 2500.
    query_params['maxResults'] = max_results
    query_params['singleEvents'] = True

    if next_page_token:
        query_params['pageToken'] = next_page_token
    if next_sync_token:
        query_params['syncToken'] = next_sync_token

    return query_params


def get_google_events(calendar_to_sync, next_page_token=None, next_sync_token=None, headers=None):
    """
    При частичной синхронизации и первоначальной синхронизации рекомендуется использовать одинаковые параметры запроса
    во избежание неопределенного поведения. Для более подробной информации читать про параметр syncToken на странице
    https://developers.google.com/calendar/api/v3/reference/events/list?hl=en
    """
    # Айдишники Google календаря наподобие en.kz#holiday@group.v.calendar.google.com должны быть закодированы
    encoded_id = quote(calendar_to_sync.external_calendar_id)

    params = get_google_events_query_params(next_sync_token=next_sync_token, next_page_token=next_page_token)
    resp = requests.get(f"https://www.googleapis.com/calendar/v3/calendars/{encoded_id}/events",
                        headers=headers,
                        params=params)

    return json.loads(resp.text)


def sync_events_from_google_calendars(calendars=None, profile=None):
    """
    Нужно вызывать после синхронизации календарей.

    Часть кода списано с 1С Управление небольшой фирмой ОбщийМодуль.ОбменСGoogle.ЗагрузитьДанныеGoogleCalendar
    Материалы про nextPageToken и nextSyncToken:
     https://developers.google.com/calendar/api/v3/reference/events/list?hl=en
     https://developers.google.com/calendar/api/guides/sync
    """

    # TODO Предусмотреть получение нового токена, если во время синхронизации он устарел
    google_token = GoogleTokenModel.get_token_for_web_client(profile)

    google_token = GoogleTokenModel.update_google_access_token(google_token=google_token)

    headers = {
        "Authorization": f"{google_token.token_type} {google_token.access_token}"
    }
    for google_calendar in calendars:

        if google_calendar['accessRole'] != 'owner':
            # 1С УНФ: ОбщийМодуль.ОбменСGoogle.ЗагрузитьДанныеGoogleCalendar
            continue

        next_page_token = ""

        # В 1С Управление нашей фирмой еще используется счетчик для генерации случайных чисел
        # при определении цвета (по видимости календаря).
        # Счетчик расположен в цикле while вместе с кодом поиска календаря по id.
        # Я вынес поиск календаря на уровень for loop, потому что пока не знаю/не понимаю,
        # где имеет смысл применять счетчик.
        calendar_to_sync = models.CalendarModel.objects.filter(
            is_active=True,
            synchronize=True,
            external_calendar_id=google_calendar['id']).first()
        while next_page_token == "" or next_page_token is not None:

            if not calendar_to_sync:
                break

            response_data = get_google_events(calendar_to_sync,
                                              next_page_token=next_page_token,
                                              next_sync_token=calendar_to_sync.external_calendar_next_sync_token,
                                              headers=headers)
            err = response_data.get("error", None)
            if err is not None and err["code"] == 410:
                # nextSyncToken устарел, делаем запрос без него. Полная синхронизация.
                response_data = get_google_events(calendar_to_sync,
                                                  next_page_token=next_page_token,
                                                  headers=headers)

            if err:
                raise Exception(f'Произошла ошибка синхронизации с Google Calendar:{err["message"]}')

            for google_event in response_data['items']:
                create_or_update_google_event(google_event=google_event, calendar_to_sync=calendar_to_sync)

            next_page_token = response_data.get("nextPageToken", None)

            next_sync_token = response_data.get("nextSyncToken", None)
            if next_sync_token:
                calendar_to_sync.external_calendar_next_sync_token = next_sync_token
                calendar_to_sync.save()

    return calendars


def get_access_users(request):
    if not request:
        return set()
    user = request.user.profile
    my_organizations = user.my_organizations
    from_organizations = set(models.EventCalendarAccessOrganizationModel.objects.filter(
        organization_id__in=my_organizations
    ).values_list('owner', flat=True))
    from_profiles = set(models.EventCalendarAccessProfileModel.objects.filter(
        user=user,
    ).values_list('owner', flat=True))
    from_access = from_organizations | from_profiles
    from_access.add(user.pk)
    return from_access


def get_my_day_event_queryset(request):
    """
    Получает queryset событий для "Моего дня" с применением фильтрации по правам.
    """
    from bpms.tasks.models import TaskModel
    
    # Получаем параметры из запроса
    user_param = request.query_params.get('user')
    project_param = request.query_params.get('project')
    workgroup_param = request.query_params.get('workgroup')
    event_id_param = request.query_params.get('id')
    profile_id = request.user.profile.pk

    # Определяем user_ids
    if user_param:
        user_ids = user_param.split(',')
    else:
        user_ids = [str(profile_id)]
    
    # Базовый queryset по участникам
    qs = models.EventCalendarModel.objects.filter(
        is_active=True,
        calendar__is_active=True,
        members__pk__in=user_ids
    )

    # Собираем related_object_ids из проектов и рабочих групп
    related_object_ids = []
    if project_param:
        project_ids = project_param.split(',')
        related_object_ids.extend(project_ids)
        task_ids_from_projects = TaskModel.objects.filter(
            is_active=True,
            project_id__in=project_ids
        ).values_list('id', flat=True)
        related_object_ids.extend(task_ids_from_projects)

    if workgroup_param:
        workgroup_ids = workgroup_param.split(',')
        related_object_ids.extend(workgroup_ids)
        task_ids_from_workgroups = TaskModel.objects.filter(
            is_active=True,
            workgroup_id__in=workgroup_ids
        ).values_list('id', flat=True)
        related_object_ids.extend(task_ids_from_workgroups)

    if related_object_ids:
        related_object_ids = list(set(related_object_ids))
        qs = qs.filter(calendar__related_object_id__in=related_object_ids)

    # Если явно передан id события — сузим выборку до этого события
    if event_id_param:
        qs = qs.filter(pk=event_id_param)

    qs = qs.distinct().order_by('-start_at', '-created_at')
    
    # Применяем фильтрацию по правам и временному диапазону
    qs = filter_event_queryset(qs, request)
    
    return qs
