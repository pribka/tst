# ==============================
# Standard library
# ==============================
import os
import re
import json
import html as html_lib
from types import SimpleNamespace
from typing import List, Dict

# ==============================
# Django core
# ==============================
import django

# ==============================
# Django settings init
# ==============================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bkz3.settings")
django.setup()

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Exists, OuterRef, CharField
from django.db.models.functions import Cast
from common.utils import wait_if_paused

from bpms.tasks.models import TaskModel, TaskInterestNeedModel
from change_history.models import ChangeHistoryModel
from help_desk.models import HelpDeskTicketModel
from common.catalogs.models import (
    KlassificationDimensionModel,
    KlassificationCategoryModel,
    KlassificationModel,
)
from bpms.tasks.crm_lead_interest import create_interest_from_lead
from bpms.meetings.cron import (
    extract_summary_from_meetings,
    extract_intents_from_meetings,
    extract_efficiency_from_meetings,
)
from analytics.utils.analyze_data import create_digest_data, process_activity_summary_queue

import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

# ==============================
# Настройки Ollama
# ==============================
OLLAMA_URL = "http://172.31.255.5:11434/api/generate" # для прода
# OLLAMA_URL = "https://connect.gos24.kz/olala/generate" # для локального тестирования
OLLAMA_MODEL = "qwen3:8b"
CRM_LEAD_ANALYSIS_BATCH_SIZE = 10

# Один Session на всё
OLLAMA_SESSION = requests.Session()


# ==============================
# Утилиты для HTML-текста задач
# ==============================

def html_to_plain_text(html: str, max_len: int = 2000) -> str:
    """
    Очищаем html-текст:
    - <br>/<p>/<div>/<li> → переводы строк
    - выкидываем все теги
    - декодируем HTML-сущности
    - схлопываем пробелы и пустые строки
    - обрезаем до max_len символов (чтобы не раздувать промпт)
    """
    if not html:
        return ""

    text = html

    # Переводы строк
    text = re.sub(r"</(p|div|li)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<(br|br/)[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Убираем остальные теги
    text = re.sub(r"<[^>]+>", " ", text)

    # HTML-сущности → символы
    text = html_lib.unescape(text)

    # NBSP → пробел
    text = text.replace("\xa0", " ")

    # Схлопываем пробелы
    text = re.sub(r"[ \t]+", " ", text)
    # Схлопываем многократные пустые строки
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    text = text.strip()

    if max_len and len(text) > max_len:
        text = text[:max_len] + "..."

    return text


# ==============================
# Построение промпта (один на задачу)
# ==============================

def build_prompt_for_task_all_dimensions(
        task_name: str,
        task_description_html: str,
        task_result: str,
        dimensions_payload: List[Dict],
) -> str:
    """
    Один промпт на задачу, в нём сразу все измерения и их категории.
    В промпт НЕ летят никакие ID — только имена измерений и имена категорий.
    Ожидаемый ответ модели — JSON-объект:
    {
      "Имя измерения 1": ["Категория 1", "Категория 2"],
      "Имя измерения 2": []
    }
    """
    description_clean = html_to_plain_text(task_description_html or "", max_len=32000)
    # Чтобы кавычки внутри описания не ломали промпт
    description_clean = description_clean.replace('"', "'")
    task_name_safe = (task_name or "").replace('"', "'")

    # Ужимаем JSON измерений: без лишних пробелов
    dims_json = json.dumps(
        dimensions_payload,
        ensure_ascii=False,
        separators=(",", ":")
    )

    tr_to_prompt = ""
    if task_result:
        tr_to_prompt = f"Ожидаемый результат по задаче: {task_result}"

    prompt = f"""
Ты — классификатор задач.
У тебя есть несколько пространств классификации (измерений).
Для КАЖДОГО измерения ты должен:
- внимательно выбрать НОЛЬ, ОДНУ или НЕСКОЛЬКО категорий;
- выбирать категории ТОЛЬКО из списка, который я даю.

Список измерений и их категорий (JSON):

{dims_json}

Контекст задачи:
Название: "{task_name_safe}"
Описание: "{description_clean}"
{tr_to_prompt}

Требования к ответу:
- Верни ТОЛЬКО один JSON-объект.
- Ключи — ИМЕНА измерений (поле "name" из списка выше).
- Значения — JSON-массив ИМЁН категорий (строки).
- Не пихай в категории измерения всё подряд. Подбирай по смыслу.
- В каждом измерении можно использовать ТОЛЬКО те строки категорий, которые перечислены в его списке "categories".
- Нельзя придумывать свои новые категории и менять формулировки.
- Если ни одна категория не подходит для измерения, верни для него пустой массив [].
- Не добавляй текст до или после JSON.

Пример допустимого ответа:
{{
  "1. Тип задачи": ["Доработка / Улучшение"],
  "2. Область деятельности": ["Информационные технологии"],
  "3. Вид работы (формат выполнения)": []
}}
"""
    return prompt.strip()


# ==============================
# Вызов Ollama, парсинг JSON-ответа
# ==============================

def call_ollama_json_object(prompt: str) -> Dict[str, List[str]]:
    """
    Вызывает Ollama и ожидает в ответе JSON-объект вида:
    {
      "Имя измерения": ["Кат1", "Кат2", ...],
      ...
    }

    В случае проблем возвращает {} (пустой словарь).
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",  # просим чистый JSON
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 4096,  # с запасом, чтобы влез весь объект
        },
    }

    try:
        resp = OLLAMA_SESSION.post(
            OLLAMA_URL,
            json=payload,
            timeout=(15, 120),
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error("Ошибка вызова Ollama: %s", e)
        return {}

    try:
        data = resp.json()
    except Exception as e:
        logger.error("Ollama вернул не JSON: %s; raw=%r", e, resp.text[:300])
        return {}

    text = (data.get("response") or "").strip()
    if not text:
        logger.error("Пустой response от Ollama при format=json, data=%r", data)
        return {}

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Ответ Ollama не является JSON-объектом: %r", text[:300])
        return {}

    if not isinstance(result, dict):
        logger.error("Ollama вернула JSON, но не объект: %r", result)
        return {}

    out: Dict[str, List[str]] = {}
    for dim_name, cats in result.items():
        if isinstance(cats, list):
            out[str(dim_name)] = [str(c) for c in cats]
        else:
            out[str(dim_name)] = []

    return out


# ==============================
# Основная логика классификации
# ==============================

def _build_crm_queue_request(ticket):
    profile = ticket.specialist or ticket.author
    if not profile or not getattr(profile, "user", None):
        return None

    return SimpleNamespace(
        user=profile.user,
        query_params={},
        GET={},
        data={},
    )


def process_crm_lead_interest_queue(batch_size=CRM_LEAD_ANALYSIS_BATCH_SIZE):
    """
    Автоматический CRM-проход в общей LLM-очереди task_klass.py.

    Берём лиды, у которых ещё нет активного интереса с заполненной таблицей
    потребностей. Саму бизнес-логику не дублируем: используем тот же helper,
    что и ручная кнопка "LLM-анализ" на фронте.
    """
    lead_id_text = Cast("pk", output_field=CharField())
    active_interests = TaskModel.objects.filter(
        is_active=True,
        task_type_id="interest",
        reason=OuterRef("id_text"),
    )
    active_interest_needs = TaskInterestNeedModel.objects.filter(
        is_active=True,
        task__is_active=True,
        task__task_type_id="interest",
        task__reason=OuterRef("id_text"),
    )

    leads = (
        HelpDeskTicketModel.objects
        .filter(is_active=True, ticket_type_id="lead")
        .filter(Q(specialist__user__isnull=False) | Q(author__user__isnull=False))
        .annotate(id_text=lead_id_text)
        .annotate(
            has_crm_interest=Exists(active_interests),
            has_crm_interest_needs=Exists(active_interest_needs),
        )
        .filter(Q(has_crm_interest=False) | Q(has_crm_interest_needs=False))
        .select_related(
            "specialist__user",
            "author__user",
            "customer_card__org_admin",
            "contact_person",
            "channel",
            "status",
        )
        .order_by("created_at")[:batch_size]
    )

    processed_count = 0
    for ticket in leads:
        wait_if_paused()
        request = _build_crm_queue_request(ticket)
        if request is None:
            logger.error("CRM lead %s skipped: no specialist/author user for queue context", ticket.pk)
            continue

        try:
            result = create_interest_from_lead(ticket, request, force_create=True)
        except Exception:
            logger.exception("CRM lead %s auto analysis failed", ticket.pk)
            continue

        processed_count += 1
        task_id = (result.get("task") or {}).get("id")
        print(
            "CRM lead auto analysis: "
            f"lead={ticket.pk} created={result.get('created')} "
            f"interest={task_id} needs={len(result.get('needs') or [])}"
        )

    return processed_count


def classify_all_tasks_for_all_dimensions():
    """
    Массовая классификация:

    - Берём все измерения и категории.
    - Считаем, сколько активных измерений (у которых есть хотя бы одна категория).
    - Для каждой задачи считаем, сколько у неё уже есть записей KlassificationModel
      по ЭТИМ активным измерениям:
        * если 0 < existing_count < active_dims_count → удаляем ВСЕ эти записи для задачи
          и пересчитываем заново;
        * если existing_count == active_dims_count → задачу пропускаем;
        * если existing_count == 0 → считаем с нуля.
    - При пересчёте делаем ОДИН запрос в Ollama с ВСЕМИ измерениями.
    - ВАЖНО: даже если для измерения массив категорий пустой ([]),
      мы создаём KlassificationModel для этого измерения и задачи,
      и очищаем его .category — это считается «измерение размечено».
    """

    dimensions = list(KlassificationDimensionModel.objects.all())
    if not dimensions:
        return

    task_ct = ContentType.objects.get_for_model(TaskModel)

    # Окно по истории — как у тебя
    now = timezone.now()
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=0)
    date_from = '2025-09-01'

    hist_window_qs = (
        ChangeHistoryModel.objects
        .filter(
            is_active=True,
            related_object__taskmodel__organization__name__in=[
                'Госсектор 24',
                'Delocloud Dev'
            ],
            related_object__ct=task_ct,
            action_date__gte=date_from,
            action_date__lt=date_to,
        )
        .only("id", "related_object_id")
    )
    task_ids = list(hist_window_qs.values_list("related_object_id", flat=True).distinct())
    if not task_ids:
        return

    tasks_qs = (
        TaskModel.objects
        .filter(is_active=True, pk__in=task_ids)
        .select_related(
            "status", "project", "organization",
            "author__user", "operator__user", "owner__user"
        )
        .prefetch_related(
            "visors__user",
            "cooperators__user",
        )
        .order_by('-created_at')
    )
    tasks = list(tasks_qs)
    if not tasks:
        return

    # Категории по измерениям + payload для промпта
    dim_to_cats_qs: Dict[int, 'KlassificationCategoryModel.objects'] = {}
    dims_payload: List[Dict] = []

    for dim in dimensions:
        cats_qs = KlassificationCategoryModel.objects.filter(dimension=dim)
        dim_to_cats_qs[dim.id] = cats_qs
        cats = list(cats_qs.values_list("name", flat=True))
        if not cats:
            continue

        dims_payload.append({
            "name": dim.name,
            "categories": cats,
        })

    if not dims_payload:
        return

    active_dimensions = [
        dim for dim in dimensions
        if dim_to_cats_qs.get(dim.id) and dim_to_cats_qs[dim.id].exists()
    ]
    active_dims_count = len(active_dimensions)
    if active_dims_count == 0:
        return

    # Основной цикл по задачам
    for task in tasks:
        wait_if_paused()
        existing_klass_qs = KlassificationModel.objects.filter(
            related_object=task,
            dimension__in=active_dimensions,
        )
        existing_count = existing_klass_qs.count()

        if 0 < existing_count < active_dims_count:
            # Есть, но не все → удаляем и пересчитываем
            existing_klass_qs.delete()
            existing_count = 0

        if existing_count == active_dims_count:
            # Уже размечены все активные измерения — пропускаем
            continue

        # Пересчитываем ВСЕ активные измерения для задачи
        prompt = build_prompt_for_task_all_dimensions(
            task_name=task.name,
            task_description_html=getattr(task, "description", "") or "",
            task_result=getattr(task, "result", "") or "",
            dimensions_payload=dims_payload,
        )

        classification_result = call_ollama_json_object(prompt)

        # Чистый текст для логов
        description_clean = html_to_plain_text(getattr(task, "description", "") or "")
        task_res = getattr(task, "result", "") or ""

        # ===== ЕДИНСТВЕННЫЙ ЧЕЛОВЕКОЧИТАЕМЫЙ ВЫВОД В КОНСОЛЬ =====
        print("\n" + "=" * 80)
        print(f"Название: {task.name}")
        print(f"Описание: {description_clean}")
        print(f"Ожидаемый результат: {task_res}")
        print("\nКлассификация (по измерениям):")
        print(json.dumps(classification_result, ensure_ascii=False, indent=2))
        print("=" * 80 + "\n")
        # =======================================================

        if classification_result is None:
            # На всякий случай
            continue

        # Применяем ответ к активным измерениям
        for dim in active_dimensions:
            cats_qs = dim_to_cats_qs.get(dim.id)
            if not cats_qs or not cats_qs.exists():
                continue

            # Даже если ключа нет — считаем, что [] (измерение размечено, но без категорий)
            selected_names = classification_result.get(dim.name)
            if not isinstance(selected_names, list):
                selected_names = []

            selected_cats = cats_qs.filter(name__in=selected_names)

            klass_obj, _ = KlassificationModel.objects.get_or_create(
                related_object=task,
                dimension=dim,
            )

            if selected_cats.exists():
                klass_obj.category.set(selected_cats)
            else:
                # Пустой массив → очищаем категории, но запись оставляем
                klass_obj.category.clear()


# ==============================
# Entrypoint
# ==============================

if __name__ == "__main__":
    wait_if_paused()

    jobs = [
        ("process_crm_lead_interest_queue", process_crm_lead_interest_queue),
        ("classify_all_tasks_for_all_dimensions", classify_all_tasks_for_all_dimensions),
        ("extract_intents_from_meetings", extract_intents_from_meetings),
        ("extract_summary_from_meetings", extract_summary_from_meetings),
        ("extract_efficiency_from_meetings", extract_efficiency_from_meetings),
        ("process_activity_summary_queue", process_activity_summary_queue),
    ]

    for job_name, job_func in jobs:
        wait_if_paused()
        try:
            job_func()
        except Exception:
            print("LLM job failed: %s", job_name)
            logger.exception("LLM job failed: %s", job_name)
