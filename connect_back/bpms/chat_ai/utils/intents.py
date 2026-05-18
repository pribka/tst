from django.apps import apps
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from django.db.models import Q
from django.test import RequestFactory
from es_search.utils import universal_search
from .reference_matching import (
    name_tokens,
    token_stem,
    split_reference_names,
    resolve_reference_field_value,
)


def _split_reference_names(raw_value, model_path=""):
    return split_reference_names(raw_value, model_path)

def create_request_with_data_path(original_request, data_path):
    """Модифицирует существующий request с дополнительными параметрами из data_path"""
    try:
        # Берем базовые GET-параметры из исходного request.
        base_params = original_request.GET.copy()

        # Создаем отдельный request для конкретного поля, чтобы фильтры не "текли" в другие поля.
        request_copy = RequestFactory().get(getattr(original_request, "path", "/"))
        request_copy.user = getattr(original_request, "user", None)
        request_copy.profile = getattr(original_request, "profile", None)

        from django.http import QueryDict
        new_query_dict = QueryDict(mutable=True)
        new_query_dict.update(base_params)

        if not data_path:
            request_copy.GET = new_query_dict
            request_copy.query_params = request_copy.GET
            return request_copy

        # Парсим URL и извлекаем query string
        parsed_url = urlparse(data_path)
        query_string = parsed_url.query
        
        if not query_string:
            request_copy.GET = new_query_dict
            request_copy.query_params = request_copy.GET
            return request_copy
        
        # Парсим query параметры
        query_params = parse_qs(query_string)

        # Добавляем новые параметры
        for key, values in query_params.items():
            new_query_dict[key] = values[0] if values else ''

        request_copy.GET = new_query_dict
        request_copy.query_params = request_copy.GET
        return request_copy
        
    except Exception:
        # Если что-то пошло не так, возвращаем оригинальный request
        return original_request


def find_candidates_for_model(model_path, search_name, request, max_candidates=5):
    """Поиск кандидатов для конкретной модели по имени через Elasticsearch"""
    def _fallback_candidates(model_class):
        """Fallback-поиск по БД на случай ошибок/пустого ответа Elasticsearch."""
        try:
            if hasattr(model_class, "get_select_queryset"):
                qs = model_class.get_select_queryset(request)
            else:
                qs = model_class.objects.all()
        except Exception:
            return []

        query_tokens = _name_tokens(search_name)
        model_label = getattr(model_class._meta, "label_lower", "")

        # Ускоряем и повышаем релевантность для профилей пользователей.
        try:
            if model_label == "users.profilemodel" and query_tokens:
                query_filter = Q()
                for token in query_tokens:
                    query_filter |= Q(user__first_name__icontains=token)
                    query_filter |= Q(user__last_name__icontains=token)
                    query_filter |= Q(user__middle_name__icontains=token)
                qs = qs.filter(query_filter).distinct()
            elif query_tokens and any(field.name == "name" for field in model_class._meta.fields):
                query_filter = Q()
                for token in query_tokens:
                    query_filter |= Q(name__icontains=token)
                qs = qs.filter(query_filter)
        except Exception:
            pass

        query_stems = [_token_stem(token) for token in query_tokens]
        scored = []
        seen = set()

        for instance in qs[:300]:
            try:
                snapshot = model_class.get_snapshot(instance.pk)
            except Exception:
                continue

            candidate_id = snapshot.get("id") or instance.pk
            if candidate_id in seen:
                continue
            seen.add(candidate_id)

            candidate_repr = snapshot.get("repr") or str(instance)
            candidate_tokens = _name_tokens(candidate_repr)
            candidate_stems = {_token_stem(token) for token in candidate_tokens}
            score = sum(1 for stem in query_stems if stem in candidate_stems)
            if query_stems and score == 0:
                continue

            snapshot["for_name"] = search_name
            scored.append((score, snapshot))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:max_candidates]]

    try:
        # Разбираем путь модели (app_label.ModelName)
        app_label, model_name = model_path.split('.', 1)
        model_class = apps.get_model(app_label, model_name)
        
        # Проверяем, есть ли у модели нужные методы
        if not hasattr(model_class, 'get_snapshot'):
            return []
        
        candidates = model_class.get_filtered_select_queryset(search_name, request)
        field_candidates = []
        
        for instance in candidates:
            snapshot = model_class.get_snapshot(instance.pk)
            snapshot["for_name"] = search_name
            field_candidates.append(snapshot)
        if field_candidates:
            return field_candidates

        return _fallback_candidates(model_class)
        
    except (ValueError, LookupError, Exception):
        # гнорируем ошибки для конкретной модели и пробуем fallback по БД.
        try:
            app_label, model_name = model_path.split('.', 1)
            model_class = apps.get_model(app_label, model_name)
            return _fallback_candidates(model_class)
        except Exception:
            return []


def find_candidates_for_reference_fields(intent_instance, request):
    """Шаг 1: Найти кандидатов для ссылочных полей"""
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    if not schema:
        return {}
    
    candidates_map = {}
    
    for field_name, raw_value in intent_instance.raw_data.items():
        if field_name == "intent_type":
            continue
            
        field_def = schema.get(field_name)
        if not field_def:
            continue
        
        model_path = field_def.get("model", "")
        
        # Обрабатываем только ссылочные поля
        if model_path and raw_value:
            # Получаем data_path из метаданных поля
            data_path = field_def.get("data_path", "")
            
            # Создаем request с дополнительными параметрами из data_path
            enhanced_request = create_request_with_data_path(request, data_path)
            
            names = _split_reference_names(raw_value, model_path)
            field_candidates = []
            
            for name in names:
                # спользуем отдельную функцию для поиска кандидатов с enhanced_request
                candidates = find_candidates_for_model(model_path, name, enhanced_request, max_candidates=5)
                field_candidates.extend(candidates)
            
            if field_candidates:
                candidates_map[field_name] = field_candidates
    
    return candidates_map


def _name_tokens(value):
    return name_tokens(value)


def _token_stem(token):
    return token_stem(token)


def create_values_for_all_fields(intent_instance, candidates_map):
    """Шаг 2: Создать value для каждого поля"""
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    values_map = {}
    
    for field_name, raw_value in intent_instance.raw_data.items():
        field_def = schema.get(field_name)
        if not field_def:
            continue
        
        field_type = field_def.get("type", "")
        model = field_def.get("model", "")
        
        # Ссылочные поля на любые модели
        if model:
            field_candidates = candidates_map.get(field_name, [])
            
            if not raw_value:
                # спользуем default из метаданных, если есть, иначе None
                default_value = field_def.get("default")
                values_map[field_name] = default_value if default_value is not None else None
                continue

            value = resolve_reference_field_value(
                raw_value=raw_value,
                model_path=model,
                field_type=field_type,
                candidates=field_candidates,
            )

            if field_type == "ManyToManyField":
                if value:
                    values_map[field_name] = value
                else:
                    default_value = field_def.get("default")
                    values_map[field_name] = default_value if default_value is not None else []
            else:
                if value is not None:
                    values_map[field_name] = value
                else:
                    default_value = field_def.get("default")
                    values_map[field_name] = default_value if default_value is not None else None
        
        # Поля даты/времени
        elif field_type == "DateTimeField":
            resolved_date = validate_datetime(raw_value)
            if resolved_date:
                values_map[field_name] = resolved_date
            else:
                # спользуем default из метаданных, если есть, иначе None
                default_value = field_def.get("default")
                values_map[field_name] = default_value if default_value is not None else None
        
        # Текстовые поля
        else:
            if raw_value is not None:
                values_map[field_name] = str(raw_value)
            else:
                # спользуем default из метаданных, если есть, иначе None
                default_value = field_def.get("default")
                values_map[field_name] = default_value if default_value is not None else None
    
    return values_map


def fill_resolved_from_values(intent_instance, values_map):
    """Шаг 3: Заполнить resolved исходя из полей value"""
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    resolved_map = {}
    
    for field_name, value in values_map.items():
        field_def = schema.get(field_name)
        if not field_def:
            continue
        
        field_type = field_def.get("type", "")
        model = field_def.get("model", "")
        
        # Ссылочные поля на любые модели
        if model:
            if value:
                if isinstance(value, list):
                    # ManyToManyField - список ID
                    resolved_value = [item["id"] for item in value if "id" in item]
                    resolved_map[field_name] = resolved_value if resolved_value else []
                else:
                    # ForeignKey/OneToOneField - одно ID
                    resolved_map[field_name] = value.get("id") if "id" in value else None
        # Все остальные поля - значение уже готово
        else:
            if value is not None:
                resolved_map[field_name] = value
    return resolved_map


def update_field_statuses(intent_instance, resolved_map):
    """Шаг 4: Обновить статусы полей"""
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    statuses_map = {}
    
    for field_name, field_def in schema.items():
        required = field_def.get("required", False)
        resolved = resolved_map.get(field_name)
        
        # Определяем статус согласно таблице
        if required:
            if resolved:
                statuses_map[field_name] = "ready"
            else:
                statuses_map[field_name] = "missing"
        else:
            if resolved:
                statuses_map[field_name] = "ready"
            else:
                statuses_map[field_name] = "optional"
    
    return statuses_map


def update_intent_status(intent_instance, statuses_map):
    """Шаг 5: Обновить статус всего intention"""
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    
    # Проверяем все обязательные поля
    for field_name, field_def in schema.items():
        required = field_def.get("required", False)
        if required:
            field_status = statuses_map.get(field_name, "missing")
            if field_status != "ready":
                return "resolving"
    return "ready"


def validate_datetime(date_str):
    """Валидация даты и времени"""
    if not date_str:
        return None
    
    try:
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(date_str), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return None
        
    except Exception:
        return None


def extract_values_map_from_resolutions(intent_instance):
    """звлечь values_map из текущих resolutions"""
    values_map = {}
    
    for field_name, resolution in intent_instance.resolutions.items():
        values_map[field_name] = resolution.get("value")
    
    return values_map


def build_resolutions(intent_instance, request):
    """Построить resolutions из raw_data по шагам (для первичного создания)"""
    if not intent_instance.raw_data or not intent_instance.intent_type:
        return
    
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    schema = metadata.get('fields', {})
    if not schema:
        return
    
    # Шаг 1: Найти кандидатов для ссылочных полей
    candidates_map = find_candidates_for_reference_fields(intent_instance, request)
    
    # Шаг 2: Создать value для каждого поля
    values_map = create_values_for_all_fields(intent_instance, candidates_map)
    
    # Шаг 3: Заполнить resolved исходя из полей value
    resolved_map = fill_resolved_from_values(intent_instance, values_map)
    
    # Шаг 4: Добавить фиксированные значения из метаданных в resolved_data
    fixed_values = metadata.get('fixed_values', {})
    for field_name, fixed_value in fixed_values.items():
        resolved_map[field_name] = fixed_value
    
    # Шаг 5: Обновить статусы полей
    statuses_map = update_field_statuses(intent_instance, resolved_map)
    
    # Шаг 6: Обновить статус всего intention
    intent_status = update_intent_status(intent_instance, statuses_map)
    
    # Собираем итоговые resolutions
    resolutions = {}
    
    for field_name, field_def in schema.items():
        model = field_def.get("model", "")
        
        resolution = {
            "candidates": candidates_map.get(field_name, []),
            "value": values_map.get(field_name),
            "resolved": resolved_map.get(field_name),
            "status": statuses_map.get(field_name)
        }
        
        # Добавляем пустой metadata для полей с model "users.ProfileModel" - про просьбе Кирилла.
        if model == "users.ProfileModel":
            resolution["metadata"] = {}
        
        resolutions[field_name] = resolution
    
    intent_instance.resolutions = resolutions
    intent_instance.resolved_data = resolved_map
    intent_instance.status_id = intent_status


def build_resolved_data(intent_instance):
    """Обновить resolved_data и статусы из resolutions (для повторных обновлений)"""
    if not intent_instance.resolutions:
        return
    
    # Шаг 1: звлекаем values_map из текущих resolutions
    values_map = extract_values_map_from_resolutions(intent_instance)
    
    # Шаг 2: Заполнить resolved исходя из полей value (шаг 3 из основного процесса)
    resolved_map = fill_resolved_from_values(intent_instance, values_map)
    
    # Шаг 3: Добавить фиксированные значения из метаданных в resolved_data
    metadata = getattr(intent_instance.intent_type, 'metadata', {})
    fixed_values = metadata.get('fixed_values', {})
    for field_name, fixed_value in fixed_values.items():
        resolved_map[field_name] = fixed_value
    
    # Шаг 4: Обновить статусы полей (шаг 5 из основного процесса)
    statuses_map = update_field_statuses(intent_instance, resolved_map)
    
    # Шаг 5: Обновить статус всего intention (шаг 6 из основного процесса)
    intent_status = update_intent_status(intent_instance, statuses_map)
    
    # Шаг 6: Обновить resolutions с новыми данными
    for field_name, resolution in intent_instance.resolutions.items():
        # Обновляем resolved и status в существующих resolutions
        resolution["resolved"] = resolved_map.get(field_name)
        resolution["status"] = statuses_map.get(field_name, "ready")
    
    # Шаг 7: Обновить resolved_data и статус intent-а
    intent_instance.resolved_data = resolved_map
    intent_instance.status_id = intent_status

