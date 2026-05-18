# 🔹 Стандартная библиотека
import io
import copy
import json
from django.core.cache import cache
from datetime import datetime, date
# 🔹 Django
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db import connection, models, transaction
from django.db.models import Sum, Avg, Count, Min, Max, Q, F, Value, DateField, DateTimeField
from django.db.models import ForeignKey, OneToOneField, ManyToManyField
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.conf import settings

# 🔹 Django REST framework
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.test import APIRequestFactory, force_authenticate

# 🔹 Третьи библиотеки
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from mptt.fields import TreeForeignKey

# 🔹 Локальные импорты
from common.fields import CustomForeignKey
from common.utils import is_uuid
from common.views import BaseModelViewSet
from .action_registry import get_registered_action
from . import utils
from .pagination import PagePagination, StandardPagination
from .exceptions import InvalidTablePartError, InvalidTablePartOperation
from .serializers import CTSerializer, UniversalModelReadSerializer, FastSerializerById, FastSerializer
from .utils import get_verbose_title
from .utils_meta import build_model_meta, get_field_meta
from .utils import get_verbose_title
from . import permissions
from . import models
from .utils_meta import _clear_meta_cache


def _extract_aggregate_source_field(aggregate_config):
    for func_key in ("sum", "avg", "min", "max", "count", "distinct_count"):
        if func_key in aggregate_config:
            return aggregate_config.get(func_key)
    return None


def _extract_pandas_aggregate_names(aggregate_fields, pandas_computed_fields):
    pandas_sources = set(pandas_computed_fields or [])
    if not pandas_sources:
        return []
    names = []
    for aggregate_config in aggregate_fields or []:
        source_field = _extract_aggregate_source_field(aggregate_config)
        aggregate_name = aggregate_config.get("name")
        if aggregate_name and source_field in pandas_sources:
            names.append(aggregate_name)
    return names


def _apply_model_pandas_aggregates(
    model_class,
    data,
    aggregate_fields,
    pandas_computed_fields,
    request,
    base_queryset=None,
):
    """
    Универсально применяет дополнительный расчет в pandas после SQL.
    Поддерживает вход как DataFrame, так и list[dict] (rows).
    """
    if data is None:
        return data
    if not hasattr(model_class, "apply_report_pandas_aggregates"):
        return data

    if isinstance(data, pd.DataFrame):
        if data.empty:
            return data
        return model_class.apply_report_pandas_aggregates(
            df=data,
            aggregate_fields=aggregate_fields,
            pandas_computed_fields=pandas_computed_fields,
            request=request,
            base_queryset=base_queryset,
        )

    if isinstance(data, list):
        if not data:
            return data
        rows_df = pd.DataFrame(data)
        if rows_df.empty:
            return data
        rows_df = model_class.apply_report_pandas_aggregates(
            df=rows_df,
            aggregate_fields=aggregate_fields,
            pandas_computed_fields=pandas_computed_fields,
            request=request,
            base_queryset=base_queryset,
        )
        if rows_df is None or rows_df.empty:
            return data
        aggregate_names = _extract_pandas_aggregate_names(aggregate_fields, pandas_computed_fields)
        aggregate_names = [name for name in aggregate_names if name in rows_df.columns]
        for row_index, row in enumerate(data):
            for aggregate_name in aggregate_names:
                value = rows_df.at[row_index, aggregate_name]
                row[aggregate_name] = None if pd.isna(value) else value
        return data

    return data


# 🔹 Закомментированные отладочные импорты
# from web_bkz.action_registry import action_registry
# print("=== REGISTRY DUMP ===")
# print(action_registry)
# print("=====================")


class UniversalModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]

    def get_paginate_by_param(self):
        query_value = self.request.query_params.get("pagination")
        if query_value is not None:
            return str(query_value).lower()
        if self.request.method == "POST" and isinstance(self.request.data, dict):
            data_value = self.request.data.get("pagination")
            if data_value is not None:
                return str(data_value).lower()
        return ""

    def get_pagination_class(self):
        pagination_type = self.get_paginate_by_param()

        if pagination_type == 'none':
            return None
        if pagination_type == 'page':
            return PagePagination
        else:
            return StandardPagination

    def get_queryset(self):
        app_label, model_name = self.basename.split('__')
        model_class = apps.get_model(app_label, model_name)
        queryset_params = self.request.data.get('queryset_params', {})

        if not queryset_params:
            queryset = model_class.get_queryset(self.request)
        else:
            queryset = model_class.get_queryset(self.request, queryset_params)

        return queryset

    def perform_create(self, serializer):
        disable_sqlite_foreign_keys()

        with transaction.atomic():
            instance = serializer.save()
            self._process_tps(instance, self.request.data['data'].get('tps', {}))

        enable_sqlite_foreign_keys()

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            self._process_tps(instance, self.request.data['data'].get('tps', {}))

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied()

    def create(self, request, *args, **kwargs):
        raise PermissionDenied()
        mutable_data = self.get_input_data()
        meta_block = self.request.data.get('meta')

        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.kwargs['pk'] = serializer.instance.pk
        response = self.retrieve(request, *args, **kwargs)

        if meta_block is not None:

            for item in meta_block['fields']:
                if item.get("name") == "code":
                    item["editable"] = False
                    break  # если нужно только одно совпадение

            response.data['meta'] = meta_block

        return response

    def update(self, request, *args, **kwargs):
        raise PermissionDenied()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        mutable_data = self.get_input_data()
        meta_block = self.request.data.get('meta')
        serializer = self.get_serializer(instance,
                                         data=mutable_data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.kwargs['pk'] = serializer.instance.pk

        response = self.retrieve(request, *args, **kwargs)

        if meta_block is not None:

            for item in meta_block['fields']:
                if item.get("name") == "code":
                    item["editable"] = False
                    break  # если нужно только одно совпадение

            response.data['meta'] = meta_block

        return response

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied()
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        app_label, model_name = self.basename.split('__')
        model_class = apps.get_model(app_label, model_name)
        exclude_fields = request.query_params.get('exclude_fields', 'true').lower() == 'true'
        meta = build_model_meta(request, model_class, instance, exclude_fields)

        field_names = None
        user_timezone = request.query_params.get('timezone', settings.TIME_ZONE)
        serializer = UniversalModelReadSerializer(instance,
                                                  retrieve=True,
                                                  model_class=model_class,
                                                  user_timezone=user_timezone)

        # Проверка параметра meta
        meta_param = self.request.query_params.get('meta')

        for item in meta['fields']:
            if item.get("name") == "code":
                item["editable"] = False
                break  # если нужно только одно совпадение

        if meta_param == 'true':
            return Response({"meta": meta})

        return Response({
            "meta": meta,
            "data": serializer.data
        })

    @action(detail=False, methods=['post'])
    def list_post(self, request, *args, **kwargs):
        # POST-запрос — используем ту же логику, что и в list
        return self.list(request, *args, **kwargs)

    @action(detail=False, methods=['get', 'post'])
    def select_list(self, request, *args, **kwargs):
        params = request.query_params if request.method == "GET" else request.data
        app_label, model_name = self.basename.split('__')
        model_class = apps.get_model(app_label, model_name)

        search = params.get('search')
        if search is None:
            queryset = model_class.get_select_queryset(request)
        else:
            queryset = model_class.get_filtered_select_queryset(search, request)
        try:
            model_class._meta.get_field('ct')
            queryset = queryset.select_related('ct')
        except FieldDoesNotExist:
            pass

        if request.method == "POST":
            if "id" in params:
                ids = params["id"]
                queryset = queryset.filter(id__in=ids)
            elif "code" in params:
                codes = params["code"]
                queryset = queryset.filter(code__in=codes)
            serializer = FastSerializer(queryset, many=True, model_class=model_class)
            return Response(serializer.data)

        self.pagination_class = self.get_pagination_class()
        page = self.paginate_queryset(queryset)
        serializer = FastSerializer(page if page is not None else queryset, many=True, model_class=model_class,
                                    context={'request': request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        app_label, model_name = self.basename.split('__')
        model_class = apps.get_model(app_label, model_name)

        # Универсальный способ получения параметров: GET → query_params, POST → data
        params = request.query_params if request.method == "GET" else request.data

        select_list = params.get('select_list')
        if select_list == 'true':
            return self.select_list(request, *args, **kwargs)

        exclude_fields = params.get('exclude_fields', 'true').lower() == 'true'
        meta = build_model_meta(request, model_class, None, exclude_fields)
        fields_dict = utils.get_fields_dict(request)

        group_fields_raw = fields_dict.get("groups", [])
        aggregate_fields_raw = fields_dict.get("aggregates", [])
        leveling_raw = fields_dict.get("leveling", [])
        system_fields_raw = fields_dict.get("system_fields", [])

        group_fields = utils.extract_field_names(group_fields_raw)
        leveling = utils.extract_field_names(leveling_raw)
        aggregate_fields = aggregate_fields_raw

        meta_param = params.get('meta')
        filters_raw = params.get('filters')
        ordering = params.get('ordering')
        results_type = params.get('results')
        format = params.get('format')
        report_title = params.get("report_name") or str(model_class._meta.verbose_name_plural)
        html_raw = params.get("html", False)
        html = str(html_raw).lower() == "true"
        user_timezone = params.get('timezone', settings.TIME_ZONE)

        if meta_param == 'true':
            return Response({"meta": meta})

        # Обработка системных фильтров (обязательная предварительная фильтрация)
        # Получаем system_filters из metadata отчета
        report_id = params.get('id')
        system_filters = utils.get_base_report_metadata(report_id).get('system_filters', {})
        # Получаем путь к шаблону отчёта (report_templates)
        template = utils.get_template_path_from_report(report_id)

        if system_filters:
            system_q_filter = utils.build_q_filter(system_filters)
            if system_q_filter:
                queryset = queryset.filter(system_q_filter)

        # Обработка пользовательских фильтров (парсим, но применяем после аннотаций)
        filters_data = {}
        if filters_raw:
            try:
                if isinstance(filters_raw, str):  # если фильтр передан в get-запросе, то он будет строкой
                    filters_data = json.loads(filters_raw)
                else:
                    filters_data = filters_raw  # в случае post-запроса - это уже словарь
                # Если это список — оборачиваем в "and". Т.е. случай простого фильтра
                if isinstance(filters_data, list):
                    filters_data = {
                        "logic": "and",
                        "filters": filters_data
                    }
                    simple_filter = True
                else:
                    simple_filter = False
            except json.JSONDecodeError:
                raise ValidationError('Ошибка в параметре filters')

        filters_data_for_queryset = filters_data
        non_queryset_filter_fields = _get_non_queryset_filter_fields(model_class)
        if filters_data_for_queryset and non_queryset_filter_fields:
            filters_data_for_queryset = _remove_filter_fields(filters_data_for_queryset, non_queryset_filter_fields)
            if isinstance(filters_data_for_queryset, dict) and not filters_data_for_queryset.get("filters"):
                filters_data_for_queryset = {}

        # Ранний расчёт модельных аннотаций для computed полей
        # (чтобы их можно было использовать в groups/aggregates и фильтрах)
        agg_ref_names = []
        for aggregate_config in aggregate_fields or []:
            source_field = _extract_aggregate_source_field(aggregate_config)
            if source_field:
                agg_ref_names.append(source_field)
        filter_field_names = _filter_field_names(filters_data_for_queryset) if filters_data_for_queryset else []
        requested_for_computed = list(set(group_fields + agg_ref_names + filter_field_names))
        model_annotations = {}
        if hasattr(model_class, 'get_report_annotations'):
            model_annotations = model_class.get_report_annotations(request, requested_for_computed)

        resolved_computed = set(model_annotations.keys())
        unresolved_computed = [name for name in requested_for_computed if name not in resolved_computed]
        model_computed_names = {
            meta_field["name"]
            for meta_field in model_class.get_report_computed_fields_meta()
            if meta_field.get("name")
        }
        unresolved_computed_set = set(unresolved_computed)
        pandas_computed_set = unresolved_computed_set & model_computed_names
        pandas_computed_fields = [
            name for name in unresolved_computed
            if name in pandas_computed_set
        ]
        pandas_group_fields = [field_name for field_name in group_fields if field_name in pandas_computed_set]
        if pandas_group_fields:
            raise ValidationError(
                "Поля, вычисляемые в pandas, нельзя использовать в группировке: "
                + ", ".join(pandas_group_fields)
                + ". Добавьте их в агрегаты."
            )
        aggregate_fields_for_queryset = [
            aggregate_config
            for aggregate_config in (aggregate_fields or [])
            if _extract_aggregate_source_field(aggregate_config) not in pandas_computed_set
        ]

        needed_sql_computed = set(requested_for_computed) - pandas_computed_set
        if model_annotations:
            model_annotations = {
                name: expression
                for name, expression in model_annotations.items()
                if name in needed_sql_computed
            }
        if model_annotations:
            queryset = queryset.annotate(**model_annotations)

        # Аннотации для связанных computed-полей до values() (универсально)
        related_rel_ann = utils.build_related_computed_annotations(
            model_class,
            requested_for_computed,
            request,
        )
        if related_rel_ann:
            queryset = queryset.annotate(**related_rel_ann)

        # Применяем пользовательские фильтры ПОСЛЕ применения аннотаций
        if filters_data_for_queryset:
            q_objects = build_q(filters_data_for_queryset, model_class=model_class)
            queryset = queryset.filter(q_objects)

        # Базовый объект для динамических плейсхолдеров в шаблоне (header/footer)
        base_instance = queryset.first()
        base_queryset = queryset

        # Всегда группируем по group_fields (fields_only не используется)
        queryset = queryset.values(*group_fields)

        annotations = utils.extract_annotations(model_class, aggregate_fields_for_queryset)
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Объединяем все доступные аннотации для передачи в compute_final_ordering
        available_annotations = {}
        if annotations:
            available_annotations.update(annotations)
        if model_annotations:
            available_annotations.update(model_annotations)
        if related_rel_ann:
            available_annotations.update(related_rel_ann)

        field_names = (
                group_fields +
                [agg.get("name") for agg in aggregate_fields if agg.get("name")] +
                [sf.get("name") for sf in system_fields_raw if sf.get("name")]
        )
        visible_columns_order = utils.get_columns_order(group_fields_raw, aggregate_fields_raw, system_fields_raw, leveling)
        json_title_map = utils.build_json_display_name_map(
            model_class=model_class,
            visible_columns_order=visible_columns_order,
            leveling_raw=leveling_raw,
            group_fields_raw=group_fields_raw,
            aggregate_fields_raw=aggregate_fields_raw,
            system_fields_raw=system_fields_raw,
        )

        # Обработка ordering через единый конвейер из utils
        if ordering:
            if isinstance(ordering, str):
                ordering_fields = [part.strip() for part in ordering.split(',')]
            elif isinstance(ordering, list):
                ordering_fields = ordering
            else:
                ordering_fields = []
        else:
            ordering_fields = []

        ordering_fields = utils.compute_final_ordering(
            ordering_fields,
            leveling,
            model_class,
            group_fields=group_fields,
            annotations=available_annotations if available_annotations else None,
        )

        if ordering_fields:
            queryset = queryset.order_by(*ordering_fields)

        if results_type == 'histogram':
            annotation_output_fields_hist = {
                name: getattr(expr, 'output_field', None)
                for name, expr in (available_annotations or {}).items()
                if getattr(expr, 'output_field', None) is not None
            }
            serializer = UniversalModelReadSerializer(
                queryset,
                many=True,
                list=True,
                model_class=model_class,
                field_names=field_names,
                user_timezone=user_timezone,
                annotation_output_fields=annotation_output_fields_hist,
            )
            histogram_rows = [
                {
                    key: (value if isinstance(value, dict) and value.get("url") else utils.try_repr(value))
                    for key, value in row.items()
                }
                for row in serializer.data
            ]
            histogram_df = pd.DataFrame(histogram_rows)
            histogram_df = _apply_daily_axis_enrichment_to_dataframe(
                df=histogram_df,
                model_class=model_class,
                filters_data=filters_data,
                group_fields=group_fields,
                aggregate_fields=aggregate_fields,
            )
            histogram_df = _apply_model_pandas_aggregates(
                model_class=model_class,
                data=histogram_df,
                aggregate_fields=aggregate_fields,
                pandas_computed_fields=pandas_computed_fields,
                request=request,
                base_queryset=base_queryset,
            )
            histogram_rows = _dataframe_to_rows(histogram_df)
            return utils.export_report_to_histogram(
                rows=histogram_rows,
                group_fields=group_fields,
                aggregate_fields=aggregate_fields,
            )

        if results_type in ('xls', 'apexchart'):
            # Собираем карту типов выходных полей для аннотированных полей
            annotation_output_fields = {}
            for name, expr in (available_annotations or {}).items():
                of = getattr(expr, 'output_field', None)
                if of is not None:
                    annotation_output_fields[name] = of

            serializer = UniversalModelReadSerializer(
                queryset, many=True, list=True, model_class=model_class, field_names=field_names,
                user_timezone=user_timezone, annotation_output_fields=annotation_output_fields,
            )
            data = serializer.data
            # Сохраняем dict только для гиперссылок {"repr","url"}, остальные dict -> repr
            processed_data = [
                {
                    k: (v if isinstance(v, dict) and v.get("url") else utils.try_repr(v))
                    for k, v in row.items()
                }
                for row in data
            ]
            df = pd.DataFrame(processed_data)

            # Получаем порядок колонок для вычислений (все поля, включая невидимые)
            columns_order_for_calculations = utils.get_columns_order_for_calculations(group_fields_raw,
                                                                                      aggregate_fields_raw,
                                                                                      system_fields_raw, leveling)
            df = df[[col for col in columns_order_for_calculations if col in df.columns]]

            # Добавляем нумерационные поля через pandas
            # Примечание: замена None на "Не заполнено" будет выполнена в prepare_report_data
            system_fields_requested = [sf.get("name") for sf in system_fields_raw if
                                       sf.get("name") in ("index", "group_index")]
            if system_fields_requested and not df.empty:
                # Временно обрабатываем None значения для корректной группировки при нумерации
                # (prepare_report_data сделает это еще раз, но это безопасно - операция идемпотентна)
                utils.replace_none_with_empty_for_leveling(df, leveling)

                # Добавляем index (сквозная нумерация)
                if "index" in system_fields_requested:
                    df['index'] = range(1, len(df) + 1)

                # Добавляем group_index (нумерация внутри групп leveling)
                if "group_index" in system_fields_requested:
                    if leveling:
                        # Проверяем, что все поля leveling присутствуют в DataFrame
                        leveling_present = [field for field in leveling if field in df.columns]
                        if leveling_present:
                            # Группируем по полям leveling и нумеруем внутри каждой группы
                            # dropna=False гарантирует, что "Не заполнено" будет правильно обработано
                            df['group_index'] = df.groupby(leveling_present, dropna=False).cumcount() + 1
                        else:
                            # Если полей leveling нет в DataFrame, делаем простую нумерацию
                            df['group_index'] = range(1, len(df) + 1)
                    else:
                        # Если leveling нет, делаем простую нумерацию
                        df['group_index'] = range(1, len(df) + 1)

            aggregates = []
            for agg in aggregate_fields:
                name = agg.get("name")
                if not name:
                    continue
                aggregates.append(name)
                if any(k in agg for k in ("sum", "avg", "count", "min", "max")) and name in df.columns:
                    df[name] = pd.to_numeric(df[name], errors="coerce")
            df = _apply_daily_axis_enrichment_to_dataframe(
                df=df,
                model_class=model_class,
                filters_data=filters_data,
                group_fields=group_fields,
                aggregate_fields=aggregate_fields,
            )

            # Досчёт вычисляемых метрик в pandas после SQL
            df = _apply_model_pandas_aggregates(
                model_class=model_class,
                data=df,
                aggregate_fields=aggregate_fields,
                pandas_computed_fields=pandas_computed_fields,
                request=request,
                base_queryset=base_queryset,
            )

            filters_table = utils.get_filters_table(
                filters_data,
                model_class,
                leveling_raw,
                group_fields_raw,
                aggregates,
                system_fields_raw,
            )
            filters_placeholders = utils.get_filters_placeholders(
                filters_data,
                model_class,
                leveling_raw,
                group_fields_raw,
                aggregates,
                system_fields_raw,
            )
            # Общая копилка плейсхолдеров для шаблонов (header/footer, html)
            timezone_str = f"{_('Часовой пояс')}: {params.get('timezone', settings.TIME_ZONE)}"
            creation_date_str = f"{_('Дата создания')}: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            placeholders = {
                "report_title": report_title,
                "creation_date": creation_date_str,
                "timezone": timezone_str,
            }
            if filters_placeholders:
                placeholders.update(filters_placeholders)

            df_filters = pd.DataFrame(filters_table)

            # Подготавливаем данные один раз (используем все поля для вычислений)
            output_rows, final_df, numeric_aggregate_fields, show_totals, fields_for_totals, totals_title, grand_totals_row = utils.prepare_report_data(
                params, model_class, df, leveling, aggregates, aggregate_fields_raw,
                leveling_raw, group_fields_raw, system_fields_raw, columns_order_for_calculations
            )

            # Получаем порядок колонок для отображения (только видимые поля)
            columns_order = utils.get_columns_order(group_fields_raw, aggregate_fields_raw, system_fields_raw, leveling)

            if results_type == 'apexchart':
                report_metadata = utils.get_base_report_metadata(report_id)
                apex_conf = report_metadata.get('apexchart') if report_metadata else None
                chart_title_map = utils.build_json_display_name_map(
                    model_class=model_class,
                    visible_columns_order=columns_order_for_calculations,
                    leveling_raw=leveling_raw,
                    group_fields_raw=group_fields_raw,
                    aggregate_fields_raw=aggregate_fields_raw,
                    system_fields_raw=system_fields_raw,
                )
                title_to_key = {
                    display_title: technical_key
                    for technical_key, display_title in (chart_title_map or {}).items()
                    if isinstance(display_title, str)
                }
                chart_df = final_df.copy()
                if not chart_df.empty and '__row_type__' in chart_df.columns:
                    chart_df = chart_df.loc[chart_df['__row_type__'] == 'data']
                chart_df = chart_df.drop(columns=['__row_type__', '__indent__'], errors='ignore')
                chart_rows = chart_df.to_dict(orient='records')
                for chart_row in chart_rows:
                    for chart_key, cell in chart_row.items():
                        if cell == '' or (cell is not None and pd.isna(cell)):
                            chart_row[chart_key] = None
                return Response(utils.build_apexchart_payload(chart_rows, apex_conf, title_to_key=title_to_key))

            if html:
                return utils.export_report_to_html(
                    params=params,
                    model_class=model_class,
                    output_rows=output_rows,
                    final_df=final_df,
                    df_filters=df_filters,
                    numeric_aggregate_fields=numeric_aggregate_fields,
                    show_totals=show_totals,
                    fields_for_totals=fields_for_totals,
                    totals_title=totals_title,
                    grand_totals_row=grand_totals_row,
                    leveling_raw=leveling_raw,
                    group_fields_raw=group_fields_raw,
                    aggregate_fields_raw=aggregate_fields_raw,
                    system_fields_raw=system_fields_raw,
                    report_title=report_title,
                    columns_order=columns_order,
                    placeholders=placeholders,
                )

            return utils.export_report_to_excel(
                params=params,
                model_class=model_class,
                output_rows=output_rows,
                final_df=final_df,
                df_filters=df_filters,
                numeric_aggregate_fields=numeric_aggregate_fields,
                show_totals=show_totals,
                fields_for_totals=fields_for_totals,
                totals_title=totals_title,
                grand_totals_row=grand_totals_row,
                leveling_raw=leveling_raw,
                group_fields_raw=group_fields_raw,
                aggregate_fields_raw=aggregate_fields_raw,
                system_fields_raw=system_fields_raw,
                report_title=report_title,
                columns_order=columns_order,
                placeholders=placeholders,
                template=template,
                base_instance=base_instance,
            )

        self.pagination_class = self.get_pagination_class()

        page = self.paginate_queryset(queryset)

        annotation_output_fields = {}
        for name, expr in (available_annotations or {}).items():
            of = getattr(expr, 'output_field', None)
            if of is not None:
                annotation_output_fields[name] = of
        serializer = UniversalModelReadSerializer(
            page if page is not None else queryset,
            many=True,
            list=True,
            model_class=model_class,
            field_names=field_names,
            user_timezone=user_timezone,
            annotation_output_fields=annotation_output_fields,
        )

        # Добавляем нумерационные поля через pandas
        system_fields_requested = [sf.get("name") for sf in system_fields_raw if
                                   sf.get("name") in ("index", "group_index")]
        if system_fields_requested:
            serializer_data = serializer.data
            serializer_data = utils.add_index_fields_with_pandas(
                serializer_data,
                ordering_fields,
                leveling,
                system_fields_requested
            )
        else:
            serializer_data = serializer.data

        if page is None:
            serializer_df = pd.DataFrame(serializer_data)
            serializer_df = _apply_daily_axis_enrichment_to_dataframe(
                df=serializer_df,
                model_class=model_class,
                filters_data=filters_data,
                group_fields=group_fields,
                aggregate_fields=aggregate_fields,
            )
            serializer_df = _apply_model_pandas_aggregates(
                model_class=model_class,
                data=serializer_df,
                aggregate_fields=aggregate_fields,
                pandas_computed_fields=pandas_computed_fields,
                request=request,
                base_queryset=base_queryset,
            )
            serializer_data = _dataframe_to_rows(serializer_df)
        else:
            serializer_data = _apply_model_pandas_aggregates(
                model_class=model_class,
                data=serializer_data,
                aggregate_fields=aggregate_fields,
                pandas_computed_fields=pandas_computed_fields,
                request=request,
                base_queryset=base_queryset,
            )
        serializer_data = _filter_rows_by_columns(serializer_data, visible_columns_order)

        serializer_data = utils.rename_rows_by_title(serializer_data, json_title_map)

        if page is not None:
            return self.get_paginated_response(serializer_data)

        return Response({"results": serializer_data})

    def get_serializer_class(self):
        app_label, model_name = self.basename.split('__')
        model_class = apps.get_model(app_label, model_name)  # Получаем класс модели по имени

        class SerializerClass(UniversalModelReadSerializer):
            class Meta:
                model = model_class  # Устанавливаем модель для сериализатора
                fields = '__all__'  # Включаем все поля модели
                ref_name = f"{model_class.__name__}Serializer"  # Уникальное имя ref_name

        return SerializerClass  # Возвращаем класс сериализатора для использования в ViewSet

    def _process_tps(self, parent_instance, tps_payload):
        model = type(parent_instance)
        allowed_tps = getattr(model, 'tps', [])

        for tps_model_name, actions in tps_payload.items():
            if tps_model_name not in allowed_tps:
                raise InvalidTablePartError(f"{tps_model_name} is not defined in model.tps")

            tps_model = apps.get_model(model._meta.app_label, tps_model_name)

            # Определим имя поля "owner"
            owner_field_name = 'owner'

            # ADD
            for item in actions.get('add', []):
                item.pop('owner_id', None)
                item[owner_field_name] = parent_instance  # передаём именно объект
                self._validate_editable_fields(tps_model, item)
                tps_model.objects.create(**item)

            # EDIT
            for item in actions.get('edit', []):
                try:
                    obj = tps_model.objects.get(pk=item['id'])
                except tps_model.DoesNotExist:
                    raise InvalidTablePartOperation(f"{tps_model_name} with id={item['id']} does not exist")

                # Проверка, что владелец соответствует текущему объекту
                if getattr(obj, owner_field_name).pk != parent_instance.pk:
                    raise InvalidTablePartOperation(
                        f"Attempt to modify a {tps_model_name} record not owned by the current object."
                    )

                for k, v in item.items():
                    if k == 'id':
                        continue
                    self._check_editable_field(tps_model, k)
                    setattr(obj, k, v)
                obj.save()

            # DELETE
            for item_id in actions.get('delete', []):
                tps_model.objects.filter(
                    pk=item_id,
                    owner=parent_instance
                ).delete()

    def _check_editable_field(self, model_class, field_name):
        try:
            field = model_class._meta.get_field(field_name)
            if not getattr(field, 'editable', True):
                raise InvalidTablePartOperation(f"Field '{field_name}' is not editable")
        except FieldDoesNotExist:
            raise InvalidTablePartOperation(f"Field '{field_name}' does not exist in model {model_class.__name__}")

    def _validate_editable_fields(self, model_class, data: dict):
        for field_name in data:
            self._check_editable_field(model_class, field_name)

    def get_input_data(self):
        """Получает полезную нагрузку из запроса, извлекая `data` при наличии"""
        if isinstance(self.request.data, dict) and "data" in self.request.data:
            return self.request.data["data"]
        return self.request.data


def _filter_field_names(filters_group):
    """Рекурсивно собирает имена полей из filters_data. Нужно, чтобы аннотации для вычисляемых полей (например main_specialist) добавлялись до применения фильтра."""
    names = []
    for f in filters_group.get("filters", []):
        if "filters" in f:
            names.extend(_filter_field_names(f))
        elif f.get("field"):
            names.append(f["field"])
    return names


def _get_non_queryset_filter_fields(model_class):
    if not model_class or not hasattr(model_class, "get_report_computed_fields_meta"):
        return set()
    result = set()
    for field_meta in model_class.get_report_computed_fields_meta():
        field_name = field_meta.get("name")
        if field_name and field_meta.get("apply_to_queryset") is False:
            result.add(field_name)
    return result


def _remove_filter_fields(filters_group, field_names):
    if not isinstance(filters_group, dict) or not field_names:
        return filters_group

    cleaned_filters = []
    for filter_item in filters_group.get("filters", []):
        if isinstance(filter_item, dict) and "filters" in filter_item:
            nested_group = _remove_filter_fields(filter_item, field_names)
            nested_filters = nested_group.get("filters", []) if isinstance(nested_group, dict) else []
            if nested_filters:
                cleaned_filters.append(nested_group)
            continue
        if isinstance(filter_item, dict) and filter_item.get("field") in field_names:
            continue
        cleaned_filters.append(filter_item)

    result = dict(filters_group)
    result["filters"] = cleaned_filters
    return result


def _extract_date_bounds_from_filters(filters_group, field_name):
    """Извлекает границы периода (from/to) для указанного поля из filters_data."""
    if not isinstance(filters_group, dict):
        return None, None

    def _iter_filters(group):
        for filter_item in group.get("filters", []):
            if isinstance(filter_item, dict) and "filters" in filter_item:
                yield from _iter_filters(filter_item)
            elif isinstance(filter_item, dict):
                yield filter_item

    date_from = None
    date_to = None
    for filter_item in _iter_filters(filters_group):
        if filter_item.get("field") != field_name:
            continue
        comparison_type = filter_item.get("comparison_type")
        value = utils.parse_filter_value(filter_item.get("value"))
        if isinstance(value, datetime):
            value = value.date()
        if not isinstance(value, date):
            continue
        if comparison_type in (">=", ">"):
            if date_from is None or value > date_from:
                date_from = value
        elif comparison_type in ("<=", "<"):
            if date_to is None or value < date_to:
                date_to = value
    return date_from, date_to


def _densify_daily_axis(df, date_column, date_from, date_to, dimension_columns, numeric_columns, axis_freq="D"):
    """Добавляет отсутствующие даты в оси day и заполняет числовые колонки нулями."""
    if df is None or df.empty:
        return df
    if date_column not in df.columns or not date_from or not date_to:
        return df

    normalized_df = df.copy()
    normalized_df[date_column] = pd.to_datetime(normalized_df[date_column], errors="coerce").dt.date

    def _stable_dim_key(value):
        if isinstance(value, (dict, list, tuple)):
            try:
                return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            except TypeError:
                return str(value)
        return value

    calendar_df = pd.DataFrame(
        {date_column: pd.date_range(start=date_from, end=date_to, freq=axis_freq).date}
    )

    if dimension_columns:
        fact_df = normalized_df.copy()
        dim_key_columns = []
        for dimension_column in dimension_columns:
            key_column = f"__dim_key__{dimension_column}"
            dim_key_columns.append(key_column)
            fact_df[key_column] = fact_df[dimension_column].apply(_stable_dim_key)

        unique_dims_df = fact_df[dim_key_columns + dimension_columns].drop_duplicates(subset=dim_key_columns).copy()
        dims_keys_df = unique_dims_df[dim_key_columns].copy()
        dims_keys_df["_tmp_join_key"] = 1
        calendar_df["_tmp_join_key"] = 1
        scaffold_df = dims_keys_df.merge(calendar_df, on="_tmp_join_key", how="inner").drop(columns=["_tmp_join_key"])
    else:
        fact_df = normalized_df
        dim_key_columns = []
        unique_dims_df = None
        scaffold_df = calendar_df

    merged_df = scaffold_df.merge(fact_df, on=dim_key_columns + [date_column], how="left")
    if dimension_columns and unique_dims_df is not None:
        merged_df = merged_df.drop(columns=dimension_columns, errors="ignore")
        merged_df = merged_df.merge(unique_dims_df, on=dim_key_columns, how="left")

    for numeric_column in numeric_columns:
        if numeric_column in merged_df.columns:
            merged_df[numeric_column] = pd.to_numeric(merged_df[numeric_column], errors="coerce").fillna(0)
    sort_columns = dim_key_columns + [date_column]
    merged_df = merged_df.sort_values(sort_columns).reset_index(drop=True)
    if dim_key_columns:
        merged_df = merged_df.drop(columns=dim_key_columns, errors="ignore")
    return merged_df


def _get_daily_axis_meta(model_class, group_fields):
    if not model_class or not hasattr(model_class, "get_report_computed_fields_meta"):
        return None
    if not group_fields:
        return None
    grouped_fields = set(group_fields)
    for field_meta in model_class.get_report_computed_fields_meta():
        field_name = field_meta.get("name")
        if not field_name:
            continue
        if field_meta.get("date_axis") is True and field_name in grouped_fields:
            return {
                "name": field_name,
                "axis_freq": field_meta.get("axis_freq") or "D",
            }
    return None


def _extract_daily_axis_bounds(filters_data, daily_axis_field):
    if not daily_axis_field:
        return None, None
    daily_from, daily_to = _extract_date_bounds_from_filters(filters_data, daily_axis_field)
    if daily_from is None and daily_to is None:
        daily_from, daily_to = _extract_date_bounds_from_filters(filters_data, "report_period")
    if daily_from is None and daily_to is None:
        daily_from, daily_to = _extract_date_bounds_from_filters(filters_data, "created_at")
    return daily_from, daily_to


def _apply_daily_axis_enrichment_to_dataframe(
    df,
    model_class,
    filters_data,
    group_fields,
    aggregate_fields,
):
    if df is None or df.empty:
        return df

    aggregate_names = [agg.get("name") for agg in (aggregate_fields or []) if agg.get("name")]
    daily_axis_meta = _get_daily_axis_meta(model_class, group_fields)
    daily_axis_field = daily_axis_meta["name"] if daily_axis_meta else None
    daily_axis_from, daily_axis_to = _extract_daily_axis_bounds(filters_data, daily_axis_field)
    if daily_axis_field:
        dimensions_without_day = [field for field in group_fields if field != daily_axis_field]
        df = _densify_daily_axis(
            df=df,
            date_column=daily_axis_field,
            date_from=daily_axis_from,
            date_to=daily_axis_to,
            dimension_columns=dimensions_without_day,
            numeric_columns=aggregate_names,
            axis_freq=daily_axis_meta.get("axis_freq") or "D",
        )

    return df


def _dataframe_to_rows(df):
    if df is None:
        return []
    rows = df.to_dict(orient="records")
    normalized_rows = []
    for row in rows:
        normalized_row = {}
        for key, value in row.items():
            normalized_row[key] = None if pd.isna(value) else value
        normalized_rows.append(normalized_row)
    return normalized_rows


def _filter_rows_by_columns(rows, allowed_columns):
    if not rows or not allowed_columns:
        return rows
    allowed_set = set(allowed_columns)
    filtered_rows = []
    for row in rows:
        filtered_rows.append({key: value for key, value in row.items() if key in allowed_set})
    return filtered_rows


def _normalize_chat_filter_value(raw_value):
    if isinstance(raw_value, str) and "T" in raw_value:
        date_part = raw_value.split("T", 1)[0]
        if len(date_part) == 10:
            return date_part
    return raw_value


def _build_report_filters_from_chat_payload(request_data):
    reserved_keys = {
        "report_code",
        "timezone",
        "results",
        "html",
    }
    result_filters = []

    for key, raw_value in request_data.items():
        if key in reserved_keys:
            continue
        if raw_value in (None, ""):
            continue

        field_name = key
        comparison_type = "="
        if key.endswith("__from"):
            field_name = key[:-6]
            comparison_type = ">="
        elif key.endswith("__to"):
            field_name = key[:-4]
            comparison_type = "<="
        elif isinstance(raw_value, list):
            comparison_type = "in"

        result_filters.append({
            "field": field_name,
            "comparison_type": comparison_type,
            "value": _normalize_chat_filter_value(raw_value),
        })

    return result_filters


def _build_report_fields_from_metadata(metadata):
    columns = metadata.get("columns", [])
    grouping = metadata.get("grouping", [])

    groups = []
    aggregates = []
    system_fields = []

    for column in columns:
        if not isinstance(column, dict):
            continue
        if not column.get("active", False):
            continue
        if not column.get("name"):
            continue

        base_item = {
            "name": column.get("name"),
        }
        if column.get("title"):
            base_item["title"] = column.get("title")
        if "order" in column:
            base_item["order"] = column.get("order")
        if "is_visible" in column:
            base_item["is_visible"] = column.get("is_visible")

        if column.get("aggregate"):
            aggregate_item = dict(column)
            aggregate_title = (
                aggregate_item.get("title")
                or aggregate_item.get("defaultTitle")
                or aggregate_item.get("verbose_name")
            )
            if aggregate_title:
                aggregate_item["name"] = (
                    str(aggregate_title)
                    .replace(" ", "__SPACE")
                    .replace(",", "__COMMA")
                    .replace(":", "__COLON")
                )
            aggregates.append(aggregate_item)
        elif column.get("system"):
            system_fields.append(base_item)
        else:
            groups.append(base_item)

    leveling = []
    for grouping_item in grouping:
        if not isinstance(grouping_item, dict):
            continue
        if grouping_item.get("active") and grouping_item.get("name"):
            leveling.append({"name": grouping_item.get("name")})

    return {
        "groups": groups,
        "leveling": leveling,
        "aggregates": aggregates,
        "system_fields": system_fields,
    }


def build_q_period_filter(model_class, field, comparison, value):
    """
    Строит Q для виртуального поля периода (period_filter в get_report_computed_fields_meta).
    Возвращает Q с null-семантикой для start_field/end_field или None, если поле не период или сравнение не подходит.
    """
    if not model_class or not hasattr(model_class, 'get_report_computed_fields_meta'):
        return None
    period_filter_config = None
    for meta in model_class.get_report_computed_fields_meta():
        if meta.get('name') == field and meta.get('period_filter'):
            period_filter_config = meta['period_filter']
            break
    if not period_filter_config or comparison not in (">=", ">", "<=", "<"):
        return None
    start_field = period_filter_config.get("start_field")
    end_field = period_filter_config.get("end_field")
    if not start_field or not end_field or value is None:
        return None
    if comparison == ">=":
        return Q(**{f"{end_field}__gte": value})
    if comparison == ">":
        return Q(**{f"{end_field}__gt": value})
    if comparison == "<=":
        return Q(**{f"{start_field}__lte": value})
    # "<"
    return Q(**{f"{start_field}__lt": value})


def build_q(filters_group, model_class=None):
    logic = filters_group.get("logic", "and").lower()
    filters = filters_group.get("filters", [])

    q_objects = Q()
    for f in filters:
        if "filters" in f:  # вложенная группа
            q_child = build_q(f, model_class=model_class)
        else:
            field = f.get("field")
            comparison = f.get("comparison_type")
            value = f.get("value")
            value = utils.parse_filter_value(value)

            if not field or not comparison:
                continue

            # Сначала пробуем модельный хук для кастомной логики фильтрации
            q_child = None
            if model_class is not None and hasattr(model_class, "build_report_field_q"):
                try:
                    q_child = model_class.build_report_field_q(field, comparison, value)
                except Exception:
                    q_child = None

            if q_child is None:
                q_child = build_q_period_filter(model_class, field, comparison, value)

            if q_child is None:
                # Для comparison_type "<=" и DateTimeField: преобразуем date в datetime с временем 23:59:59
                if comparison == "<=" and model_class:
                    try:
                        model_field, _ = get_field_meta(field, model_class)
                        if model_field and isinstance(model_field, DateTimeField):
                            if isinstance(value, date):
                                value = datetime.combine(value, datetime.max.time())
                    except Exception:
                        pass

                if comparison == "=":
                    q_child = Q(**{f"{field}": value})
                elif comparison == "!=":
                    q_child = ~Q(**{f"{field}": value})
                elif comparison == ">":
                    q_child = Q(**{f"{field}__gt": value})
                elif comparison == ">=":
                    q_child = Q(**{f"{field}__gte": value})
                elif comparison == "<":
                    q_child = Q(**{f"{field}__lt": value})
                elif comparison == "<=":
                    q_child = Q(**{f"{field}__lte": value})
                elif comparison == "icontains":
                    q_child = Q(**{f"{field}__icontains": value})
                elif comparison == "not icontains":
                    q_child = ~Q(**{f"{field}__icontains": value})
                elif comparison == "isnull":
                    q_child = Q(**{f"{field}__isnull": True})
                elif comparison == "not isnull":
                    q_child = Q(**{f"{field}__isnull": False})
                elif comparison == "in":
                    if isinstance(value, str):
                        value = value.split(",")
                    q_child = Q(**{f"{field}__in": value})
                elif comparison == "not in":
                    if isinstance(value, str):
                        value = value.split(",")
                    q_child = ~Q(**{f"{field}__in": value})

        if q_child:
            if logic == "or":
                q_objects |= q_child
            else:
                q_objects &= q_child

    return q_objects


from rest_framework.parsers import JSONParser, FormParser, MultiPartParser


@csrf_exempt
def form_action_view(request, model, form_name, action_name):
    if request.method not in ["GET", "POST"]:
        return Response({"error": "Only GET and POST allowed"}, status=405)

    model_class = apps.get_model('web_bkz', model)
    if not model_class:
        raise Http404("Model not found")

    # try:
    #  #   instance = model_class.objects.get(pk=pk)
    # except model_class.DoesNotExist:
    #   #  raise Http404("Object not found")

    action_func = get_registered_action(form_name, action_name)
    if not action_func:
        raise Http404(f"Action '{action_name}' not registered for form '{form_name}'")

    drf_request = Request(request, parsers=[JSONParser(), FormParser(), MultiPartParser()])
    instance = None
    result = action_func(instance, drf_request)

    if isinstance(result, Response):
        result.accepted_renderer = JSONRenderer()
        result.accepted_media_type = 'application/json'
        result.renderer_context = {
            'request': drf_request,
            'response': result,
        }
        result.render()
        return HttpResponse(result.content, content_type='application/json', status=result.status_code)

    return Response(result)


def disable_sqlite_foreign_keys():
    """Отключает проверку внешних ключей в SQLite."""
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')
            print("SQLite FOREIGN KEY constraints disabled.")


def enable_sqlite_foreign_keys():
    """Включает обратно проверку внешних ключей в SQLite."""
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = ON;')
            print("SQLite FOREIGN KEY constraints re-enabled.")


class ReportSettingsModelViewSet(BaseModelViewSet):
    """Вьюсет общих шаблонов отчетов."""
    permission_classes = (IsAuthenticated, permissions.ReportSettingsModelPermission)
    model = models.ReportSettingsModel

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='count_by_category')
    def count_by_category(self, request):
        """Количество отчётов по категориям и общее количество."""
        qs = self.get_queryset()
        per_category = qs.values('category_id').annotate(count=Count('pk')).order_by('category_id')
        result = {}
        total = 0
        for row in per_category:
            key = row['category_id'] if row['category_id'] else 'uncategorized'
            result[key] = row['count']
            total += row['count']
        result['total'] = total
        return Response(result)

    @action(detail=False, methods=['get'], url_path=r'by_code/(?P<code>[^/.]+)')
    def by_code(self, request, code=None):
        """Детальная настройка отчёта по уникальному code."""
        report_settings = self.model.objects.all().filter(code=code).first()
        if not report_settings:
            return Response(
                {"error": f'Отчёт с code="{code}" не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer_class = self.model.get_serializer_class(action='retrieve')
        serializer = serializer_class(report_settings, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='run_from_chat')
    def run_from_chat(self, request):
        report_code = request.data.get("report_code")

        report_settings = models.ReportSettingsModel.objects.filter(
            is_active=True,
            code=report_code,
        ).first()
        if not report_settings:
            return Response(
                {"error": f'Отчёт с code="{report_code}" не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        metadata = report_settings.metadata or {}
        model_name = metadata.get("modelName")
        if not model_name:
            raise ValidationError('В настройках отчёта отсутствует "modelName".')

        model_class = None
        model_name_normalized = str(model_name).strip().lower()
        for app_model in apps.get_models():
            if app_model.__name__.lower() == model_name_normalized:
                model_class = app_model
                break
        if model_class is None:
            raise ValidationError(f'Не найдена модель отчёта для modelName="{model_name}".')

        ordering = []
        for ordering_item in metadata.get("ordering", []):
            if not isinstance(ordering_item, dict):
                continue
            field_name = ordering_item.get("name")
            if not field_name:
                continue
            order_direction = str(ordering_item.get("orderBy", "ASC")).upper()
            if order_direction == "DESC":
                ordering.append(f"-{field_name}")
            else:
                ordering.append(field_name)

        report_payload = {
            "report_name": report_settings.name,
            "fields": _build_report_fields_from_metadata(metadata),
            "filters": _build_report_filters_from_chat_payload(request.data),
            "ordering": ordering,
            "results": request.data.get("results", "xls"),
            "html": request.data.get("html", False),
            "id": str(report_settings.pk),
            "timezone": request.data.get("timezone", settings.TIME_ZONE),
        }

        app_label = model_class._meta.app_label
        model_class_name = model_class.__name__
        basename = f"{app_label}__{model_class_name}"

        model_url_part = model_class_name.lower()
        internal_request = APIRequestFactory().post(
            f"/api/v1/reports/{model_url_part}/list_post/",
            report_payload,
            format="json",
        )
        force_authenticate(internal_request, user=request.user)

        internal_view = UniversalModelViewSet.as_view(
            {"post": "list_post"},
            basename=basename,
        )
        return internal_view(internal_request)


class UserReportSettingsModelViewSet(BaseModelViewSet):
    """Вьюсет пользовательских шаблонов отчетов."""
    permission_classes = (IsAuthenticated, permissions.UserReportSettingsModelPermission)
    model = models.UserReportSettingsModel

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=('is_active',))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='count_by_category')
    def count_by_category(self, request):
        """Количество пользовательских отчётов по категории базового отчёта и общее количество."""
        qs = self.get_queryset()
        per_category = qs.values('base_report__category_id').annotate(count=Count('pk')).order_by('base_report__category_id')
        result = {}
        total = 0
        for row in per_category:
            key = row['base_report__category_id'] if row['base_report__category_id'] else 'uncategorized'
            result[key] = row['count']
            total += row['count']
        result['total'] = total
        return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clear_meta_cache(request):
    """Эндпойнт для очистки кэша мета-данных."""
    if not request.user.is_staff:
        raise PermissionDenied('Доступ запрещен. Требуются права администратора.')
    try:
        result = _clear_meta_cache()
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            f'Ошибка при очистке кэша: {str(e)}',
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
