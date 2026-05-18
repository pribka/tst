#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import warnings
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import django

import plotly.graph_objects as go
import plotly.io as pio
from plotly.colors import qualitative

try:
    from bs4 import MarkupResemblesLocatorWarning
except Exception:  # pragma: no cover - optional dependency guard
    MarkupResemblesLocatorWarning = None


ContentType = None
Count = None
Q = None
timezone = None
TaskModel = None
KlassificationCategoryModel = None
KlassificationModel = None


PROJECT_ID_FIELD = "related_object__taskmodel__project_id"
PROJECT_NAME_FIELD = "related_object__taskmodel__project__name"
DIMENSION_ID_FIELD = "dimension_id"
DIMENSION_NAME_FIELD = "dimension__name"
DIMENSION_CREATED_AT_FIELD = "dimension__created_at"
CATEGORY_ID_FIELD = "category__id"
CATEGORY_NAME_FIELD = "category__name"
TASK_ID_FIELD = "related_object_id"
TASK_NAME_FIELD = "related_object__taskmodel__name"
TASK_COUNTER_FIELD = "related_object__taskmodel__counter"
NO_PROJECT_LABEL = "Без проекта"
NO_DIMENSION_LABEL = "Без измерения"
NO_NAME_LABEL = "Без названия"
DEFAULT_TITLE = "Отчет по классификациям задач"
COLOR_SEQUENCE = (
    qualitative.Plotly
    + qualitative.Safe
    + qualitative.Set3
)


@dataclass
class CategoryRow:
    category_id: Optional[str]
    category_name: str
    tasks_count: int
    tasks: List["TaskInfo"]


@dataclass
class TaskInfo:
    task_id: str
    task_name: str
    task_counter: str


@dataclass
class DimensionRow:
    dimension_id: Optional[str]
    dimension_name: str
    created_at_sort_value: object
    distinct_tasks: int
    uncategorized_tasks: int
    categories: List[CategoryRow]


@dataclass
class ProjectRow:
    project_id: Optional[str]
    project_name: str
    dimensions: List[DimensionRow]


def normalize_name(value: Optional[str], fallback: str) -> str:
    if value is None:
        return fallback
    cleaned = str(value).strip()
    return cleaned or fallback


def project_sort_key(item: ProjectRow) -> Tuple[int, str]:
    return (1 if item.project_name == NO_PROJECT_LABEL else 0, item.project_name.lower())


def dimension_sort_key(item: DimensionRow) -> Tuple[int, object, str]:
    return (
        1 if item.created_at_sort_value is None else 0,
        item.created_at_sort_value or "",
        item.dimension_name.lower(),
    )


def category_sort_key(item: CategoryRow) -> str:
    return item.category_name.lower()


def task_sort_key(item: TaskInfo) -> Tuple[str, str, str]:
    return (item.task_counter.lower(), item.task_name.lower(), item.task_id)


def build_color_map(categories: List[CategoryRow]) -> Dict[Optional[str], str]:
    color_map: Dict[Optional[str], str] = {}
    for index, item in enumerate(categories):
        color_map[item.category_id] = COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)]
    return color_map


def build_chart_legend_html(categories: List[CategoryRow], color_map: Dict[Optional[str], str]) -> str:
    if not categories:
        return ""

    items = []
    for item in categories:
        color = color_map.get(item.category_id, "#999999")
        items.append(
            "<div class='chart-legend-item'>"
            f"<span class='chart-legend-swatch' style='background:{escape(color)}'></span>"
            f"<span class='chart-legend-label'>{escape(item.category_name)}</span>"
            "</div>"
        )
    return f"<div class='chart-legend'>{''.join(items)}</div>"


def bootstrap_django() -> None:
    global ContentType, Count, Q, timezone, TaskModel, KlassificationCategoryModel, KlassificationModel

    if ContentType is not None:
        return

    print("Bootstrapping Django...", flush=True)
    if MarkupResemblesLocatorWarning is not None:
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bkz3.settings")
    django.setup()

    from django.contrib.contenttypes.models import ContentType as DjangoContentType
    from django.db.models import Count as DjangoCount
    from django.db.models import Q as DjangoQ
    from django.utils import timezone as django_timezone

    from bpms.tasks.models import TaskModel as DjangoTaskModel
    from common.catalogs.models import (
        KlassificationCategoryModel as DjangoKlassificationCategoryModel,
        KlassificationModel as DjangoKlassificationModel,
    )

    ContentType = DjangoContentType
    Count = DjangoCount
    Q = DjangoQ
    timezone = django_timezone
    TaskModel = DjangoTaskModel
    KlassificationCategoryModel = DjangoKlassificationCategoryModel
    KlassificationModel = DjangoKlassificationModel
    print("Django is ready.", flush=True)


def collect_report_data() -> Dict[str, object]:
    bootstrap_django()
    print("Loading classification aggregates...", flush=True)
    task_ct = ContentType.objects.get_for_model(TaskModel)
    base_qs = KlassificationModel.objects.filter(
        is_active=True,
        related_object__ct=task_ct,
    ).filter(
        Q(related_object__taskmodel__project__name__icontains="Коннект")
        | Q(related_object__taskmodel__project__name__icontains="АУЦА")
    )

    distinct_tasks_total = base_qs.values("related_object_id").distinct().count()
    klassifications_total = base_qs.count()

    dimension_rows = list(
        base_qs.values(
            PROJECT_ID_FIELD,
            PROJECT_NAME_FIELD,
            DIMENSION_ID_FIELD,
            DIMENSION_NAME_FIELD,
            DIMENSION_CREATED_AT_FIELD,
        )
        .annotate(tasks_count=Count("related_object_id", distinct=True))
        .order_by(PROJECT_NAME_FIELD, DIMENSION_CREATED_AT_FIELD, DIMENSION_NAME_FIELD)
    )

    if not dimension_rows:
        print("No active task classifications found.", flush=True)
        return {
            "projects": [],
            "distinct_tasks_total": distinct_tasks_total,
            "klassifications_total": klassifications_total,
            "charts_total": 0,
        }

    dimension_ids = [row[DIMENSION_ID_FIELD] for row in dimension_rows if row[DIMENSION_ID_FIELD] is not None]

    catalog_categories_rows = list(
        KlassificationCategoryModel.objects.filter(dimension_id__in=dimension_ids)
        .values("dimension_id", "id", "name")
        .order_by("dimension__name", "name", "id")
    )

    category_rows = list(
        base_qs.filter(category__isnull=False)
        .values(
            PROJECT_ID_FIELD,
            PROJECT_NAME_FIELD,
            DIMENSION_ID_FIELD,
            DIMENSION_NAME_FIELD,
            DIMENSION_CREATED_AT_FIELD,
            CATEGORY_ID_FIELD,
            CATEGORY_NAME_FIELD,
        )
        .annotate(tasks_count=Count("related_object_id", distinct=True))
        .order_by(PROJECT_NAME_FIELD, DIMENSION_CREATED_AT_FIELD, CATEGORY_NAME_FIELD)
    )

    category_task_rows = list(
        base_qs.filter(category__isnull=False)
        .values(
            PROJECT_ID_FIELD,
            DIMENSION_ID_FIELD,
            CATEGORY_ID_FIELD,
            TASK_ID_FIELD,
            TASK_NAME_FIELD,
            TASK_COUNTER_FIELD,
        )
        .distinct()
        .order_by(
            PROJECT_ID_FIELD,
            DIMENSION_ID_FIELD,
            CATEGORY_ID_FIELD,
            TASK_COUNTER_FIELD,
            TASK_NAME_FIELD,
            TASK_ID_FIELD,
        )
    )

    uncategorized_rows = list(
        base_qs.filter(category__isnull=True)
        .values(
            PROJECT_ID_FIELD,
            PROJECT_NAME_FIELD,
            DIMENSION_ID_FIELD,
            DIMENSION_NAME_FIELD,
            DIMENSION_CREATED_AT_FIELD,
        )
        .annotate(tasks_count=Count("related_object_id", distinct=True))
        .order_by(PROJECT_NAME_FIELD, DIMENSION_CREATED_AT_FIELD, DIMENSION_NAME_FIELD)
    )

    categories_by_dimension: Dict[Optional[str], List[Dict[str, object]]] = defaultdict(list)
    known_category_ids: Dict[Optional[str], set] = defaultdict(set)
    for row in catalog_categories_rows:
        dimension_id = row["dimension_id"]
        category_id = row["id"]
        categories_by_dimension[dimension_id].append(
            {
                "category_id": category_id,
                "category_name": normalize_name(row["name"], NO_NAME_LABEL),
            }
        )
        known_category_ids[dimension_id].add(category_id)

    for row in category_rows:
        dimension_id = row[DIMENSION_ID_FIELD]
        category_id = row[CATEGORY_ID_FIELD]
        if category_id in known_category_ids[dimension_id]:
            continue
        categories_by_dimension[dimension_id].append(
            {
                "category_id": category_id,
                "category_name": normalize_name(row[CATEGORY_NAME_FIELD], NO_NAME_LABEL),
            }
        )
        known_category_ids[dimension_id].add(category_id)

    for dimension_id in list(categories_by_dimension.keys()):
        categories_by_dimension[dimension_id].sort(key=lambda item: item["category_name"].lower())

    tasks_by_bucket: Dict[Tuple[str, Optional[str], Optional[str]], List[TaskInfo]] = defaultdict(list)
    for row in category_task_rows:
        raw_project_id = row[PROJECT_ID_FIELD]
        project_key = str(raw_project_id) if raw_project_id is not None else "__no_project__"
        raw_dimension_id = row[DIMENSION_ID_FIELD]
        raw_category_id = row[CATEGORY_ID_FIELD]
        tasks_by_bucket[(project_key, raw_dimension_id, raw_category_id)].append(
            TaskInfo(
                task_id=str(row[TASK_ID_FIELD]),
                task_name=normalize_name(row[TASK_NAME_FIELD], NO_NAME_LABEL),
                task_counter=normalize_name(row[TASK_COUNTER_FIELD], "-"),
            )
        )

    for bucket_key in list(tasks_by_bucket.keys()):
        tasks_by_bucket[bucket_key].sort(key=task_sort_key)

    projects_map: Dict[str, Dict[str, object]] = {}
    dimensions_map: Dict[Tuple[str, Optional[str]], Dict[str, object]] = {}

    for row in dimension_rows:
        raw_project_id = row[PROJECT_ID_FIELD]
        project_key = str(raw_project_id) if raw_project_id is not None else "__no_project__"
        project_entry = projects_map.setdefault(
            project_key,
            {
                "project_id": raw_project_id,
                "project_name": normalize_name(row[PROJECT_NAME_FIELD], NO_PROJECT_LABEL),
                "dimensions": {},
            },
        )

        raw_dimension_id = row[DIMENSION_ID_FIELD]
        dimension_key = (project_key, raw_dimension_id)
        dimension_entry = {
            "dimension_id": raw_dimension_id,
            "dimension_name": normalize_name(row[DIMENSION_NAME_FIELD], NO_DIMENSION_LABEL),
            "created_at_sort_value": row[DIMENSION_CREATED_AT_FIELD],
            "distinct_tasks": int(row["tasks_count"]),
            "uncategorized_tasks": 0,
            "category_counts": {
                item["category_id"]: 0 for item in categories_by_dimension.get(raw_dimension_id, [])
            },
        }
        project_entry["dimensions"][raw_dimension_id] = dimension_entry
        dimensions_map[dimension_key] = dimension_entry

    for row in category_rows:
        raw_project_id = row[PROJECT_ID_FIELD]
        project_key = str(raw_project_id) if raw_project_id is not None else "__no_project__"
        raw_dimension_id = row[DIMENSION_ID_FIELD]
        dimension_entry = dimensions_map.get((project_key, raw_dimension_id))
        if dimension_entry is None:
            continue
        dimension_entry["category_counts"][row[CATEGORY_ID_FIELD]] = int(row["tasks_count"])

    for row in uncategorized_rows:
        raw_project_id = row[PROJECT_ID_FIELD]
        project_key = str(raw_project_id) if raw_project_id is not None else "__no_project__"
        raw_dimension_id = row[DIMENSION_ID_FIELD]
        dimension_entry = dimensions_map.get((project_key, raw_dimension_id))
        if dimension_entry is None:
            continue
        dimension_entry["uncategorized_tasks"] = int(row["tasks_count"])

    projects: List[ProjectRow] = []
    charts_total = 0
    for project_entry in projects_map.values():
        dimensions: List[DimensionRow] = []
        for dimension_id, dimension_entry in project_entry["dimensions"].items():
            category_items = categories_by_dimension.get(dimension_id, [])
            categories = [
                CategoryRow(
                    category_id=item["category_id"],
                    category_name=item["category_name"],
                    tasks_count=dimension_entry["category_counts"].get(item["category_id"], 0),
                    tasks=tasks_by_bucket.get(
                        (str(project_entry["project_id"]) if project_entry["project_id"] is not None else "__no_project__", dimension_id, item["category_id"]),
                        [],
                    ),
                )
                for item in category_items
            ]
            categories.sort(key=category_sort_key)
            dimensions.append(
                DimensionRow(
                    dimension_id=dimension_entry["dimension_id"],
                    dimension_name=dimension_entry["dimension_name"],
                    created_at_sort_value=dimension_entry["created_at_sort_value"],
                    distinct_tasks=dimension_entry["distinct_tasks"],
                    uncategorized_tasks=dimension_entry["uncategorized_tasks"],
                    categories=categories,
                )
            )
            charts_total += 1

        dimensions.sort(key=dimension_sort_key)
        projects.append(
            ProjectRow(
                project_id=project_entry["project_id"],
                project_name=project_entry["project_name"],
                dimensions=dimensions,
            )
        )

    projects.sort(key=project_sort_key)

    print(
        f"Aggregates loaded: {len(projects)} projects, {charts_total} dimension charts.",
        flush=True,
    )
    return {
        "projects": projects,
        "distinct_tasks_total": distinct_tasks_total,
        "klassifications_total": klassifications_total,
        "charts_total": charts_total,
    }


def build_pie_chart_html(
    project_name: str,
    dimension_name: str,
    categories: List[CategoryRow],
    include_plotlyjs: bool,
) -> str:
    positive_categories = [item for item in categories if item.tasks_count > 0]
    if not positive_categories:
        return "<div class='empty-chart'>Нет категорий с задачами для построения диаграммы.</div>"

    color_map = build_color_map(positive_categories)
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[item.category_name for item in positive_categories],
                values=[item.tasks_count for item in positive_categories],
                hole=0.36,
                sort=False,
                textinfo="percent",
                textposition="inside",
                hovertemplate="%{label}<br>Задач: %{value}<br>Доля: %{percent}<extra></extra>",
                marker={
                    "colors": [color_map[item.category_id] for item in positive_categories],
                    "line": {"color": "#ffffff", "width": 1.5},
                },
            )
        ]
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin={"t": 16, "r": 20, "b": 24, "l": 20},
        showlegend=False,
    )
    chart_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )
    legend_html = build_chart_legend_html(positive_categories, color_map)
    return f"{chart_html}{legend_html}"


def build_task_list_html(tasks: List[TaskInfo]) -> str:
    if not tasks:
        return "<div class='empty-task-list'>Задачи по этой категории не найдены.</div>"

    items = []
    for task in tasks:
        task_title = f"{task.task_counter} | {task.task_name}"
        task_url = f"https://connect.gos24.kz?task={escape(task.task_id)}"
        items.append(
            "<li class='task-item'>"
            f"<a href='{task_url}' target='_blank' rel='noopener noreferrer'>{escape(task_title)}</a>"
            "</li>"
        )
    return f"<ul class='task-list'>{''.join(items)}</ul>"


def build_category_table(categories: List[CategoryRow]) -> str:
    if not categories:
        return "<div class='empty-table'>Для этого измерения не найдены значения категорий.</div>"

    rows = []
    for item in categories:
        css_class = "zero-count" if item.tasks_count == 0 else ""
        rows.append(
            (
                f"<tr class='{css_class}'>"
                "<td>"
                "<details class='task-details'>"
                f"<summary>{escape(item.category_name)}</summary>"
                f"{build_task_list_html(item.tasks)}"
                "</details>"
                "</td>"
                f"<td class='number-cell'>{item.tasks_count}</td>"
                "</tr>"
            )
        )
    body = "".join(rows)
    return (
        "<table class='category-table'>"
        "<thead><tr><th>Категория</th><th>Задач</th></tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
    )


def build_html(report_data: Dict[str, object], title: str) -> str:
    bootstrap_django()
    generated_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S %Z")
    projects: List[ProjectRow] = report_data["projects"]
    charts_total = int(report_data["charts_total"])
    distinct_tasks_total = int(report_data["distinct_tasks_total"])
    klassifications_total = int(report_data["klassifications_total"])

    summary_html = (
        "<div class='summary-grid'>"
        f"<div class='summary-card'><span class='summary-label'>Проектов</span><strong>{len(projects)}</strong></div>"
        f"<div class='summary-card'><span class='summary-label'>Диаграмм</span><strong>{charts_total}</strong></div>"
        f"<div class='summary-card'><span class='summary-label'>Задач с классификацией</span><strong>{distinct_tasks_total}</strong></div>"
        f"<div class='summary-card'><span class='summary-label'>Записей KlassificationModel</span><strong>{klassifications_total}</strong></div>"
        "</div>"
    )

    if not projects:
        projects_html = (
            "<section class='project-section'>"
            "<div class='empty-report'>Активные классификации для задач не найдены.</div>"
            "</section>"
        )
    else:
        include_plotlyjs = True
        rendered_projects = []
        for project in projects:
            dimension_cards = []
            for dimension in project.dimensions:
                chart_html = build_pie_chart_html(
                    project_name=project.project_name,
                    dimension_name=dimension.dimension_name,
                    categories=dimension.categories,
                    include_plotlyjs=include_plotlyjs,
                )
                include_plotlyjs = False

                note_parts = [f"Классифицировано задач: {dimension.distinct_tasks}"]
                if dimension.uncategorized_tasks:
                    note_parts.append(f"Без категории: {dimension.uncategorized_tasks}")

                dimension_cards.append(
                    (
                        "<article class='dimension-card'>"
                        f"<div class='dimension-header'><h3>{escape(dimension.dimension_name)}</h3>"
                        f"<p>{escape(' | '.join(note_parts))}</p></div>"
                        f"<div class='chart-wrap'>{chart_html}</div>"
                        f"{build_category_table(dimension.categories)}"
                        "</article>"
                    )
                )

            project_html = (
                "<section class='project-section'>"
                f"<div class='project-header'><h2>{escape(project.project_name)}</h2>"
                f"<p>Измерений с данными: {len(project.dimensions)}</p></div>"
                "<div class='dimension-grid'>"
                f"{''.join(dimension_cards)}"
                "</div>"
                "</section>"
            )
            rendered_projects.append(project_html)
        projects_html = "".join(rendered_projects)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
        :root {{
            --bg: #f4f1ea;
            --panel: #fffdf8;
            --panel-2: #f8f5ee;
            --border: #dbcdb4;
            --text: #2f2417;
            --muted: #6f6255;
            --accent: #a64b2a;
            --accent-soft: #f2d6c8;
            --shadow: 0 16px 42px rgba(57, 41, 24, 0.09);
            --radius: 20px;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(166, 75, 42, 0.12), transparent 30%),
                linear-gradient(180deg, #f6f1e8 0%, #f2ede5 100%);
            color: var(--text);
        }}
        .page {{
            max-width: 1500px;
            margin: 0 auto;
            padding: 32px 24px 64px;
        }}
        .hero {{
            background: linear-gradient(135deg, rgba(255, 253, 248, 0.96), rgba(247, 239, 226, 0.98));
            border: 1px solid var(--border);
            border-radius: calc(var(--radius) + 6px);
            box-shadow: var(--shadow);
            padding: 28px;
            margin-bottom: 24px;
        }}
        .hero h1 {{
            margin: 0 0 10px;
            font-size: 34px;
            line-height: 1.15;
        }}
        .hero p {{
            margin: 0;
            color: var(--muted);
            max-width: 980px;
            line-height: 1.5;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin: 24px 0;
        }}
        .summary-card {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: var(--shadow);
        }}
        .summary-card strong {{
            display: block;
            font-size: 30px;
            margin-top: 6px;
        }}
        .summary-label {{
            color: var(--muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .project-section {{
            margin-top: 28px;
        }}
        .project-header {{
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(111, 98, 85, 0.24);
        }}
        .project-header h2 {{
            margin: 0;
            font-size: 28px;
        }}
        .project-header p {{
            margin: 0;
            color: var(--muted);
        }}
        .dimension-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 18px;
        }}
        .dimension-card {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            width: 100%;
        }}
        .dimension-header {{
            padding: 18px 20px 0;
        }}
        .dimension-header h3 {{
            margin: 0;
            font-size: 22px;
        }}
        .dimension-header p {{
            margin: 8px 0 0;
            color: var(--muted);
        }}
        .chart-wrap {{
            padding: 8px 12px 0;
        }}
        .chart-legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 10px 14px;
            margin: 10px 16px 18px;
            padding: 14px 16px;
            background: var(--panel-2);
            border: 1px solid rgba(219, 205, 180, 0.75);
            border-radius: 14px;
        }}
        .chart-legend-item {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            min-width: 0;
        }}
        .chart-legend-swatch {{
            width: 14px;
            height: 14px;
            flex: 0 0 14px;
            border-radius: 4px;
            margin-top: 2px;
        }}
        .chart-legend-label {{
            font-size: 14px;
            line-height: 1.35;
            word-break: break-word;
        }}
        .category-table {{
            width: calc(100% - 24px);
            margin: 0 12px 16px;
            border-collapse: collapse;
            border-radius: 14px;
            overflow: hidden;
        }}
        .category-table th,
        .category-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(219, 205, 180, 0.65);
            text-align: left;
        }}
        .category-table thead th {{
            background: var(--panel-2);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
        }}
        .category-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        .task-details summary {{
            cursor: pointer;
            font-weight: 600;
            list-style: none;
        }}
        .task-details summary::-webkit-details-marker {{
            display: none;
        }}
        .task-details summary::before {{
            content: "▸";
            display: inline-block;
            margin-right: 8px;
            color: var(--accent);
        }}
        .task-details[open] summary::before {{
            content: "▾";
        }}
        .task-list {{
            margin: 10px 0 0;
            padding-left: 18px;
        }}
        .task-item + .task-item {{
            margin-top: 6px;
        }}
        .task-item a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .task-item a:hover {{
            text-decoration: underline;
        }}
        .empty-task-list {{
            margin-top: 10px;
            color: var(--muted);
            font-size: 14px;
        }}
        .number-cell {{
            width: 110px;
            text-align: right !important;
            font-variant-numeric: tabular-nums;
        }}
        .zero-count {{
            color: var(--muted);
        }}
        .empty-report,
        .empty-chart,
        .empty-table {{
            margin: 12px;
            padding: 18px;
            border-radius: 16px;
            border: 1px dashed rgba(166, 75, 42, 0.35);
            background: rgba(242, 214, 200, 0.28);
            color: var(--muted);
        }}
        .note {{
            margin-top: 18px;
            padding: 14px 16px;
            border-left: 4px solid var(--accent);
            background: rgba(242, 214, 200, 0.4);
            border-radius: 12px;
            color: var(--text);
        }}
        @media (max-width: 720px) {{
            .page {{
                padding: 20px 14px 40px;
            }}
            .hero h1 {{
                font-size: 28px;
            }}
            .project-header {{
                display: block;
            }}
            .dimension-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <main class="page">
        <section class="hero">
            <h1>{escape(title)}</h1>
            <p>Сводный отчет по классификациям задач из модели <code>KlassificationModel</code>. Группировка: проект из <code>related_object.taskmodel.project</code>, затем измерение, затем распределение задач по категориям.</p>
            <div class="note">
                Отчет сформирован: {escape(generated_at)}.<br>
                Фильтр проектов: названия содержат "Коннект" или "АУЦА". Если у задачи в одном измерении выбрано несколько категорий, такая задача учитывается в нескольких секторах диаграммы.
            </div>
            {summary_html}
        </section>
        {projects_html}
    </main>
</body>
</html>
"""


def write_report(output_path: Path, title: str) -> Path:
    report_data = collect_report_data()
    print("Rendering HTML...", flush=True)
    html = build_html(report_data=report_data, title=title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing file to {output_path}...", flush=True)
    output_path.write_text(html, encoding="utf-8")
    print("Report file written.", flush=True)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Построить HTML-отчет по классификациям задач с pie chart на Plotly."
    )
    parser.add_argument(
        "--output",
        default="klassification_report.html",
        help="Путь к итоговому HTML-файлу. По умолчанию: %(default)s",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help="Заголовок отчета. По умолчанию: %(default)s",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    saved_path = write_report(output_path=output_path, title=args.title)
    print(f"Report saved to: {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
