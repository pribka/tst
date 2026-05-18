# views.py
import json
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from content_item_gos24.models import Tag, Partition, ContentItem, OfficialClarificationOrgan

# задаёшь здесь и больше нигде
IMPORT_PASSWORD = "my_secret_password"

class TransferConnectTagImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # 1) пароль только из query
        given = request.query_params.get("password")
        if given != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # 2) читаем данные: либо файл, либо распарсенный JSON
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id' (id_gos24)")
                id_gos24 = int(item["id"])
                title = (item.get("title") or "").strip()
                is_active = bool(item.get("is_active", True))
                main = bool(item.get("main", False))
                created_str = item.get("created")

                obj, was_created = Tag.objects.get_or_create(
                    id_gos24=id_gos24,
                    defaults={"name": title, "is_active": is_active, "main": main}
                )

                if was_created and created_str:
                    dt = parse_datetime(created_str)
                    if dt:
                        obj.created = dt

                if not was_created:
                    obj.name = title
                    obj.is_active = is_active
                    obj.main = main
                obj.sent_gos = False
                obj.save()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectPartitionImportAPIView(APIView):
    """
    Импорт разделов:
    [
      {"id": 650, "name": "Новое на портале"},
      ...
    ]
    - id -> Partition.id_gos24
    - name -> Partition.name
    """
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # 1) проверка пароля
        given = request.query_params.get("password")
        if given != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # 2) загрузка данных
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        imported = created_cnt = updated_cnt = 0
        errors = []

        # 3) сохранение в БД
        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id' (id_gos24)")
                if "name" not in item:
                    raise ValueError("Отсутствует поле 'name'")

                id_gos24 = int(item["id"])
                name = (item.get("name") or "").strip()

                obj, was_created = Partition.objects.get_or_create(
                    id_gos24=id_gos24,
                    defaults={"name": name}
                )

                if not was_created:
                    obj.name = name
                obj.sent_gos = False
                obj.save()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectNewsImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_NEWS_PUBLICATIONS_GOS24
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title             = (item.get("title") or "").strip()
                description       = item.get("description") or ""
                description_clean = item.get("description_clean") or ""
                body              = item.get("body") or ""
                body_clean        = item.get("body_clean") or ""
                image             = item.get("image") or None

                only_subscribed   = bool(item.get("only_subscribed", False))
                main_in_week      = bool(item.get("main_in_week", False))
                anchor_links      = bool(item.get("anchor_links", False))
                is_active         = bool(item.get("is_active", True))

                pub_dt = parse_datetime(item["publication_date"]) if item.get("publication_date") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24,
                    defaults={
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
                )

                obj.created_at = created_src

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

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectArticleImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_ARTICLE
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title             = (item.get("title") or "").strip()
                description       = item.get("description") or ""
                description_clean = item.get("description_clean") or ""
                body              = item.get("body") or ""
                body_clean        = item.get("body_clean") or ""
                image             = item.get("image") or None

                only_subscribed   = bool(item.get("only_subscribed", False))
                main_in_week      = bool(item.get("main_in_week", False))
                anchor_links      = bool(item.get("anchor_links", False))
                is_active         = bool(item.get("is_active", True))

                pub_dt = parse_datetime(item["publication_date"]) if item.get("publication_date") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24,
                    defaults={
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
                )

                obj.created_at = created_src

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

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectOfficialClarificationOrganImportAPIView(APIView):
    """
    Импорт официальных органов из JSON.
    Формат:
    [
      { "id": 1, "title": "Министерство финансов" },
      { "id": 2, "title": "Министерство юстиции" }
    ]
    - id -> id_gos24
    """
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем JSON или файл
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item or "title" not in item:
                    raise ValueError("Отсутствует 'id' или 'title'")

                id_gos24 = int(item["id"])
                title = (item.get("title") or "").strip()

                obj, was_created = OfficialClarificationOrgan.objects.get_or_create(
                    id_gos24=id_gos24,
                    defaults={"title": title}
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

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectOfficialClarificationImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_OFFICIAL
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title             = (item.get("title") or "").strip()
                description       = item.get("description") or ""
                description_clean = item.get("description_clean") or ""
                body              = item.get("body") or ""
                body_clean        = item.get("body_clean") or ""
                image             = item.get("image") or None

                only_subscribed   = bool(item.get("only_subscribed", False))
                main_in_week      = bool(item.get("main_in_week", False))
                anchor_links      = bool(item.get("anchor_links", False))
                is_active         = bool(item.get("is_active", True))

                pub_dt = parse_datetime(item["publication_date"]) if item.get("publication_date") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    if item.get("partition_id")  == 100:
                        partition_obj = Partition.objects.filter(id_gos24=100).first()
                    elif item.get("partition_id") == 110:
                        partition_obj = Partition.objects.filter(id_gos24=300).first()
                    elif item.get("partition_id")  == 200:
                        partition_obj = Partition.objects.filter(id_gos24=710).first()
                    elif item.get("partition_id") == 300:
                        partition_obj = Partition.objects.filter(id_gos24=310).first()
                    else:
                        partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                organ_obj = None
                if item.get("organ_id") is not None:
                    organ_obj = OfficialClarificationOrgan.objects.filter(id_gos24=item["organ_id"]).first()


                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24,
                    defaults={
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
                )

                obj.created_at = created_src

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

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectQuestionImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_QA
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                question       = item.get("question") or ""
                answer       = item.get("question") or ""
                question_html = item.get("question_html") or ""
                answer_html = item.get("answer_html") or ""

                main_in_week      = bool(item.get("main_in_week", False))
                is_active         = bool(item.get("is_active", True))

                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24,
                    defaults={
                        "title": question,
                        "question": question,
                        "question_html": question_html,
                        "answer": answer,
                        "answer_html": answer_html,
                        "partition": partition_obj,
                        "main_in_week": main_in_week,
                        "is_active": is_active,
                    }
                )

                obj.created_at = created_src

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

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectWebinarImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_WEBINAR
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = int(item["id"])

                title             = (item.get("title") or "").strip()
                body              = item.get("body") or ""
                body_clean        = item.get("body_clean") or ""
                webinar_date        = item.get("webinar_date") or ""
                youtube_url        = item.get("youtube_url") or ""
                content_type        = item.get("content_type") or ""
                broadcast        = item.get("broadcast") or ""
                lecturer_full_name        = item.get("lecturer_full_name") or ""

                spend   = bool(item.get("spend", False))
                free   = bool(item.get("free", False))
                is_active         = bool(item.get("is_active", True))

                planned_date = item.get("planned_date")
                start_live_time = parse_datetime(item["start_live_time"]) if item.get("start_live_time") else None
                end_live_time = parse_datetime(item["end_live_time"]) if item.get("end_live_time") else None
                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24,
                    defaults={
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
                )

                obj.created_at = created_src

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

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


class TransferConnectKnowledgebaseImportAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def _json(self, data, code=status.HTTP_200_OK):
        return JsonResponse(
            data, status=code,
            safe=isinstance(data, dict),
            json_dumps_params={"ensure_ascii": False}
        )

    def post(self, request, *args, **kwargs):
        # проверка пароля
        if request.query_params.get("password") != IMPORT_PASSWORD:
            return self._json({"error": "Доступ запрещён"}, status.HTTP_403_FORBIDDEN)

        # читаем данные
        try:
            if 'file' in request.FILES:
                raw = request.FILES['file'].read().decode('utf-8')
                payload = json.loads(raw)
            else:
                payload = request.data
        except json.JSONDecodeError:
            return self._json({"error": "Некорректный JSON"}, status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, list):
            return self._json({"error": "Ожидается список объектов"}, status.HTTP_400_BAD_REQUEST)

        KIND = ContentItem.KIND_KNOWLEDGEBASE
        imported = created_cnt = updated_cnt = 0
        errors = []

        for idx, item in enumerate(payload, start=1):
            try:
                if "id" not in item:
                    raise ValueError("Отсутствует поле 'id'")
                id_gos24 = item["id"]
                id_gos24_original = item["id_gos24"]

                title             = (item.get("title") or "").strip()
                body              = item.get("body") or ""
                body_clean        = item.get("body_clean") or ""
                youtube_url        = item.get("youtube_url") or ""
                content_type        = item.get("content_type") or ""
                tutorial_id        = item.get("tutorial_id") or ""
                section_id        = item.get("section_id") or ""

                anchor_links   = bool(item.get("anchor_links", False))
                is_active         = bool(item.get("is_active", True))

                created_src = parse_datetime(item["created"]) if item.get("created") else None

                partition_obj = None
                if item.get("partition_id") is not None:
                    partition_obj = Partition.objects.filter(id_gos24=item["partition_id"]).first()

                category_obj = None
                if item.get("category_id") is not None:
                    category_obj = Partition.objects.filter(id_gos24=item["category_id"]).first()

                obj, was_created = ContentItem.objects.get_or_create(
                    kind=KIND,
                    id_gos24=id_gos24_original,
                    defaults={
                        "id": id_gos24,
                        "title": title,
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
                    }
                )

                obj.created_at = created_src

                if not was_created:
                    obj.id = id_gos24
                    obj.title = title
                    obj.id_gos24 = id_gos24_original
                    obj.body = body
                    obj.body_clean = body_clean
                    obj.youtube_url = youtube_url
                    obj.tutorial_id = tutorial_id
                    obj.section_id = section_id
                    obj.content_type = content_type
                    obj.partition = partition_obj
                    obj.category = category_obj
                    obj.anchor_links = anchor_links
                    obj.is_active = is_active
                obj.sent_gos = False
                obj.save()

                tags_ids = item.get("tags") or []
                tags_qs = Tag.objects.filter(id_gos24__in=tags_ids)
                if not tags_qs.exists() and tags_ids:
                    tags_qs = Tag.objects.filter(id__in=tags_ids)
                obj.tags.set(tags_qs) if tags_qs.exists() else obj.tags.clear()

                imported += 1
                created_cnt += int(was_created)
                updated_cnt += int(not was_created)

            except Exception as e:
                errors.append({"index": idx, "id": item.get("id"), "error": str(e)})

        code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return self._json({
            "status": "ok" if not errors else "partial",
            "kind": KIND,
            "imported": imported,
            "created": created_cnt,
            "updated": updated_cnt,
            "errors": errors
        }, code)


