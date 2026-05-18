import requests
import xmltodict
import uuid
import logging
import json

from django.utils import timezone
from django.db import transaction
from datetime import timedelta, datetime
from requests.exceptions import ConnectionError, Timeout, RequestException

from users.models import ProfileModel
from common.utils import is_uuid
from . import models
from .utils import get_hash_url
from .utils import extract_intents_from_meeting, extract_summary_from_meeting, extract_efficiency_from_meeting, sanitize_intents_speaker_strict, delete_file_physically_and_from_db
from typing import List

logger = logging.getLogger(__name__)

def get_active_meetings(server):
    """Возвращает список active meetingID на сервере BigBlueButton."""
    url = get_hash_url('getMeetings', '', server)
    
    try:
        response = requests.get(url, timeout=10)
        doc = xmltodict.parse(response.text)
        
        if doc['response']['returncode'] != 'SUCCESS':
            return []
            
        meetings_block = doc['response'].get('meetings')
        if not meetings_block:
            return []  # Нет ни одного активного собрания

        meetings = meetings_block.get('meeting', [])

        if isinstance(meetings, dict):
            meetings = [meetings]  # один митинг

        # Вернём список ID всех запущенных конференций
        return [meeting.get('meetingID') for meeting in meetings if 'meetingID' in meeting]
    except (ConnectionError, Timeout, RequestException) as e:
        print(f"ERROR: Connection error to BBB server {server}: {e}")
        return []
    except Exception as e:
        print(f"ERROR: Unexpected error getting meetings from {server}: {e}")
        return []

def get_meeting_attendees(meeting_id, server):
    """Возвращает список attendee участников конференции. Элемент списка - это OrderedDict."""
    # Параметры запроса
    get_params = f"meetingID={meeting_id}"
    url = get_hash_url('getMeetingInfo', get_params, server)
    
    try:
        response = requests.get(url, timeout=10)  # Добавляем таймаут и здесь
        doc = xmltodict.parse(response.text)
        
        if doc['response']['returncode'] != 'SUCCESS':
            return None  # конференция не найдена или ошибка

        attendees_container = doc['response'].get('attendees')
        if not attendees_container or 'attendee' not in attendees_container:
            return []  # нет участников

        attendees = attendees_container['attendee']

        # Один участник — это словарь, а не список
        if isinstance(attendees, dict):
            attendees = [attendees]

        return attendees

    except (ConnectionError, Timeout, RequestException) as e:
        print(f"ERROR: Connection error getting attendees for meeting {meeting_id} from {server}: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error getting attendees for meeting {meeting_id} from {server}: {e}")
        return None

def update_meeting_moderators(meeting_id, attendees, current_member_ids):
    """Обновляет статус модераторов в MeetingMemberModel на основе данных attendees."""
    if not attendees or not current_member_ids:
        return 0
    
    # Создаем словарь userID -> role из attendees
    attendee_roles = {}
    for attendee in attendees:
        user_id = attendee.get('userID')
        role = attendee.get('role')
        if user_id and role and is_uuid(user_id) and user_id in current_member_ids:
            attendee_roles[user_id] = role
    
    if not attendee_roles:
        return 0
    
    # Обновляем статус участников
    with transaction.atomic():
        # Получаем текущих участников встречи
        meeting_members = models.MeetingMemberModel.objects.filter(
            meeting_id=meeting_id,
            user_id__in=attendee_roles.keys()
        )
        
        updated_count = 0
        for member in meeting_members:
            current_role = attendee_roles.get(str(member.user_id))
            expected_moderator_status = current_role == 'MODERATOR'
            
            # Обновляем только если статус не совпадает
            if member.is_moderator != expected_moderator_status:
                member.is_moderator = expected_moderator_status
                member.save(update_fields=['is_moderator'])
                updated_count += 1
        return updated_count


def update_meeting_section_members():
    """Обновляет продолжительность присутствия участников на собрании."""
    servers = models.MeetingServerModel.objects.filter(is_active=True, code='default')
    
    for server in servers:
        try:
            meeting_ids = get_active_meetings(server)
            if not meeting_ids:  # Пропускаем если нет активных встреч или ошибка
                continue
                
            for meeting_id in meeting_ids:
                try:
                    # Получаем текущую секцию
                    section = models.MeetingSectionModel.objects.filter(
                        meeting_id=meeting_id,
                        status='online',
                    ).order_by('-created_at').first()
                    if section:
                        last_check_member_time = section.last_check_member_time
                        now = timezone.now()
                        attendees = get_meeting_attendees(meeting_id, server) or []
                        user_ids = [attendee.get('userID') for attendee in attendees if 'userID' in attendee]
                        # Внешние пользователи имеют userID в виде строки, а не uuid (profile_id), таких отфильтровываем
                        current_member_ids = set([item for item in user_ids if is_uuid(item)] or [])

                        # Оставляем только пользователей, которые найдены у нас в базе
                        current_member_ids = set(str(uid) for uid in ProfileModel.objects.filter(pk__in=current_member_ids).values_list('pk', flat=True))
                        existing_member_ids = set(str(uid) for uid in section.meeting_section_members.values_list('user_id', flat=True))

                        # Обновляем статус модераторов
                        update_meeting_moderators(meeting_id, attendees, current_member_ids)

                        with transaction.atomic():
                            # Создание записей о новых участниках собрания
                            new_member_ids = current_member_ids - existing_member_ids
                            if new_member_ids:
                                list_objects = [models.MeetingSectionMemberModel(
                                    section=section,
                                    user_id=new_member_id,
                                    duration=timedelta(0),
                                    last_check_member_time=now,
                                    ) for new_member_id in new_member_ids]
                                models.MeetingSectionMemberModel.objects.bulk_create(list_objects)

                            # Обновление продолжительности у ранее присутствовавших
                            continuing_member_ids = current_member_ids & existing_member_ids
                            continuing_members = section.meeting_section_members.filter(user_id__in=continuing_member_ids)
                            for continuing_member in continuing_members:
                                if last_check_member_time is not None and continuing_member.last_check_member_time==last_check_member_time:
                                    time_passed = now - last_check_member_time
                                    if continuing_member.duration is None:
                                        continuing_member.duration = time_passed
                                    else:
                                        continuing_member.duration += time_passed
                                    continuing_member.last_check_member_time = now
                                else:
                                    continuing_member.last_check_member_time = now
                            models.MeetingSectionMemberModel.objects.bulk_update(continuing_members, ['duration', 'last_check_member_time',])
                            
                            section.last_check_member_time = now
                            section.save()    

                except Exception as e:
                    print(f"ERROR: Error processing meeting {meeting_id} on server {server}: {e}")
                    continue
                    
        except Exception as e:
            print(f"ERROR: Error processing server {server}: {e}")
            continue
                    

def delete_fast_meetings():
    """Удаляем (is_active=False) быстрые конференции, которые завершены, старше 24 часов и не имеют записей."""
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    # Находим конференции, которые нужно удалить
    meetings_to_disable = models.PlannedMeetingModel.objects.filter(
        is_fast=True,
        status='ended',
        date_begin__lt=cutoff_time,
        has_record=False,
        is_active=True
    )
    
    if not meetings_to_disable.exists():
        return 0
    
    # Удаляем конференции
    with transaction.atomic():
        updated_count = meetings_to_disable.update(
            is_active=False,
            deleted_at=timezone.now()
        )
        return updated_count


def extract_intents_from_meetings():
    """Извлечение намерений из транскрибации видеозаписи собрания."""

    records = models.MeetingRecordsModel.objects.filter(
        section__isnull=False,
        transcribe_json__isnull=False,
        is_intents_ready=False
    ).exclude(transcribe_json={}).exclude(transcribe_json="").order_by("-created_at")

    for record in records:
        try:
            extract_intents_from_meeting(record)
        except Exception as e:
            print(f"Ошибка при извлечении намерений для записи {record.pk}: {e}")
            continue
    return None


def extract_summary_from_meetings():
    """Извлечение саммари из транскрибации видеозаписи собрания."""

    records = models.MeetingRecordsModel.objects.filter(
        section__isnull=False,
        transcribe_json__isnull=False,
        is_summary_ready=False
    ).exclude(transcribe_json={}).exclude(transcribe_json="").order_by("-created_at")

    for record in records:
        try:
            extract_summary_from_meeting(record)
        except Exception as e:
            print(f"Ошибка при извлечении саммари для записи {record.pk}: {e}")
            continue
    return None


def extract_efficiency_from_meetings():
    """Извлечение анализа эффективности из транскрибации видеозаписи собрания."""

    cutoff_time = timezone.now() - timedelta(days=7)
    records = models.MeetingRecordsModel.objects.filter(
        section__isnull=False,
        transcribe_json__isnull=False,
        is_efficiency_ready=False,
        created_at__gte=cutoff_time,
    ).exclude(transcribe_json={}).exclude(transcribe_json="").order_by("-created_at")

    for record in records:
        try:
            extract_efficiency_from_meeting(record)
        except Exception as e:
            print(f"Ошибка при извлечении анализа эффективности для записи {record.pk}: {e}")
            continue
    return None


def cleanup_recent_record_files():
    """Очистка старых record_file (склеенное аудио+видео) у MeetingRecordsModel."""
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    records = models.MeetingRecordsModel.objects.filter(
        record_file__isnull=False
    ).select_related('record_file').filter(
        record_file__created_at__lt=cutoff_time
    )
    
    deleted_count = 0
    for record in records:
        try:
            if record.record_file:
                delete_file_physically_and_from_db(record.record_file)
                record.record_file = None
                record.save(update_fields=('record_file',))
                deleted_count += 1
        except Exception as e:
            print(f"Ошибка при удалении record_file для записи {record.pk}: {e}")
            continue
    
    return deleted_count