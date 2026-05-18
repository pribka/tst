import logging
import requests
from django.db import transaction
from .models import Partition, OfficialClarificationOrgan, ContentItem, Tag, \
    SettingsGos  # поправьте импорт под ваш проект
from django.utils import timezone

logger = logging.getLogger(__name__)
# DOMEN = "https://tst.gos24.kz"

# DOMEN = "http://127.0.0.1:8000"

def partition_exchange():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/partition/"
            # Берём только то, что ещё не отправляли
            qs = Partition.objects.filter(sent_gos=False)

            # Формируем JSON-массив
            payload = [
                {
                    "uid_connect": str(p.pk),   # используйте str, если PK — UUID
                    "code": p.code or "",
                    "name": p.name or "",
                    "name_kk": p.name_kk or "",
                }
                for p in qs
            ]

            if not payload:
                logger.info("partition_exchange: нечего отправлять")
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(
                    API_URL,
                    json=payload,          # <-- ключевое: отправляем JSON
                    timeout=60,
                    verify=False
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.exception("partition_exchange: ошибка запроса: %s", e)
                return {"sent": len(payload), "updated": 0, "status": f"error: {e}", 'payload': str(payload)}

            # Если сервер возвращает успех — помечаем записи
            updated = 0
            with transaction.atomic():
                ids = [p.pk for p in qs]
                updated = Partition.objects.filter(pk__in=ids).update(sent_gos=True)

            return {"sent": len(payload), "updated": updated, "status": "ok"}
    return {"sent": 'False'}


def partition_exchange2():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/partition2/"
            # Берём только то, что ещё не отправляли
            qs = Partition.objects.filter(sent_gos=False)

            # Формируем JSON-массив
            payload = [
                {
                    "uid_connect": str(p.pk),   # используйте str, если PK — UUID
                    "code": p.code or "",
                    "name": p.name or "",
                }
                for p in qs
            ]

            if not payload:
                logger.info("partition_exchange: нечего отправлять")
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(
                    API_URL,
                    json=payload,          # <-- ключевое: отправляем JSON
                    timeout=60,
                    verify=False
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.exception("partition_exchange: ошибка запроса: %s", e)
                return {"sent": len(payload), "updated": 0, "status": f"error: {e}", 'payload': str(payload)}

            # Если сервер возвращает успех — помечаем записи
            updated = 0
            with transaction.atomic():
                ids = [p.pk for p in qs]
                updated = Partition.objects.filter(pk__in=ids).update(sent_gos=True)

            return {"sent": len(payload), "updated": updated, "status": "ok"}
    return {"sent": 'False'}


def tag_exchange():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/tag/"
            # Берём только то, что ещё не отправляли
            qs = Tag.objects.filter(sent_gos=False)

            # Формируем JSON-массив
            payload = [
                {
                    "uid_connect": str(p.pk),   # используйте str, если PK — UUID
                    "name": p.name or "",
                    "name_kk": p.name_kk or "",
                }
                for p in qs
            ]

            if not payload:
                logger.info("partition_exchange: нечего отправлять")
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(
                    API_URL,
                    json=payload,          # <-- ключевое: отправляем JSON
                    timeout=60,
                    verify=False
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.exception("partition_exchange: ошибка запроса: %s", e)
                return {"sent": len(payload), "updated": 0, "status": f"error: {e}", 'payload': str(payload)}

            # Если сервер возвращает успех — помечаем записи
            updated = 0
            with transaction.atomic():
                ids = [p.pk for p in qs]
                updated = Tag.objects.filter(pk__in=ids).update(sent_gos=True)

            return {"sent": len(payload), "updated": updated, "status": "ok"}
    return {"sent": 'False'}


def tag_exchange2():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/tag2/"
            # Берём только то, что ещё не отправляли
            qs = Tag.objects.filter(sent_gos=False)

            # Формируем JSON-массив
            payload = [
                {
                    "uid_connect": str(p.pk),   # используйте str, если PK — UUID
                    "name": p.name or "",
                }
                for p in qs
            ]

            if not payload:
                logger.info("partition_exchange: нечего отправлять")
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(
                    API_URL,
                    json=payload,          # <-- ключевое: отправляем JSON
                    timeout=60,
                    verify=False
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.exception("partition_exchange: ошибка запроса: %s", e)
                return {"sent": len(payload), "updated": 0, "status": f"error: {e}", 'payload': str(payload)}

            # Если сервер возвращает успех — помечаем записи
            updated = 0
            with transaction.atomic():
                ids = [p.pk for p in qs]
                updated = Tag.objects.filter(pk__in=ids).update(sent_gos=True)

            return {"sent": len(payload), "updated": updated, "status": "ok"}
    return {"sent": 'False'}


def official_organ_exchange():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/organs/"
            qs = OfficialClarificationOrgan.objects.filter(sent_gos=False)
            payload = [
                {
                    "uid_connect": str(x.pk),   # чем будешь связывать записи на стороне получателя
                    "title": x.title or "",
                    "title_kk": x.title_kk or "",
                }
                for x in qs
            ]
            if not payload:
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(API_URL, json=payload, timeout=60, verify=False)
                # при отладке полезно увидеть тело ответа при ошибке
                if resp.status_code >= 400:
                    logger.error("official_organ_exchange: %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            except requests.RequestException as e:
                body = getattr(e, "response", None).text if getattr(e, "response", None) else ""
                logger.error("official_organ_exchange error: %s; body=%s", e, body)
                return {"sent": 0, "updated": 0, "status": f"error: {e}"}

            with transaction.atomic():
                OfficialClarificationOrgan.objects.filter(pk__in=[x.pk for x in qs]).update(sent_gos=True)

            return {"sent": len(payload), "updated": len(payload), "status": "ok"}
    return {"sent": 'False'}


def official_organ_exchange2():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/organs2/"
            qs = OfficialClarificationOrgan.objects.filter(sent_gos=False)
            payload = [
                {
                    "uid_connect": str(x.pk),   # чем будешь связывать записи на стороне получателя
                    "title": x.title or "",
                }
                for x in qs
            ]
            if not payload:
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(API_URL, json=payload, timeout=60, verify=False)
                # при отладке полезно увидеть тело ответа при ошибке
                if resp.status_code >= 400:
                    logger.error("official_organ_exchange: %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            except requests.RequestException as e:
                body = getattr(e, "response", None).text if getattr(e, "response", None) else ""
                logger.error("official_organ_exchange error: %s; body=%s", e, body)
                return {"sent": 0, "updated": 0, "status": f"error: {e}"}

            with transaction.atomic():
                OfficialClarificationOrgan.objects.filter(pk__in=[x.pk for x in qs]).update(sent_gos=True)

            return {"sent": len(payload), "updated": len(payload), "status": "ok"}
    return {"sent": 'False'}


def _iso(dt):
    if not dt:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt.isoformat()


def content_item_exchange():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/content-items/"
            qs = (ContentItem.objects
                  .prefetch_related('tags')
                  .select_related("partition", "organ")
                  .filter(sent_gos=False)[:500])

            payload = []
            for x in qs:
                tag_uids = list(x.tags.values_list('id', flat=True))
                payload.append({
                    "uid_connect": str(x.pk),
                    "kind": x.kind,
                    "is_active": x.is_active,
                    "main_in_week": x.main_in_week,
                    "created": _iso(x.created_at),
                    "title": x.title,
                    "title_kk": x.title_kk,
                    "slug": x.slug,
                    "publish": x.publish,
                    "draft": x.draft,
                    "publication_date": _iso(x.publication_date),
                    "only_subscribed": x.only_subscribed,
                    "image": x.image,
                    "summary": x.summary,
                    "body": x.body,
                    "body_kk": x.body_kk,
                    "body_clean": x.body_clean,
                    "body_clean_kk": x.body_clean_kk,
                    "body_amp": x.body_amp,
                    "body_html": x.body_html,
                    "content_type": x.content_type,
                    "body_html_amp": x.body_html_amp,
                    "description": x.description,
                    "description_kk": x.description_kk,
                    "description_clean": x.description_clean,
                    "description_clean_kk": x.description_clean_kk,
                    "description_amp": x.description_amp,
                    "tutorial_id": x.tutorial_id,
                    "section_id": x.section_id,
                    "id_gos24": x.id_gos24,
                    "webinar_active": x.webinar_active,
                    "question": x.question,
                    "question_kk": x.question_kk,
                    "question_html": x.question_html,
                    "question_html_kk": x.question_html_kk,
                    "answer": x.answer,
                    "answer_kk": x.answer_kk,
                    "answer_html": x.answer_html,
                    "answer_html_kk": x.answer_html_kk,
                    "small_title": x.small_title,
                    "lecturer_full_name": x.lecturer_full_name,
                    "content_edu_type": x.content_edu_type,
                    "webinar_date": x.webinar_date,
                    "planned_date": x.planned_date.isoformat() if x.planned_date else None,
                    "common_date": x.common_date.isoformat() if x.common_date else None,
                    "start_live_time": _iso(x.start_live_time),
                    "end_live_time": _iso(x.end_live_time),
                    "youtube_url": x.youtube_url,
                    "broadcast": x.broadcast,
                    "next": x.next,
                    "spend": x.spend,
                    "free": x.free,

                    # связи по uid_connect (предполагается, что на получателе они есть)
                    "partition_uid": str(x.partition.pk) if x.partition else None,
                    "organ_uid": str(x.organ.pk) if x.organ else None,
                    "tags_uid": [str(u) for u in tag_uids if u],
                })

            if not payload:
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(API_URL, json=payload, timeout=1000, verify=False)
                if resp.status_code >= 400:
                    logger.error("content_item_exchange: %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            except requests.RequestException as e:
                body = getattr(e, "response", None).text if getattr(e, "response", None) else ""
                logger.error("content_item_exchange error: %s; body=%s", e, body)
                return {"sent": 0, "updated": 0, "status": f"error: {e}"}

            with transaction.atomic():
                ContentItem.objects.filter(pk__in=[x.pk for x in qs]).update(sent_gos=True)

            return {"sent": len(payload), "updated": len(payload), "status": "ok"}
    return {"sent": 'False'}


def content_item_exchange2():
    settings_gos = SettingsGos.objects.filter(is_active=True, send_gos=True).first()
    if settings_gos:
        if settings_gos.send_gos:
            DOMEN = settings_gos.url_send_gos
            API_URL = DOMEN + "/api/v2/content_item_gos24/exchange/content-items2/"
            qs = (ContentItem.objects
                  .prefetch_related('tags')
                  .select_related("partition", "organ")
                  .filter(sent_gos=False)[:500])

            payload = []
            for x in qs:
                tag_uids = list(x.tags.values_list('id', flat=True))
                payload.append({
                    "uid_connect": str(x.pk),
                    "kind": x.kind,
                    "is_active": x.is_active,
                    "main_in_week": x.main_in_week,
                    "created": _iso(x.created_at),
                    "title": x.title,
                    "slug": x.slug,
                    "publish": x.publish,
                    "draft": x.draft,
                    "publication_date": _iso(x.publication_date),
                    "only_subscribed": x.only_subscribed,
                    "image": x.image,
                    "summary": x.summary,
                    "body": x.body,
                    "body_clean": x.body_clean,
                    "body_amp": x.body_amp,
                    "body_html": x.body_html,
                    "content_type": x.content_type,
                    "body_html_amp": x.body_html_amp,
                    "description": x.description,
                    "description_clean": x.description_clean,
                    "description_amp": x.description_amp,
                    "tutorial_id": x.tutorial_id,
                    "section_id": x.section_id,
                    "id_gos24": x.id_gos24,
                    "webinar_active": x.webinar_active,
                    "question": x.question,
                    "question_html": x.question_html,
                    "answer": x.answer,
                    "answer_html": x.answer_html,
                    "small_title": x.small_title,
                    "lecturer_full_name": x.lecturer_full_name,
                    "content_edu_type": x.content_edu_type,
                    "webinar_date": x.webinar_date,
                    "planned_date": x.planned_date.isoformat() if x.planned_date else None,
                    "common_date": x.common_date.isoformat() if x.common_date else None,
                    "start_live_time": _iso(x.start_live_time),
                    "end_live_time": _iso(x.end_live_time),
                    "youtube_url": x.youtube_url,
                    "broadcast": x.broadcast,
                    "next": x.next,
                    "spend": x.spend,
                    "free": x.free,

                    # связи по uid_connect (предполагается, что на получателе они есть)
                    "partition_uid": str(x.partition.pk) if x.partition else None,
                    "organ_uid": str(x.organ.pk) if x.organ else None,
                    "tags_uid": [str(u) for u in tag_uids if u],
                })

            if not payload:
                return {"sent": 0, "updated": 0, "status": "empty"}

            try:
                resp = requests.post(API_URL, json=payload, timeout=1000, verify=False)
                if resp.status_code >= 400:
                    logger.error("content_item_exchange: %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            except requests.RequestException as e:
                body = getattr(e, "response", None).text if getattr(e, "response", None) else ""
                logger.error("content_item_exchange error: %s; body=%s", e, body)
                return {"sent": 0, "updated": 0, "status": f"error: {e}"}

            with transaction.atomic():
                ContentItem.objects.filter(pk__in=[x.pk for x in qs]).update(sent_gos=True)

            return {"sent": len(payload), "updated": len(payload), "status": "ok"}
    return {"sent": 'False'}


def all_exchange_gos24():
    partition_exchange()
    tag_exchange()
    official_organ_exchange()
    content_item_exchange()

