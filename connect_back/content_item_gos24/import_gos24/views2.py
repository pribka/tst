# views.py
import json
from contextlib import contextmanager

from django.db import transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime

from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.views import APIView

from content_item_gos24.models import (
    Tag,
    Partition,
    ContentItem,
    OfficialClarificationOrgan,
)

# задаёшь здесь и больше нигде
IMPORT_PASSWORD = "my_secret_password"


# =========================
# ===== СЕРВИС-ФУНКЦИИ ====
# =========================

def _set_created_field(obj, dt):
    """Безопасно проставляет поле даты создания, если оно есть в модели."""
    if not dt:
        return
    for name in ("created_at", "created", "date_created", "created_on"):
        if hasattr(obj, name):
            setattr(obj, name, dt)
            break


def _apply_tags(obj, tags_ids):
    """Привязка M2M-тегов по id_gos24, с фолбэком на 'id'."""
    if not hasattr(obj, "tags"):
        return
    tags_ids = tags_ids or []
    if not tags_ids:
        obj.tags.clear()
        return

    qs = Tag.objects.filter(id_gos24__in=tags_ids)
    if not qs.exists():
        qs = Tag.objects.filter(id__in=tags_ids)
    obj.tags.set(qs) if qs.exists() else obj.tags.clear()


@contextmanager
def _atomic_per_item(enable=True):
    """Тонкий helper: per-item atomic(), чтобы не валить весь импорт при ошибках."""
    if enable:
        with transaction.atomic():
            yield
    else:
        # без транзакции
        yield


def import_connect_tags(items, *, atomic=True):
    """
    Импорт тегов из списка словарей.
    Возвращает dict: {"imported":..., "created":..., "updated":..., "errors":[...]}
    """
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id' (id_gos24)")
                id_gos24 = int(item["id"])
                title = (item.get("title") or "").strip()
                is_active = bool(item.get("is_active", True))
                main = bool(item.get("main", False))
                created_str = item.get("created")

                obj, was_created = Tag.objects.get_or_create(
                    id_gos24=id_gos24,
                    defaults={"name": title, "name_ru": title, "is_active": is_active, "main": main},
                )

                if was_created and created_str:
                    _set_created_field(obj, parse_datetime(created_str))

                if not was_created:
                    obj.name = title
                    obj.name_ru = title
                    obj.is_active = is_active
                    obj.main = main

                obj.sent_gos = False
                obj.save()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_partitions(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id' (id_gos24)")
                if "name" not in item:
                    raise ValueError("Отсутствует поле 'name'")

                id_gos24 = int(item["id"])
                name = (item.get("name") or "").strip()

                obj, was_created = Partition.objects.get_or_create(
                    id_gos24=id_gos24, defaults={"name": name, "name_ru": name}
                )

                if not was_created:
                    obj.name = name
                    obj.name_ru = name
                obj.sent_gos = False
                obj.save()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def _upsert_content_item_base(kind, item, *, atomic=True):
    """
    Общая логика upsert для ContentItem.
    Возвращает (obj, was_created, errors_dict_or_None)
    """
    try:
        with _atomic_per_item(atomic):
            if "id" not in item:
                raise ValueError("Отсутствует поле 'id'")
            id_gos24 = int(item["id"])

            title = (item.get("title") or "").strip()
            description = item.get("description") or ""
            description_clean = item.get("description_clean") or ""
            body = item.get("body") or ""
            body_clean = item.get("body_clean") or ""
            image = item.get("image") or None

            only_subscribed = bool(item.get("only_subscribed", False))
            main_in_week = bool(item.get("main_in_week", False))
            anchor_links = bool(item.get("anchor_links", False))
            is_active = bool(item.get("is_active", True))

            pub_dt = parse_datetime(item["publication_date"]) if item.get("publication_date") else None
            created_src = parse_datetime(item["created"]) if item.get("created") else None

            partition_obj = None
            if item.get("partition_id") is not None:
                partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

            defaults = {
                "title": title,
                "description": description,
                "description_clean": description_clean,
                "body": body,
                "body_clean": body_clean,
                "partition": partition_obj,
                "publication_date": pub_dt,
                "only_subscribed": only_subscribed,
                "main_in_week": main_in_week,
                "anchor_links": anchor_links,
                "image": image,
                "is_active": is_active,
            }

            obj, was_created = ContentItem.objects.get_or_create(
                kind=kind, id_gos24=id_gos24, defaults=defaults
            )

            _set_created_field(obj, created_src)

            if not was_created:
                obj.title = title
                obj.description = description
                obj.description_clean = description_clean
                obj.body = body
                obj.body_clean = body_clean
                obj.partition = partition_obj
                obj.publication_date = pub_dt
                obj.only_subscribed = only_subscribed
                obj.main_in_week = main_in_week
                obj.anchor_links = anchor_links
                obj.image = image
                obj.is_active = is_active

            obj.sent_gos = False
            obj.save()

            _apply_tags(obj, item.get("tags") or [])

            return obj, was_created, None
    except Exception as e:
        return None, None, {"id": item.get("id"), "error": str(e)}


def import_connect_news(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_NEWS_PUBLICATIONS_GOS24

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        obj, was_created, err = _upsert_content_item_base(KIND, item, atomic=atomic)
        if err:
            err["index"] = idx
            errors.append(err)
            continue
        imported += 1
        created_cnt += int(was_created)
        updated_cnt += int(not was_created)

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_articles(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_ARTICLE

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        obj, was_created, err = _upsert_content_item_base(KIND, item, atomic=atomic)
        if err:
            err["index"] = idx
            errors.append(err)
            continue
        imported += 1
        created_cnt += int(was_created)
        updated_cnt += int(not was_created)

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_official_organs(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item or "title" not in item:
                    raise ValueError("Отсутствует 'id' или 'title'")

                id_gos24 = int(item["id"])
                title = (item.get("title") or "").strip()

                obj, was_created = OfficialClarificationOrgan.objects.get_or_create(
                    id_gos24=id_gos24, defaults={"title": title}
                )

                if not was_created:
                    obj.title = title
                obj.sent_gos = False
                obj.save()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_official_clarifications(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_OFFICIAL

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title = (item.get("title") or "").strip()
                description = item.get("description") or ""
                description_clean = item.get("description_clean") or ""
                body = item.get("body") or ""
                body_clean = item.get("body_clean") or ""
                image = item.get("image") or None

                only_subscribed = bool(item.get("only_subscribed", False))
                main_in_week = bool(item.get("main_in_week", False))
                anchor_links = bool(item.get("anchor_links", False))
                is_active = bool(item.get("is_active", True))

                pub_dt = parse_datetime(item["publication_date"]) if item.get("publication_date") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                organ_obj = None
                if item.get("organ_id") is not None:
                    organ_obj = OfficialClarificationOrgan.objects.filter(id_gos24=item["organ_id"]).first()

                defaults = {
                    "title": title,
                    "description": description,
                    "description_clean": description_clean,
                    "body": body,
                    "body_clean": body_clean,
                    "partition": partition_obj,
                    "organ": organ_obj,
                    "publication_date": pub_dt,
                    "only_subscribed": only_subscribed,
                    "main_in_week": main_in_week,
                    "anchor_links": anchor_links,
                    "image": image,
                    "is_active": is_active,
                }

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND, id_gos24=id_gos24, defaults=defaults
                )

                _set_created_field(obj, created_src)

                if not was_created:
                    obj.title = title
                    obj.description = description
                    obj.description_clean = description_clean
                    obj.body = body
                    obj.body_clean = body_clean
                    obj.partition = partition_obj
                    obj.organ = organ_obj
                    obj.publication_date = pub_dt
                    obj.only_subscribed = only_subscribed
                    obj.main_in_week = main_in_week
                    obj.anchor_links = anchor_links
                    obj.image = image
                    obj.is_active = is_active

                obj.sent_gos = False
                obj.save()

                _apply_tags(obj, item.get("tags") or [])

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_questions(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_QA

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                question = item.get("question") or ""
                # BUGFIX: раньше answer брался из 'question'; теперь из 'answer'
                answer = item.get("answer") or ""
                question_html = item.get("question_html") or ""
                answer_html = item.get("answer_html") or ""

                main_in_week = bool(item.get("main_in_week", False))
                is_active = bool(item.get("is_active", True))

                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                defaults = {
                    "title": question,
                    "question": question,
                    "question_html": question_html,
                    "answer": answer,
                    "answer_html": answer_html,
                    "partition": partition_obj,
                    "main_in_week": main_in_week,
                    "is_active": is_active,
                }

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND, id_gos24=id_gos24, defaults=defaults
                )

                _set_created_field(obj, created_src)

                if not was_created:
                    obj.question = question
                    obj.question_html = question_html
                    obj.answer = answer
                    obj.answer_html = answer_html
                    obj.partition = partition_obj
                    obj.main_in_week = main_in_week
                    obj.is_active = is_active

                obj.sent_gos = False
                obj.save()

                _apply_tags(obj, item.get("tags") or [])

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_webinars(items, *, atomic=True):
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_WEBINAR

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title = (item.get("title") or "").strip()
                body = item.get("body") or ""
                body_clean = item.get("body_clean") or ""
                webinar_date = item.get("webinar_date") or ""
                youtube_url = item.get("youtube_url") or ""
                content_type = item.get("content_type") or ""
                broadcast = item.get("broadcast") or ""
                lecturer_full_name = item.get("lecturer_full_name") or ""

                spend = bool(item.get("spend", False))
                free = bool(item.get("free", False))
                is_active = bool(item.get("is_active", True))

                planned_date = item.get("planned_date")
                start_live_time = parse_datetime(item["start_live_time"]) if item.get("start_live_time") else None
                end_live_time = parse_datetime(item["end_live_time"]) if item.get("end_live_time") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                defaults = {
                    "title": title,
                    "body": body,
                    "body_clean": body_clean,
                    "youtube_url": youtube_url,
                    "webinar_date": webinar_date,
                    "content_type": content_type,
                    "spend": spend,
                    "planned_date": planned_date,
                    "partition": partition_obj,
                    "broadcast": broadcast,
                    "lecturer_full_name": lecturer_full_name,
                    "start_live_time": start_live_time,
                    "end_live_time": end_live_time,
                    "only_subscribed": not free,
                    "is_active": is_active,
                }

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND, id_gos24=id_gos24, defaults=defaults
                )

                _set_created_field(obj, created_src)

                if not was_created:
                    obj.title = title
                    obj.body = body
                    obj.body_clean = body_clean
                    obj.youtube_url = youtube_url
                    obj.content_type = content_type
                    obj.webinar_date = webinar_date
                    obj.spend = spend
                    obj.planned_date = planned_date
                    obj.broadcast = broadcast
                    obj.lecturer_full_name = lecturer_full_name
                    obj.start_live_time = start_live_time
                    obj.end_live_time = end_live_time
                    obj.only_subscribed = not free
                    obj.partition = partition_obj
                    obj.is_active = is_active

                obj.sent_gos = False
                obj.save()

                _apply_tags(obj, item.get("tags") or [])

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


def import_connect_knowledgebase(items, *, atomic=True):
    """
    NB: как и в твоём коде — используем item['id'] как PK объекта,
    а НЕ id_gos24. Оставил это поведение.
    """
    if not isinstance(items, list):
        raise ValueError("Ожидается список объектов")
    KIND = ContentItem.KIND_KNOWLEDGEBASE

    imported = created_cnt = updated_cnt = 0
    errors = []

    for idx, item in enumerate(items, start=1):
        try:
            with _atomic_per_item(atomic):
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                obj_id = item["id"]  # строго как в исходнике
                id_gos24_original = item["id_gos24"]

                title = (item.get("title") or "").strip()
                body = item.get("body") or ""
                body_clean = item.get("body_clean") or ""
                youtube_url = item.get("youtube_url") or ""
                content_type = item.get("content_type") or ""
                tutorial_id = item.get("tutorial_id") or ""
                section_id = item.get("section_id") or ""
                anchor_links = bool(item.get("anchor_links", False))
                is_active = bool(item.get("is_active", True))
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                category_obj = None
                if item.get("category_id") is not None:
                    category_obj = Partition.objects.filter(id_gos24=item["category_id"]).first()

                defaults = {
                    "title": title,
                    "id": obj_id,
                    "body": body,
                    "body_clean": body_clean,
                    "youtube_url": youtube_url,
                    "tutorial_id": tutorial_id,
                    "section_id": section_id,
                    "content_type": content_type,
                    "partition": partition_obj,
                    "category": category_obj,
                    "anchor_links": anchor_links,
                    "is_active": is_active,
                    "kind": KIND,
                }

                # тут get_or_create по id (PK)
                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND, id_gos24=id_gos24_original, defaults=defaults
                )

                _set_created_field(obj, created_src)

                if not was_created:
                    obj.title = title
                    obj.body = body
                    obj.id = obj_id
                    obj.body_clean = body_clean
                    obj.youtube_url = youtube_url
                    obj.tutorial_id = tutorial_id
                    obj.section_id = section_id
                    obj.content_type = content_type
                    obj.partition = partition_obj
                    obj.category = category_obj
                    obj.anchor_links = anchor_links
                    obj.is_active = is_active
                    obj.kind = KIND

                obj.sent_gos = False
                obj.save()

                _apply_tags(obj, item.get("tags") or [])

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)
        except Exception as e:
            errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

    return {
        "kind": KIND,
        "imported": imported,
        "created": created_cnt,
        "updated": updated_cnt,
        "errors": errors,
    }


# =========================
# =====   ВСПОМОГАТЕЛЬНОЕ ДЛЯ VIEW  ====
# =========================

def _json_response(data, code=status.HTTP_200_OK):
    return JsonResponse(
        data,
        status=code,
        safe=isinstance(data, dict),
        json_dumps_params={"ensure_ascii": False},
    )


def _read_payload_from_request(request):
    try:
        if "file" in request.FILES:
            raw = request.FILES["file"].read().decode("utf-8")
            return json.loads(raw)
        return request.data
    except json.JSONDecodeError:
        return "__BAD_JSON__"


def _wrap_result_for_http(result, *, include_kind=False):
    errors = result.get("errors") or []
    code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
    payload = {
        "status": "ok" if not errors else "partial",
        "imported": result.get("imported", 0),
        "created": result.get("created", 0),
        "updated": result.get("updated", 0),
        "errors": errors,
    }
    if include_kind and "kind" in result:
        payload["kind"] = result["kind"]
    return payload, code


def _guard_password(request):
    given = request.query_params.get("password")
    return given == IMPORT_PASSWORD


# =========================
# =======   VIEWS   =======
# =========================

class TransferConnectTagImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_tags(payload)
        data, code = _wrap_result_for_http(result)
        return _json_response(data, code)


class TransferConnectPartitionImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_partitions(payload)
        data, code = _wrap_result_for_http(result)
        return _json_response(data, code)


class TransferConnectNewsImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_news(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)


class TransferConnectArticleImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_articles(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)


class TransferConnectOfficialClarificationOrganImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_official_organs(payload)
        data, code = _wrap_result_for_http(result)
        return _json_response(data, code)


class TransferConnectOfficialClarificationImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_official_clarifications(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)


class TransferConnectQuestionImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_questions(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)


class TransferConnectWebinarImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_webinars(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)


class TransferConnectKnowledgebaseImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if not _guard_password(request):
            return _json_response({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        payload = _read_payload_from_request(request)
        if payload == "__BAD_JSON__":
            return _json_response({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)
        if not isinstance(payload, list):
            return _json_response({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        result = import_connect_knowledgebase(payload)
        data, code = _wrap_result_for_http(result, include_kind=True)
        return _json_response(data, code)
