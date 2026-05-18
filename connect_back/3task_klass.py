# ==============================
# Standard library
# ==============================
import os
import re
import csv
import json
import html as html_lib
from uuid import UUID
from typing import Optional, Tuple, List
from datetime import datetime, timedelta, time

# ==============================
# Third-party
# ==============================
import pytz
import pandas as pd

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

from bpms.tasks.models import (
    TaskModel,
    TaskStatusModel,
    TaskExecutionTimeModel,
)

from change_history.models import (
    ChangeHistoryModel,
    ChangeHistoryObjectPropertyModel,
)

import json
import logging
from typing import List

import requests

from common.catalogs.models import (
    KlassificationDimensionModel,
    KlassificationCategoryModel,
    KlassificationModel,
)

logger = logging.getLogger(__name__)

# Настройки Ollama
OLLAMA_URL = "http://172.31.255.5:11434/api/generate"
# OLLAMA_MODEL = "deepseek-r1:8b"
OLLAMA_MODEL = "qwen3:8b"


# OLLAMA_MODEL = "qwen2.5:7b"
def build_prompt_for_dimension(
        dimension_name: str,
        variant_names: List[str],
        task_name: str,
        task_description: str,
        task_result: str,
) -> str:
    """
    Собираем промпт для одного пространства (dimension) и одной задачи.
    На вход: имя пространства, список имён вариантов, название и описание задачи.
    На выходе: текст промпта.
    """

    # список категорий — сразу JSON-массив строк,
    # чтобы модель не придумывала своё форматирование
    variants_json = ",\n".join(f"\"{name}\"" for name in variant_names)
    tr_to_prompt = ''
    if task_result:
        tr_to_prompt = f'Ожидаемый результат по задаче: {task_result}'
    prompt = f"""
Ты — классификатор задач.
Формат выбора:
- Разрешено выбрать НОЛЬ, ОДНУ или НЕСКОЛЬКО категорий.
- Выбор осуществляется строго по ИМЕНИ категории.

Пространство классификации (измерение):
"{dimension_name}"

Список категорий (строки, которые можно использовать в ответе):
[
{variants_json}
]

Контекст задачи:
Название: "{task_name}"
Описание: "{task_description}"
{tr_to_prompt}

Требования к ответу:
- Верни ТОЛЬКО JSON-массив строк — имён выбранных категорий.
- Не добавляй никаких комментариев до или после JSON.
- Не добавляй никаких дополнительных полей.
- Если ни одна категория не подходит, верни пустой массив: [].

Примеры допустимых ответов:
[]
["Баг / Ошибка"]
["Баг / Ошибка", "Финансы / Бухучёт / Экономика"]

Шаблон ответа (замени значения или оставь пустой список):
[
    "..."
]
"""

    print(prompt)
    return prompt.strip()


def call_ollama_json_array(prompt: str) -> List[str]:
    """
    Вызывает Ollama (deepseek-r1:8b) и ожидает в ответе JSON-массив строк.
    Возвращает список имён вариантов.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        #    "format": "json",  # просим Ollama следить за JSON
        "stream": False,  # получить один ответ целиком
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 1024,
            # "no_think": True,  # отключаем рассуждения r1, чтобы не срал в ответ
        },
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    # Для stream=false ollama обычно кладёт итог в поле "response"
    raw = data.get("response", "").strip()

    text = (data.get("response") or "").strip()

    # Ищем последний JSON-массив в тексте
    import re
    matches = re.findall(r"\[[\s\S]*\]", text)
    if not matches:
        raise ValueError(f"В ответе нет JSON-массива: {text!r}")

    raw_array = matches[-1]

    try:
        result = json.loads(raw_array)
    except json.JSONDecodeError as e:
        logger.error("Не удалось распарсить JSON-массив из Ollama: %s; raw=%r", e, raw_array)
        raise

    if not isinstance(result, list):
        raise ValueError(f"Ollama вернула не массив: {result!r}")

    return [str(x) for x in result]


def classify_single_task_dimension_by_names(
        *,
        task_name: str,
        task_description: str,
        task_result: str,
        dimension_name: str,
        variant_names: List[str],
) -> List[str]:
    """
    Высокоуровневая функция:
    - собирает промпт,
    - зовёт deepseek-r1:8b через Ollama,
    - возвращает массив выбранных имён категорий (строки).

    Никакой работы с БД здесь нет — только вызов модели.
    """

    prompt = build_prompt_for_dimension(
        dimension_name=dimension_name,
        variant_names=variant_names,
        task_name=task_name,
        task_description=task_description or "",
        task_result=task_result or '',
    )

    selected_names = call_ollama_json_array(prompt)
    return selected_names


# ===== Ниже пример «боевой обвязки» под твои модели ===== #


def classify_all_tasks_for_all_dimensions():
    """
    Пример массовой классификации:
    - бежим по всем TaskModel
    - по всем измерениям (KlassificationDimensionModel)
    - для каждого создаём KlassificationModel и проставляем категории по имени.

    Можно вызывать из management-команды или celery-задачи.
    """

    dimensions = KlassificationDimensionModel.objects.all()
    # tasks = TaskModel.objects.all()  # сюда можно добавить фильтры

    task_ct = ContentType.objects.get_for_model(TaskModel)

    # --- История в окне для отбора задач
    now = timezone.now()
    date_to = now.replace(hour=23, minute=59, second=59, microsecond=0)
    date_from = date_to - timedelta(days=6)
    date_from = '2025-09-01'

    hist_window_qs = (
        ChangeHistoryModel.objects
        .filter(
            is_active=True,
            related_object__taskmodel__organization__name__in=[
                'Госсектор 24',
                'Delocloud Dev'
            ],
            # related_object__taskmodel__operator__user__email='pribka@mail.ru',
            # related_object__taskmodel__status='need_help',
            related_object__ct=task_ct,
            action_date__gte=date_from,
            action_date__lt=date_to,
        )
        .only("id", "related_object_id")
    )
    task_ids = list(hist_window_qs.values_list("related_object_id", flat=True).distinct())
    if not task_ids:
        return pd.DataFrame(columns=[
            "task_id", "counter", "name", "description_clean",
            "created_at",
            "status",
            "project",
            "organization",
            "date_start_plan",
            "dead_line",
            'priority',
            "first_start_at", "completed_at", "last_completed_at",
            "operator_changes_count", "rework_count",
            "hours_total_all", "hours_total_range",
            "planned_duration_days", "actual_duration_days", "delay_days", "is_delayed",
            "lead_time_days", "time_to_start_days",
            "author_email", "operator_email", "owner_email",
            "visors_emails", "cooperators_emails",
            "comments_count", "unique_participants_count",
            "guests_emails", "guests_count",
        ])

    # --- Подтягиваем задачи + роли и M2M
    # ВАЖНО: без .only(), чтобы не ловить FieldError "deferred + select_related"
    tasks_qs = (
        TaskModel.objects
        .filter(is_active=True,
                pk__in=task_ids)
        .select_related("status", "project", "organization",
                        "author__user", "operator__user", "owner__user")
        .prefetch_related(
            "visors__user",
            "cooperators__user",
        )
    )
    tasks = tasks_qs.order_by('-created_at')

    for task in tasks:
        for dim in dimensions:
            categories_qs = KlassificationCategoryModel.objects.filter(dimension=dim)
            variant_names = list(categories_qs.values_list("name", flat=True))

            if not variant_names:
                continue
            recs = KlassificationModel.objects.filter(related_object=task,
                                                      dimension=dim, ).count()
            if recs > 0:
                print("Пропускаем", task.name, dim.name)
                continue
            try:
                selected_names = classify_single_task_dimension_by_names(
                    task_name=task.name,
                    task_description=getattr(task, "description", "") or "",
                    task_result=getattr(task, "result", "") or "",
                    dimension_name=dim.name,
                    variant_names=variant_names,
                )
                print(task.name, dim.name, selected_names)
            except Exception as exc:
                logger.exception(
                    "Ошибка при классификации задачи %s по измерению %s: %s",
                    task.pk, dim.pk, exc,
                )
                continue

            # фильтруем реальные категории по имени
            selected_cats = categories_qs.filter(name__in=selected_names)

            klass_obj, _new = KlassificationModel.objects.get_or_create(
                related_object=task,
                dimension=dim,
                #  description="",  # сюда можно при желании писать комментарий, если добавишь в промпт
            )
            if selected_cats.exists():
                klass_obj.category.set(selected_cats)


classify_all_tasks_for_all_dimensions()
