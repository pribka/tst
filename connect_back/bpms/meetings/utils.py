import hashlib
import os
import requests
import uuid
import json
import re
import subprocess
import tempfile
from copy import deepcopy
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.conf import settings
from . import models
from bkz3.settings import BACKEND_URL, FRONTEND_URL, RECORDS_ROOT
from django.utils import dateparse
from decimal import Decimal, ROUND_UP
from django.db import IntegrityError, transaction
from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework.response import Response
from rest_framework import status
from common.utils import order_queryset_from_get_param, get_filter_queryset, get_datetime_param
from common.models import File
import xmltodict
from django.utils import timezone
from bpms.comments.models import CommentModel
from bpms.tasks.models import TaskModel, TaskExecutionTimeModel
from bpms.tasks.utils import get_cached_statuses
from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupModel
from bpms.chat.models import ChatModel
from bpms.event_calendar.models import EventCalendarModel
from bpms.event_calendar.utils import get_project_from_calendar
from bpms.chat_ai.utils.messages import invoke_role_prompt, INTENT_RESPONSE_SOFT_SCHEMA, SUMMARY_SCHEMA, EFFICIENCY_SCHEMA
from bpms.chat_ai.serializers import IntentCreateSerializer
from bpms.chat_ai.models import IntentModel
from .notifications import notify_about_record_summary_ready
from common.current_profile.middleware import user_context
from help_desk import models as help_desk_models
from contractor_permissions.utils import check_user_app_section_role_permission


SPEAKER_RE = re.compile(r"\bSPEAKER_\d+\b", re.IGNORECASE)

PEOPLE_FIELDS = {
    "create_task": ("operator", "cooperators", "visors"),
    "create_event": ("members",),
    "create_meet": ("members",),
}


def _clean_people_strict(value: Any) -> Optional[str]:
    """
    Строгая очистка полей с людьми:
    - если не строка -> вернуть как есть
    - пустая строка -> None
    - если встречается SPEAKER_XX -> None
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    text_val = value.strip()
    if not text_val:
        return None

    if SPEAKER_RE.search(text_val):
        return None

    return text_val


def sanitize_intents_speaker_strict(intents):
    """
    Удаляет SPEAKER_XX из человеко-имённых полей, опираясь на PEOPLE_FIELDS.
    """
    data = deepcopy(intents)
    for obj in data:
        intent_type = obj.get("intent_type")
        for field in PEOPLE_FIELDS.get(intent_type, ()):
            if field in obj:
                obj[field] = _clean_people_strict(obj.get(field))
    return data


def _fmt_time(sec: float) -> str:
    """Форматирует секунды в формат [MM:SS] или [HH:MM:SS] если есть часы."""
    sec = int(round(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def round_duration(duration_seconds_raw):
    return max(60, ((duration_seconds_raw + 59) // 60) * 60)


def build_transcription_chunks(transcribe_json, max_llm_chars: int = 80000) -> Optional[List[str]]:
    """
    Делит транскрибацию записи на чанки текста в формате [MM:SS] текст, чтобы уложиться в лимит LLM.
    Возвращает список текстовых чанков либо None, если исходные данные не список.
    """
    try:
        parsed = json.loads(transcribe_json)
    except Exception:
        parsed = []

    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except Exception:
            parsed = []

    if not isinstance(parsed, list):
        return None

    # Формируем строки в формате [MM:SS] текст
    lines: List[str] = []
    for item in parsed:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        start_time = item.get("start") or 0
        time_str = _fmt_time(start_time)
        lines.append(f"[{time_str}] {text}")

    if not lines:
        return []

    # Делим на чанки по лимиту символов
    chunks: List[str] = []
    current_chunk_lines: List[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line)
        if current_len + line_len <= max_llm_chars:
            current_chunk_lines.append(line)
            current_len += line_len
        else:
            if current_chunk_lines:
                chunks.append("\n".join(current_chunk_lines))
            current_chunk_lines = [line]
            current_len = line_len

    if current_chunk_lines:
        chunks.append("\n".join(current_chunk_lines))

    return chunks


def extract_intents_from_meeting(record):
    section = record.section
    members_qs = section.meeting_section_members.select_related("user")
    member_names = []
    for member in members_qs:
        member_names.append(member.user.full_name)
    members_str = ", ".join(member_names)

    context = {
        "current_date": datetime.today().strftime("%Y-%m-%d"),
        "current_weekday": datetime.today().strftime("%A"),
        "meeting_members": members_str,
    }

    chunks = build_transcription_chunks(record.transcribe_json)

    if not chunks:
        return []

    intents: List[dict] = []

    for chunk in chunks:
        if not chunk:
            continue
        chunk_intents = invoke_role_prompt(
            user_message=chunk,
            role_code="meeting_intent_parser",
            context=context,
            consumer=record,
            format_schema=INTENT_RESPONSE_SOFT_SCHEMA,
            url_query_param=f"transcr_intents&record={record.pk}",
        )
        if chunk_intents and isinstance(chunk_intents, list):
            intents.extend(chunk_intents)

    # Удаляем ранее созданные намерения для этой записи
    IntentModel.objects.filter(source_object=record.pk).delete()

    intents = sanitize_intents_speaker_strict(intents)

    for item in intents:
        item_copy = item.copy()
        intent_type = item_copy.pop("intent_type", None)
        serializer = IntentCreateSerializer(
            data={
                "source_object": record.pk,
                "intent_type": intent_type,
                "raw_data": item_copy,
            }
        )
        if serializer.is_valid():
            serializer.save()

    print(f"Извлечены намерения для видеозаписи {record.pk}. Количество: {len(intents)}.")
    record.is_intents_ready = True
    record.save(update_fields=["is_intents_ready"])
    return intents


def extract_summary_from_meeting(record):
    """Извлекает краткое содержание из транскрибации."""
    chunks = build_transcription_chunks(record.transcribe_json, max_llm_chars=10000)

    if not chunks:
        return 0

    summaries: List[str] = []
    for chunk in chunks:
        if not chunk:
            continue
        chunk_summary = invoke_role_prompt(
            user_message=chunk,
            role_code="meeting_summary",
            context={},
            consumer=record,
            format_schema=SUMMARY_SCHEMA,
            url_query_param=f"transcr_summary&record={record.pk}",
        )
        summaries.extend([str(item).strip() for item in (chunk_summary or [])])

    if summaries and len(chunks) > 1:
        combined_summaries_text = "\n".join([f"- {item}" for item in summaries])
        combined_summary = invoke_role_prompt(
            user_message=combined_summaries_text,
            role_code="meeting_summary_combine",
            context={},
            consumer=record,
            format_schema=SUMMARY_SCHEMA,
            url_query_param=f"transcr_summary_combine&record={record.pk}",
        )
        summaries = [str(item).strip() for item in (combined_summary or [])]

    numbered = [f"{idx}. {item}" for idx, item in enumerate(summaries, start=1)]
    summary_text = "\n\n".join(numbered)

    if record.summary.strip():
        record.summary_old = record.summary
    record.summary = summary_text
    record.is_summary_ready = True

    if not record.is_summary_notified:
        section = record.section
        if section is not None:
            notify_about_record_summary_ready(section)
            record.is_summary_notified = True

    record.save(update_fields=["summary", "summary_old", "is_summary_ready", "is_summary_notified"])
    print(f"Извлечено краткое содержание для видеозаписи {record.pk}. Количество пунктов: {len(summaries)}.")

    return len(summaries)


def extract_efficiency_from_meeting(record):
    """Извлекает анализ эффективности использования времени из транскрибации."""
    chunks = build_transcription_chunks(record.transcribe_json, max_llm_chars=15000)

    if not chunks:
        return 0

    efficiencies: List[str] = []
    for chunk in chunks:
        if not chunk:
            continue
        chunk_efficiency = invoke_role_prompt(
            user_message=chunk,
            role_code="meeting_efficiency",
            context={},
            consumer=record,
            format_schema=EFFICIENCY_SCHEMA,
            url_query_param=f"transcr_efficiency&record={record.pk}",
        )
        efficiencies.extend([str(item).strip() for item in (chunk_efficiency or [])])

    # Объединяем все efficiencies и убираем дубли через LLM
    if efficiencies:
        combined_efficiencies_text = "\n".join([f"- {item}" for item in efficiencies])
        combined_efficiency = invoke_role_prompt(
            user_message=combined_efficiencies_text,
            role_code="meeting_efficiency_combine",
            context={},
            consumer=record,
            format_schema=EFFICIENCY_SCHEMA,
            url_query_param=f"transcr_efficiency_combine&record={record.pk}",
        )
        efficiencies = [str(item).strip() for item in (combined_efficiency or [])]

    numbered = [f"{idx}. {item}" for idx, item in enumerate(efficiencies, start=1)]
    efficiency_text = "\n\n".join(numbered)

    record.efficiency = efficiency_text
    record.is_efficiency_ready = True
    record.save(update_fields=["efficiency", "is_efficiency_ready"])
    print(f"Извлечен анализ эффективности для видеозаписи {record.pk}. Количество пунктов: {len(efficiencies)}.")

    return len(efficiencies)


def get_connect_meeting_url(pk=int()):
    return f"{BACKEND_URL}/api/v1/meetings/{str(pk)}/connect/"


def get_invite_link(invite_link=int()):
    return f"{BACKEND_URL}/api/v1/meetings/{str(invite_link)}/connect_external/"


def get_meeting_queryset(request):
    model = models.PlannedMeetingModel
    query_params = request.query_params
    qs = model.get_queryset(request).annotate(
        status_ordering=Case(
            When(status='online', then=Value(0)),
            # When(status='new', then=Value(1)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).distinct()
    date_begin_gte = query_params.get('date_begin_gte')
    if date_begin_gte:
        qs = qs.filter(date_begin__gte=date_begin_gte)
    date_begin_lte = query_params.get('date_begin_lte')
    if date_begin_lte:
        qs = qs.filter(date_begin__lte=date_begin_lte)
    qs = order_queryset_from_get_param(
        request, model, get_filter_queryset(
            request, model, qs
        )
    )
    if not qs.ordered:
        return qs.order_by('status_ordering', '-updated_at')
    else:
        return qs


def get_hash_url(first_param, get_params, server):
    """Генерирует подписанный URL для запроса к API BigBlueButton.
    Параметры:
        first_param (str): Имя метода API (например, 'getMeetings', 'join', 'create').
        get_params (str): Строка GET-параметров (без начального '?').
        server (object): Объект сервера, содержащий поля `url` (базовый URL API) и `secret` (секретный ключ для подписи).
    Возвращает подписанный URL с параметром checksum, который можно использовать для обращения к API BigBlueButton."""
    prep = first_param + get_params + server.secret
    checksum = hashlib.sha1(prep.encode()).hexdigest()
    divider = ''
    if not get_params == '':
        divider = '&'
    return server.url + first_param + '?' + get_params + divider + 'checksum=' + checksum


def get_webcams_file_url(meeting_record_url):
    """
    Возвращает URL на файл webcams.webm по URL записи встречи.
    URL в записи BBB указывает на playback-страницу:
    https://<host>/playback/presentation/2.3/<RECORD_ID>
    Медиа-файлы лежат по адресу:
    https://<host>/presentation/<RECORD_ID>/video/webcams.webm
    
    Возвращает URL на webcams.webm или None, если не удалось извлечь record_id.
    """
    parsed = urlparse(meeting_record_url)
    path_parts = [part for part in parsed.path.split('/') if part]
    if not path_parts:
        return None
    record_id = path_parts[-1]
    media_base = f"{parsed.scheme}://{parsed.netloc}/presentation/{record_id}"
    return f"{media_base}/video/webcams.webm"


def get_deskshare_file_url(meeting_record_url):
    """Возвращает URL на видеозапись демострации экрана deskshare.webm по URL записи встречи."""
    parsed = urlparse(meeting_record_url)
    path_parts = [part for part in parsed.path.split('/') if part]
    if not path_parts:
        return None
    record_id = path_parts[-1]
    media_base = f"{parsed.scheme}://{parsed.netloc}/presentation/{record_id}"
    return f"{media_base}/deskshare/deskshare.webm"


def download_webcams_file(meeting_record_url):
    """
    Выкачивает файл webcams.webm по URL записи встречи и сохраняет его в папку webcams.
    Возвращает объект File с сохраненным webcams.webm файлом или None в случае ошибки.
    """
    webcams_url = get_webcams_file_url(meeting_record_url)
    if not webcams_url:
        return None

    # Извлекаем record_id для использования в имени файла
    parsed = urlparse(meeting_record_url)
    path_parts = [part for part in parsed.path.split('/') if part]
    if not path_parts:
        return None
    record_id = path_parts[-1]

    # 2) Скачиваем файл. Если сервер вернул HTML/текст, не сохраняем как видео
    response = requests.get(webcams_url, stream=True, timeout=300)
    # Некоторые прокси/Nginx могут отдавать страницу с кодом 200, но это HTML-ошибка.
    content_type = response.headers.get('Content-Type', '')
    response.raise_for_status()
    if 'text/html' in content_type or 'text/plain' in content_type:
        raise ValueError(f'Ожидался бинарный webm, получили {content_type}')

    # 3) Генерируем имя
    filename = f"webcams_{record_id}_{uuid.uuid4().hex[:8]}.webm"

    # 4) Создаем объект File
    file_obj = File()
    file_obj.name = f"webcams_{record_id}"
    file_obj.extension = 'webm'
    # Если в справочнике типов есть video/webm — можно заменить на него
    file_obj.mime_type_id = 'application/octet-stream'
    file_obj.is_video = True
    file_obj.description = f"Видеозапись встречи {record_id}"
    file_obj.author = None

    # 5) Сохраняем поток в память по частям (без нагрузки на RAM через конкатенацию строк)
    file_bytes = bytearray()
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            file_bytes.extend(chunk)

    file_obj.size = len(file_bytes)
    # Временно переопределяем upload_to для сохранения в records/
    original_upload_to = file_obj.upload.field.upload_to
    file_obj.upload.field.upload_to = lambda instance, fname: f"records/{fname}"
    file_obj.upload.save(filename, ContentFile(bytes(file_bytes)), save=False)
    file_obj.upload.field.upload_to = original_upload_to

    file_obj.save()
    return file_obj


def sync_meeting_members(meeting, required_member_ids):
    """
    Синхронизирует участников собрания с требуемым списком.
    Добавляет недостающих участников и удаляет лишних.
    Автор собрания всегда остается участником и не удаляется.
    """
    required_member_ids = set(required_member_ids)
    if meeting.author_id:
        required_member_ids.add(meeting.author_id)
    
    current_member_ids = set(
        models.MeetingMemberModel.objects.filter(
            meeting=meeting,
            is_active=True
        ).values_list('user_id', flat=True)
    )
    
    # Добавляем недостающих участников
    missing_ids = required_member_ids - current_member_ids
    for user_id in missing_ids:
        models.MeetingMemberModel.objects.get_or_create(
            meeting=meeting,
            user_id=user_id,
            defaults={'is_moderator': True}
        )
    
    # Удаляем лишних участников (тех, кого нет в required_member_ids, кроме автора)
    extra_ids = current_member_ids - required_member_ids
    if extra_ids:
        models.MeetingMemberModel.objects.filter(
            meeting=meeting,
            user_id__in=extra_ids,
            is_active=True
        ).exclude(
            user_id=meeting.author_id
        ).delete()


def merge_deskshare_with_audio(meeting_record_url):
    """
    Скачивает видео экрана (deskshare.webm) и аудио (webcams.webm),
    склеивает их с помощью ffmpeg и сохраняет результат в папку records.
    Если демонстрации экрана не было (нет deskshare или 404) — сохраняет только webcams.webm.
    Возвращает объект File с сохраненным файлом или None в случае ошибки.
    """
    webcams_url = get_webcams_file_url(meeting_record_url)
    if not webcams_url:
        return None

    deskshare_url = get_deskshare_file_url(meeting_record_url)
    if not deskshare_url:
        return download_webcams_file(meeting_record_url)

    # Извлекаем record_id для использования в имени файла
    parsed = urlparse(meeting_record_url)
    path_parts = [part for part in parsed.path.split('/') if part]
    if not path_parts:
        return None
    record_id = path_parts[-1]

    # Создаем временную директорию для работы с файлами
    with tempfile.TemporaryDirectory() as temp_dir:
        deskshare_path = os.path.join(temp_dir, 'deskshare.webm')
        webcams_path = os.path.join(temp_dir, 'webcams.webm')
        output_path = os.path.join(temp_dir, 'merged.webm')

        try:
            # Скачиваем видео экрана; при отсутствии файла (404) или не-медиа — только webcams
            try:
                response = requests.get(deskshare_url, stream=True, timeout=300)
                content_type = response.headers.get('Content-Type', '')
                response.raise_for_status()
                if 'text/html' in content_type or 'text/plain' in content_type:
                    response.close()
                    return download_webcams_file(meeting_record_url)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    return download_webcams_file(meeting_record_url)
                raise

            with open(deskshare_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            # Скачиваем аудио из webcams
            response = requests.get(webcams_url, stream=True, timeout=300)
            content_type = response.headers.get('Content-Type', '')
            response.raise_for_status()
            if 'text/html' in content_type or 'text/plain' in content_type:
                raise ValueError(f'Ожидался бинарный webm для webcams, получили {content_type}')
            
            with open(webcams_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            # Склеиваем видео и аудио с помощью ffmpeg
            # -i deskshare.webm - видео экрана
            # -i webcams.webm - аудио
            # -c:v copy - копировать видео без перекодирования
            # -c:a copy - копировать аудио без перекодирования
            # -map 0:v:0 - взять видео из первого файла
            # -map 1:a:0 - взять аудио из второго файла
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', deskshare_path,
                '-i', webcams_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-y',  # Перезаписать выходной файл, если существует
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            # Проверяем, что выходной файл создан
            if not os.path.exists(output_path):
                raise ValueError('FFmpeg не создал выходной файл')

            # Читаем результат
            with open(output_path, 'rb') as f:
                file_bytes = f.read()

            # Создаем объект File
            filename = f"merged_{record_id}_{uuid.uuid4().hex[:8]}.webm"
            file_obj = File()
            file_obj.name = f"merged_{record_id}"
            file_obj.extension = 'webm'
            file_obj.mime_type_id = 'application/octet-stream'
            file_obj.is_video = True
            file_obj.description = f"Склеенное видео встречи {record_id}"
            file_obj.author = None
            file_obj.size = len(file_bytes)

            # Временно переопределяем upload_to для сохранения в records/
            original_upload_to = file_obj.upload.field.upload_to
            file_obj.upload.field.upload_to = lambda instance, fname: f"records/{fname}"
            file_obj.upload.save(filename, ContentFile(file_bytes), save=False)
            file_obj.upload.field.upload_to = original_upload_to

            file_obj.save()
            return file_obj

        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении ffmpeg: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except Exception as e:
            print(f"Ошибка при склеивании видео и аудио: {e}")
            return None


def process_meeting_record(meeting_record_pk):
    """
    Обрабатывает запись встречи: выкачивает webcams.webm файл, сохраняет ссылку на него,
    запускает процесс транскрибации, сохраняет транскрибацию.
    На вход принимает pk экземпляра MeetingRecordsModel.
    """
    try:
        # Получаем объект записи встречи
        meeting_record = models.MeetingRecordsModel.objects.get(pk=meeting_record_pk)
        
        if not meeting_record.url:
            print("URL записи встречи пустой")
            meeting_record.status = 'error'
            meeting_record.save(update_fields=('status',))
            return False
            
        # Ставим статус "В процессе"
        meeting_record.status = 'processing'
        meeting_record.save(update_fields=('status',))

        # Выкачиваем файл
        file_obj = download_webcams_file(meeting_record.url)
        
        if file_obj:
            # Сохраняем ссылку на файл в записи встречи
            meeting_record.record_file = file_obj
            meeting_record.save()
            print(f"Файл webcams.webm успешно выкачан и сохранен: {file_obj.name}")
        else:
            print("Не удалось выкачать файл webcams.webm")
            meeting_record.status = 'error'
            meeting_record.save(update_fields=('status',))
            return False

        # TODO Запускаем процесс транскрибации.
        # TODO Сохраняем результат транскрибации в поле transcribe

        # Ставим статус "Готова"
        meeting_record.status = 'done'
        meeting_record.save(update_fields=('status',))
        return True
        
    except Exception as e:
        print(f"Ошибка при обработке записи встречи {meeting_record_pk}: {e}")
        # Пытаемся обновить статус на error
        try:
            meeting_record = models.MeetingRecordsModel.objects.get(pk=meeting_record_pk)
            meeting_record.status = 'error'
            meeting_record.save(update_fields=('status',))
        except:
            pass
        return False


def sync_meeting_recordings(meeting_id: int, section_id: Optional[int] = None) -> int:
    """
    Тянет getRecordings из BBB и апсертом сохраняет записи в MeetingRecordsModel
    с установкой section_id из metadata.section_id/sectionId/section-id.
    Возвращает количество обработанных URL.
    """
    meeting = models.PlannedMeetingModel.objects.get(pk=meeting_id)
    url = get_hash_url('getRecordings', f'meetingID={meeting.id}', meeting.server)
    resp = requests.get(url, timeout=60)
    doc = xmltodict.parse(resp.text)
    try:
        recording = doc['response']['recordings']['recording']
    except TypeError:
        return 0

    # нормализуем к списку
    recordings = recording if isinstance(recording, list) else [recording]

    handled = 0
    for rec in recordings:
        # поддерживаем как один format (dict), так и список форматов
        formats = (rec.get('playback') or {}).get('format')
        if not formats:
            continue
        if not isinstance(formats, list):
            formats = [formats]

        for record in formats:
            record_url = record.get('url') if isinstance(record, dict) else None
            if not record_url:
                continue

            obj, created = models.MeetingRecordsModel.objects.get_or_create(
                meeting=meeting,
                url=record_url,
                defaults={'initial_data': record}
            )
            if not created:
                updated = False
                if not obj.initial_data:
                    obj.initial_data = record
                    updated = True
                if updated:
                    obj.save()
            handled += 1

            if created and meeting.related_object:
                try:
                    original = meeting.related_object.original_object
                    if isinstance(original, TaskModel):
                        created_dt = timezone.localtime(obj.created_at).strftime('%d.%m.%Y %H:%M')
                        text = f'<a href="{record_url}" target="_blank" rel="noopener noreferrer">Готова видеозапись</a> собрания от {created_dt}'
                        CommentModel.objects.create(
                            related_object=meeting.related_object,
                            text=text,
                            author=None,
                            is_system=True,
                        )
                except Exception:
                    pass

    # применим fallback к самой последней записи без секции
    if section_id:
        try:
            latest_record = models.MeetingRecordsModel.objects.filter(
                meeting_id=meeting_id,
                is_active=True,
            ).order_by('-created_at').first()
            if latest_record and latest_record.section_id is None:
                latest_record.section_id = section_id
                latest_record.save(update_fields=('section',))
        except Exception:
            pass

    if handled and meeting.has_record is False:
        meeting.has_record = True
        meeting.save(update_fields=('has_record',))
    return handled


def get_related_meeting(obj):
    """
    Возвращает видеовстречу, связанную с объектом, либо None.
    EventCalendarModel: возвращает obj.meeting.
    Иначе: последняя активная встреча с related_object_id=obj.id.
    """
    if isinstance(obj, EventCalendarModel):
        return obj.meeting
    return models.PlannedMeetingModel.objects.filter(
        related_object_id=obj.id,
        is_active=True
    ).order_by('-created_at').first()


def get_meeting_project_for_related_object(original_object):
    """
    Возвращает project_id (UUID) для собрания по related_object, без загрузки объекта проекта.
    - Задача (TaskModel): project_id задачи.
    - Чат (ChatModel): id проекта с linked_chat = этот чат, иначе project_id задачи с linked_chat = этот чат.
    - Событие календаря (EventCalendarModel): проект календаря (если календарь привязан к проекту).
    - Обращение (HelpDeskTicketModel): project_id из analytics_key.project.
    - Иначе: None.
    """
    if isinstance(original_object, TaskModel):
        return getattr(original_object, 'project_id', None)
    if isinstance(original_object, EventCalendarModel):
        project = get_project_from_calendar(original_object.calendar)
        return project.pk if project else None
    if isinstance(original_object, ChatModel):
        project_id = WorkgroupModel.objects.filter(
            linked_chat_id=original_object.chat_uid,
            is_project=True,
        ).values_list('pk', flat=True).first()
        if project_id is not None:
            return project_id
        project_id = TaskModel.objects.filter(
            linked_chat_id=original_object.chat_uid,
        ).values_list('project_id', flat=True).first()
        return project_id
    if isinstance(original_object, help_desk_models.HelpDeskTicketModel):
        analytics_key = getattr(original_object, 'analytics_key', None)
        return getattr(analytics_key, 'project_id', None)
    return None


def filter_meeting_section_queryset(queryset, request):
    """Фильтрует queryset секций собраний по временному диапазону. Производит поиск по названию собрания."""
    start = get_datetime_param(request, 'start')
    if start:
        queryset = queryset.filter(Q(date_start__gte=start) | Q(date_end__gte=start))
    end = get_datetime_param(request, 'end')
    if end:
        queryset = queryset.filter(Q(date_start__lte=end) | Q(date_end__lte=end))

    text = request.query_params.get('search')
    if text:
        queryset = queryset.filter(Q(meeting__name_ru__icontains=text) | Q(meeting__name_kk__icontains=text))

    return queryset


def get_my_day_user_ids(request):
    """Список profile_id для фильтра «Мой день»: query-параметр user или текущий пользователь."""
    user_param = request.query_params.get('user')
    profile_id = request.user.profile.pk
    if user_param:
        return user_param.split(',')
    return [str(profile_id)]


def get_my_day_meeting_sections_queryset(request):
    """
    Queryset секций видеовстреч для «Моего дня» (то же, что в action my_day).
    Учитывает project, workgroup, id, meeting, user.
    """
    project_param = request.query_params.get('project')
    workgroup_param = request.query_params.get('workgroup')
    section_id = request.query_params.get('id')
    meeting_id = request.query_params.get('meeting')
    user_ids = get_my_day_user_ids(request)

    queryset = models.MeetingSectionModel.get_queryset(request)
    if str(request.user.profile.pk) not in user_ids:
        queryset = queryset.filter(meeting_section_members__user_id__in=user_ids)

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
        queryset = queryset.filter(meeting__related_object_id__in=related_object_ids)

    if section_id:
        queryset = queryset.filter(pk=section_id)

    if meeting_id:
        queryset = queryset.filter(meeting_id=meeting_id)

    queryset = queryset.distinct().order_by('-date_start', '-created_at')
    queryset = filter_meeting_section_queryset(queryset, request)
    return queryset


def delete_file_physically_and_from_db(file):
    """Удаляет файл физически с диска и из базы данных.
    file: Экземпляр модели File для удаления"""
    if not file:
        return
    
    if file.upload:
        try:
            if os.path.exists(file.upload.path):
                os.remove(file.upload.path)
        except (OSError, ValueError):
            pass
    
    file.delete()


def create_call_execution_times(section):
    """Создает трудозатраты HelpDesk по звонку: специалисту тикета за участие в созвоне."""
    meeting = section.meeting
    call_obj = meeting.calls.filter(
        is_active=True,
        ticket__isnull=False,
        ticket__specialist__isnull=False,
    ).select_related(
        'ticket',
        'ticket__specialist',
        'ticket__specialist__user',
    ).order_by('-created_at').first()
    if not call_obj:
        return

    execution_date = timezone.localdate()
    task_execution_date = timezone.localdate(section.date_start)
    specialist = call_obj.ticket.specialist
    members_id = set(call_obj.ticket.members.all().values_list('pk', flat=True))
    started_at = call_obj.answered_at
    ended_at = call_obj.ended_at
    call_duration = timedelta(0)
    if started_at is not None and ended_at is not None and ended_at > started_at:
        call_duration = ended_at - started_at
    accepted_by_call_duration = timedelta(0)
    if (
        call_obj.accepted_by_id
        and started_at is not None
        and ended_at is not None
        and ended_at > started_at
    ):
        accepted_by_call_duration = ended_at - started_at
    
    # Это нужно для очень коротких звонков, меньше 1 минуты
    participant_ids_to_ensure = set()
    if call_obj.initiator_id:
        participant_ids_to_ensure.add(call_obj.initiator_id)
    if call_obj.accepted_by_id:
        participant_ids_to_ensure.add(call_obj.accepted_by_id)
    if participant_ids_to_ensure:
        existing_member_ids = set(
            models.MeetingSectionMemberModel.objects.filter(
                section=section,
                user_id__in=participant_ids_to_ensure,
                is_active=True,
            ).values_list('user_id', flat=True)
        )
        missing_member_ids = participant_ids_to_ensure - existing_member_ids
        if missing_member_ids:
            models.MeetingSectionMemberModel.objects.bulk_create([
                models.MeetingSectionMemberModel(
                    section=section,
                    user_id=member_id,
                    duration=accepted_by_call_duration,
                )
                for member_id in missing_member_ids
            ])

    members = models.MeetingSectionMemberModel.objects.filter(
        section=section,
        is_active=True,
    ).exclude(duration__isnull=True)
    fixed_members = []

    with transaction.atomic():
        for member in members:
            duration_seconds = round_duration(int(member.duration.total_seconds()))

            with user_context(member.user.user):
                if specialist is not None and member.user_id == specialist.pk:
                    help_desk_models.HelpDeskWorkLogModel.objects.create(
                        user=specialist,
                        ticket=call_obj.ticket,
                        meeting_section=section,
                        description='Созвон с клиентом',
                        date=execution_date,
                        duration=duration_seconds,
                        is_current=False,
                    )
                    member.is_execution_time_created = True
                    fixed_members.append(member)
                elif member.user_id in members_id:
                    help_desk_models.HelpDeskWorkLogModel.objects.create(
                        user=member.user,
                        ticket=call_obj.ticket,
                        meeting_section=section,
                        description='Созвон с клиентом',
                        date=execution_date,
                        duration=duration_seconds,
                        is_current=False,
                    )
                    member.is_execution_time_created = True
                    fixed_members.append(member)
                else:
                    if not check_user_app_section_role_permission(member.user_id, 'tasks'):
                        continue
                    task = get_or_create_user_auto_task(member.user)
                    hours_value = (Decimal(duration_seconds) / 3600).quantize(Decimal('0.01'), rounding=ROUND_UP)
                    section_date_str = section.created_at.strftime('%d.%m.%Y')
                    TaskExecutionTimeModel.objects.create(
                        task=task,
                        user=member.user,
                        meeting_section=section,
                        duration=duration_seconds,
                        hours=hours_value,
                        date=task_execution_date,
                        work_type_id='discussion',
                        description=f'Встреча "{section.name}" от {section_date_str}',
                    )
                    member.is_execution_time_created = True
                    fixed_members.append(member)
        if fixed_members:
            models.MeetingSectionMemberModel.objects.bulk_update(fixed_members, ['is_execution_time_created'])


def get_or_create_project_auto_task(project):
    complete_statuses = get_cached_statuses()[2]
    auto_task = TaskModel.objects.filter(
        project=project,
        is_active=True,
        is_auto_created=True,
    ).exclude(status_id__in=complete_statuses).order_by('-created_at').first()
    if auto_task is not None:
        return auto_task

    if not project.organization_id:
        return None

    founder_membership = WorkgroupMembersModel.objects.filter(
        work_group=project,
        is_active=True,
        membership_request_status__code='APPROVED',
        membership_role__code='FOUNDER',
    ).select_related('member').first()
    if founder_membership is None:
        return None

    founder = founder_membership.member
    date_formatted = timezone.localdate().strftime('%d.%m.%Y')
    auto_task_name = f'Автозадача по видеовстречам от {date_formatted}. Проект "{project.name}"'
    return TaskModel.objects.create(
        name=auto_task_name,
        description='Служебная задача для учёта времени по видеовстречам проекта.',
        is_auto_created=True,
        project=project,
        dead_line=project.dead_line,
        author=founder,
        owner=founder,
        operator=founder,
        organization=project.organization,
        task_type_id='task',
        status_id='new',
    )


def get_or_create_user_auto_task(user):
    complete_statuses = get_cached_statuses()[2]
    auto_task_name = f'Автозадача пользователя {user.full_name}'
    auto_task = TaskModel.objects.filter(
        project__isnull=True,
        is_active=True,
        is_auto_created=True,
        author=user,
    ).exclude(status_id__in=complete_statuses).order_by('-created_at').first()
    if auto_task is not None:
        return auto_task

    user_contractor = user.get_or_set_current_contractor()
    return TaskModel.objects.create(
        name=auto_task_name,
        description='Служебная задача для учёта времени по видеовстречам пользователя.',
        is_auto_created=True,
        project=None,
        author=user,
        owner=user,
        operator=user,
        organization=user_contractor,
        task_type_id='task',
        status_id='new',
    )


def get_meeting_target_ticket(meeting):
    if not meeting.related_object_id:
        return None

    try:
        original = meeting.related_object.original_object
        if isinstance(original, help_desk_models.HelpDeskTicketModel):
            return original
    except Exception:
        pass

    return None


def get_meeting_target_task(meeting):
    target_task = None
    project = meeting.project if meeting.project_id else None
    if meeting.related_object_id:
        try:
            original = meeting.related_object.original_object
            if isinstance(original, TaskModel):
                target_task = original
            elif isinstance(original, ChatModel):
                task_linked = TaskModel.objects.filter(
                    linked_chat_id=original.chat_uid,
                ).first()
                if task_linked is not None:
                    target_task = task_linked
                elif project is None:
                    meeting_project_id = get_meeting_project_for_related_object(original)
                    if meeting_project_id is not None:
                        project = WorkgroupModel.objects.get(pk=meeting_project_id)
        except Exception:
            pass

    if target_task is None and project is not None:
        target_task = get_or_create_project_auto_task(project)

    return target_task


def create_meeting_execution_times(section):
    """
    После завершения видеовстречи создаёт трудозатраты (TaskExecutionTimeModel) для участников
    секции: либо на задачу из связанного объекта встречи, либо на автозадачу проекта, либо на
    персональную автозадачу пользователя. Проект берётся из meeting.project либо определяется
    по related_object (чат → проект/задача).
    """
    target_task = get_meeting_target_task(section.meeting)
    return create_section_task_execution_times(section=section, default_task=target_task)


def _get_section_members_for_execution_times(section):
    return models.MeetingSectionMemberModel.objects.filter(
        section=section,
        is_active=True,
    ).exclude(duration__isnull=True).select_related('user__user')

def create_section_task_execution_times(section, default_task):
    execution_date = timezone.localdate(section.date_start)
    members = _get_section_members_for_execution_times(section)
    fixed_members = []
    allowed_default_task_member_ids = set()
    execution_time_project_id = None
    if default_task is not None:
        execution_time_project_id = default_task.project_id
        if default_task.is_auto_created and default_task.project_id:
            allowed_default_task_member_ids = set(
                WorkgroupMembersModel.objects.filter(
                    work_group_id=default_task.project_id,
                    is_active=True,
                    membership_request_status__code='APPROVED',
                    member__is_active=True,
                ).values_list('member_id', flat=True)
            )
        else:
            allowed_default_task_member_ids = set(default_task.get_member_ids)

    with transaction.atomic():
        if section.execution_time_project_id != execution_time_project_id:
            section.execution_time_project_id = execution_time_project_id
            section.save(update_fields=('execution_time_project',))

        for member in members:
            if not check_user_app_section_role_permission(member.user_id, 'tasks'):
                continue

            if member.user_id in allowed_default_task_member_ids:
                task = default_task
            else:
                task = get_or_create_user_auto_task(member.user)

            duration_seconds = round_duration(int(member.duration.total_seconds()))
            hours_value = (Decimal(duration_seconds) / 3600).quantize(Decimal('0.01'), rounding=ROUND_UP)

            with user_context(member.user.user):
                section_date_str = section.created_at.strftime('%d.%m.%Y')
                TaskExecutionTimeModel.objects.create(
                    task=task,
                    user=member.user,
                    meeting_section=section,
                    duration=duration_seconds,
                    hours=hours_value,
                    date=execution_date,
                    work_type_id='discussion',
                    description=f'Встреча "{section.name}" от {section_date_str}',
                )
                member.is_execution_time_created = True
                fixed_members.append(member)

        if fixed_members:
            models.MeetingSectionMemberModel.objects.bulk_update(fixed_members, ['is_execution_time_created'])


def deactivate_section_execution_times(section, user_ids):
    """
    Деактивирует трудозатраты секции по двум моделям через save(), чтобы отработала
    сопутствующая логика (в т.ч. регистр накопления).
    """
    task_execution_times = TaskExecutionTimeModel.objects.filter(
        meeting_section=section,
        user_id__in=user_ids,
        is_active=True,
    ).select_related('user__user')
    help_desk_work_logs = help_desk_models.HelpDeskWorkLogModel.objects.filter(
        meeting_section=section,
        user_id__in=user_ids,
        is_active=True,
    ).select_related('user__user')

    for execution_time in task_execution_times:
        execution_time.is_active = False
        execution_time.save(update_fields=('is_active',))

    for work_log in help_desk_work_logs:
        work_log.is_active = False
        work_log.save(update_fields=('is_active',))


def reassign_section_execution_times(section, project):
    target_task = get_or_create_project_auto_task(project)

    member_user_ids = list(
        _get_section_members_for_execution_times(section).values_list('user_id', flat=True).distinct()
    )

    with transaction.atomic():
        deactivate_section_execution_times(
            section=section,
            user_ids=member_user_ids,
        )
        create_section_task_execution_times(
            section=section,
            default_task=target_task,
        )