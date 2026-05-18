# 🔹 Стандартная библиотека
import copy
from datetime import datetime
import pytz

# 🔹 Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.utils.duration import duration_string

# 🔹 Django REST framework
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# 🔹 Третьи библиотеки
from mptt.models import TreeForeignKey
from bs4 import BeautifulSoup

# 🔹 Локальные импорты
from common.models import BaseModel
from common.utils import is_uuid
from .utils_meta import get_field_meta
from .utils import (
    apply_default_active_date_filter_values,
    apply_filter_preset_to_report_metadata,
)
from .models import ReportSettingsModel, UserReportSettingsModel, ReportCategoryModel


class HtmlStrippedCharField(serializers.CharField):
    """CharField, который удаляет HTML-теги."""
    def to_representation(self, value):
        if value is None:
            return None
        result = super().to_representation(value)
        
        if not isinstance(result, str) or not result:
            return result
        
        try:
            soup = BeautifulSoup(result, 'html.parser')
            cleaned = soup.get_text(separator=' ', strip=True)
            return cleaned
        except Exception:
            return result


class TimezoneDateTimeField(serializers.DateTimeField):
    def __init__(self, user_timezone=None, **kwargs):
        self.user_timezone = user_timezone
        super().__init__(**kwargs)
    
    def to_representation(self, value):
        if value is None:
            return None
        
        # Конвертируем в пользовательский часовой пояс если указан
        if self.user_timezone:
            try:
                tz = pytz.timezone(self.user_timezone)
                if value.tzinfo is not None:
                    # Значение уже с timezone, конвертируем
                    value = value.astimezone(tz)
                else:
                    # Значение naive, считаем что оно в UTC
                    value = pytz.utc.localize(value).astimezone(tz)
            except Exception:
                # Если ошибка с timezone, используем оригинальное значение
                pass
        
        # Форматируем как '%Y-%m-%d %H:%M'
        return value.strftime('%Y-%m-%d %H:%M')


class LocalizedBooleanField(serializers.BooleanField):
    def to_representation(self, value):
        if value is None:
            return None
        elif value is True:
            return "Да"
        elif value is False:
            return "Нет"
        else:
            return value


class DurationFormatField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        try:
            # Поддерживаем timedelta и int/float (секунды)
            from datetime import timedelta
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
            elif isinstance(value, (int, float)):
                total_seconds = int(value)
            else:
                return str(value)
        except Exception:
            return str(value)

        sign = '-' if total_seconds < 0 else ''
        total_seconds = abs(total_seconds)
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)

        time_part = f"{hours}:{minutes:02d}:{secs:02d}"
        
        if days > 0:
            result = f"{days}д., {time_part}"
        else:
            result = time_part

        return f"{sign}{result}" if sign else result


class ChoiceDisplayField(serializers.Field):
    """Поле для отображения choices в человекочитаемом виде. Работает с любым типом поля."""
    def __init__(self, choices=None, **kwargs):
        self.choices_map = {}
        if choices:
            self.choices_map = {str(choice[0]): str(choice[1]) for choice in choices}
        super().__init__(**kwargs)
    
    def to_representation(self, value):
        if value is None or value == "":
            return value
        # Преобразуем значение в строку для поиска в choices_map
        str_value = str(value)
        return self.choices_map.get(str_value, value)


class CTSerializer(serializers.ModelSerializer):
    repr = serializers.SerializerMethodField(read_only=True)

    def get_repr(self, obj):
        return obj.__str__()

    class Meta:
        model = ContentType
        fields = '__all__'


class CTSerializerById(serializers.Serializer):
    def to_representation(self, obj):
        obj_obj = ContentType.objects.get(pk=obj)
        return CTSerializer(obj_obj).data


class FastSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='pk')  # Поле id (UUID)
    repr = serializers.CharField(source='__str__', read_only=True)  # Поле repr (строковое представление)
    ct = CTSerializer(read_only=True)
    code = serializers.CharField(read_only=True)

    class Meta:
        model = None  # Модель будет установлена динамически
        fields = ['id', 'repr', 'ct', 'code']  # Включаем поля id, repr и ct (если оно есть в модели). code для FK, где to_field='code'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Добавляем поле "file", если это FileModel
        if instance.__class__.__name__ == 'FileModel' and hasattr(instance, 'file'):
            data['file'] = instance.file.url if instance.file else None

        return data

    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)  # Извлекаем model_class из kwargs
        if model_class:
            self.Meta.model = model_class  # Устанавливаем модель для сериализатора
            self.Meta.ref_name = f"{model_class.__name__}FastSerializer"  # Уникальное имя ref_name
        super().__init__(*args, **kwargs)


class FastSerializerById(serializers.Serializer):
    def to_representation(self, obj):
        if not obj:
            return None
        # Для M2M полей, которые предварительно аннотированы как список id
        if isinstance(obj, (tuple, set)):
            obj = list(obj)
        if not isinstance(obj, list):
            try:
                import numpy as np  # noqa: WPS433 (local import by design)
                if isinstance(obj, np.ndarray):
                    obj = obj.tolist()
            except Exception:
                pass

        if isinstance(obj, list):
            # Для TagModel в отчётах фронт ожидает строку через запятую
            # (list[dict] визуально часто "схлопывается" и рендерится не так, как надо).
            if (
                getattr(self, "model_class", None) is not None
                and getattr(self.model_class, "__name__", "") == "TagModel"
            ):
                reprs = []
                for item in obj:
                    item_data = self.to_representation(item)
                    if isinstance(item_data, dict):
                        repr_value = item_data.get("repr") or item_data.get("url")
                        if repr_value:
                            reprs.append(str(repr_value))
                    elif item_data is not None:
                        reprs.append(str(item_data))
                return ", ".join(reprs) if reprs else ""

            # Для остальных типов возвращаем исходную структуру list[dict]
            # как и раньше (это нужно для LinkListField/прочих list-полей).
            return [self.to_representation(item) for item in obj]

        # Если это уже экземпляр модели — сериализуем напрямую
        if isinstance(obj, self.model_class):
            obj = obj.pk

        cache_key = f"{self.model_class.__name__}_{obj}"
        data = cache.get(cache_key)
        if data:
            return data
        #   print('no cache')
        if self.model_class == User:
            obj_obj = User.objects.get(pk=obj)
        elif is_uuid(obj):
            obj_obj = BaseModel.objects.super_get(pk=obj)
        elif isinstance(obj, int):
            obj_obj = self.model_class.objects.get(pk=obj)
        elif isinstance(obj, str):
            try:
                obj_obj = self.model_class.objects.get(code=obj)
            except:
                raise ValidationError('Cannot get original object.')
        else:
            raise ValidationError('Unknown obj type. Cannot get original object.')
        data = FastSerializer(obj_obj, model_class=self.model_class).data
        cache.set(cache_key, data, timeout=3600)
        return data

    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)  # Извлекаем model_class из kwargs
        if model_class:
            self.model_class = model_class

        super().__init__(*args, **kwargs)


class UniversalModelReadSerializer(serializers.ModelSerializer):

    def get_nested_field(self, field_path, model):
        """
        Возвращает сериализатор или поле DRF для полей, которых нет в модели.
        Разбирает поле вида 'manager_position__name__title' начиная с model.
        Для аннотированных / агрегированных полей возвращает CharField.
        """
        # Унифицированное сопоставление типов полей Django -> DRF поля
        field_map = {
            models.CharField: HtmlStrippedCharField(read_only=True),
            models.TextField: HtmlStrippedCharField(read_only=True),
            models.IntegerField: serializers.IntegerField(read_only=True),
            models.BooleanField: LocalizedBooleanField(read_only=True),
            models.FloatField: serializers.FloatField(read_only=True),
            models.DateTimeField: TimezoneDateTimeField(user_timezone=self._user_timezone, read_only=True),
            models.DateField: serializers.DateField(read_only=True),
            models.TimeField: serializers.TimeField(read_only=True),
            models.DecimalField: serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True),
            models.DurationField: DurationFormatField(read_only=True),
            models.EmailField: serializers.EmailField(read_only=True),
            models.URLField: serializers.URLField(read_only=True),
            models.JSONField: serializers.JSONField(read_only=True),
        }
        try:
            field, model = get_field_meta(field_path, model)
        except Exception:
            field, model = None, None

        # Поле не найдено в модели (get_field_meta вернул None или выбросил) — аннотированное/агрегатное
        if field is None:
            if model is not None:
                # Вычисляемое FK из get_report_computed_fields_meta (get_field_meta уже вернул related_model)
                return FastSerializerById(read_only=True, model_class=model)
            of = None
            if hasattr(self, '_annotation_output_fields') and self._annotation_output_fields:
                of = self._annotation_output_fields.get(field_path)
            if of is not None:
                for model_field, serializer_field in field_map.items():
                    if isinstance(of, model_field):
                        return serializer_field
                return HtmlStrippedCharField(read_only=True)
            return HtmlStrippedCharField(read_only=True)
        
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            return FastSerializerById(read_only=True, model_class=model)
        elif isinstance(field, models.ManyToManyField):
            if self._list:
                return FastSerializerById(read_only=True, model_class=model)
            else:
                if self._retrieve:
                    return FastSerializer(read_only=True, model_class=model, many=True)

        # Проверяем choices перед обычным маппингом
        if hasattr(field, 'choices') and field.choices:
            return ChoiceDisplayField(choices=field.choices, read_only=True)

        for model_field, serializer_field in field_map.items():
            if isinstance(field, model_field):
                return serializer_field

        # По умолчанию — HtmlStrippedCharField
        return HtmlStrippedCharField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        model_fields = self.Meta.model._meta.get_fields()
        if self._field_names is not None:
            allowed_fields = set(self._field_names or [])
        else:
            allowed_fields = None

        for field in model_fields:
            # Проверяем, что поле не имеет суффикса _ptr

            if allowed_fields is not None and field.name not in allowed_fields:
                continue
            if field.name.endswith('_ptr'):
                continue
            if field.name == 'parent':
                pass
            if field.name == 'ct':
                if self._list:
                    fields['ct'] = CTSerializerById(read_only=True)
                else:
                    fields['ct'] = CTSerializer(read_only=True)

            elif isinstance(field, (models.OneToOneField, models.ForeignKey, TreeForeignKey)):
                field_name = field.name  # Имя поля
                if self._list:
                    # Добавляем FastSerializer для ссылочных полей.
                    fields[field_name] = FastSerializerById(read_only=True, model_class=field.related_model)  
                else:
                    if self._retrieve:
                        fields[field_name] = FastSerializer(read_only=True, model_class=field.related_model)
            elif isinstance(field, models.ManyToManyField):
                field_name = field.name  # Имя поля
                if self._list:
                    # Добавляем FastSerializer для ссылочных полей.
                    fields[field_name] = FastSerializerById(read_only=True, model_class=field.related_model)  
                else:
                    if self._retrieve:
                        fields[field_name] = FastSerializer(read_only=True, model_class=field.related_model, many=True)
            elif isinstance(field, (models.CharField, models.TextField)):
                field_name = field.name
                # Если у поля есть choices, используем ChoiceDisplayField
                if hasattr(field, 'choices') and field.choices:
                    fields[field_name] = ChoiceDisplayField(choices=field.choices, read_only=True)
                else:
                    fields[field_name] = HtmlStrippedCharField(read_only=True)
            elif isinstance(field, models.DateTimeField):
                field_name = field.name
                fields[field_name] = TimezoneDateTimeField(user_timezone=self._user_timezone, read_only=True)
            elif isinstance(field, models.BooleanField):
                field_name = field.name
                fields[field_name] = LocalizedBooleanField(read_only=True)
            elif isinstance(field, models.DurationField):
                field_name = field.name
                fields[field_name] = DurationFormatField(read_only=True)
            elif isinstance(field, (models.IntegerField, models.SmallIntegerField, 
                                   models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                field_name = field.name
                # Если у поля есть choices, используем ChoiceDisplayField
                if hasattr(field, 'choices') and field.choices:
                    fields[field_name] = ChoiceDisplayField(choices=field.choices, read_only=True)
                else:
                    fields[field_name] = serializers.IntegerField(read_only=True)

        # Добавляем аннотированные / агрегированные или виртуальные поля
        if self._field_names:
            for fname in self._field_names:
                if fname in fields:
                    continue
                fields[fname] = self.get_nested_field(fname, self.Meta.model)

                # # Здесь попытка добавить сериализатор основного поля? Например, если status__code, то добавить сериализованный status?
                # if '__' in fname:
                #     base = fname.split('__')[0]
                # #    try:
                # #        related_model = self.Meta.model._meta.get_field(base).related_model
                # #        fields[fname] = FastSerializerById(read_only=True, model_class=related_model)
                # #    except Exception:
                # #        continue
                # else:
                #     # агрегат или виртуальное поле
                #     fields[fname] = serializers.CharField()

        fields_result = {}
        if allowed_fields is not None:
            for field in allowed_fields:
                fields_result[field] = fields[field]
        else:
            fields_result = fields
        return fields_result

    class Meta:
        model = None  # Модель будет установлена динамически
        fields = '__all__'  # Включаем все поля модели

    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)  # Извлекаем model_class из kwargs
        self._field_names = kwargs.pop("field_names", None)
        self._list = kwargs.pop("list", False)
        self._retrieve = kwargs.pop("retrieve", False)
        self._user_timezone = kwargs.pop("user_timezone", None)  # Извлекаем user_timezone из kwargs
        self._annotation_output_fields = kwargs.pop('annotation_output_fields', {}) or {}

        if model_class:
            self.Meta.model = model_class  # Устанавливаем модель для сериализатора
            self.Meta.ref_name = f"{model_class.__name__}UniversalModelReadSerializer"  # Уникальное имя ref_name
        super().__init__(*args, **kwargs)


# ОБЩИЕ НАСТРОЙКИ ОТЧЕТОВ

class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategoryModel
        fields = (
            'id',
            'code',
            'name',
            'sort',
        )


class ReportSettingsListSerializer(serializers.ModelSerializer):
    is_base = serializers.BooleanField(read_only=True, default=True)
    category = ReportCategorySerializer(read_only=True)

    class Meta:
        model = ReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'code',
            'app_section_code',
            'category',
            'is_base',
            )
        
class ReportSettingsDetailSerializer(serializers.ModelSerializer):
    is_base = serializers.BooleanField(read_only=True, default=True)
    category = ReportCategorySerializer(read_only=True)

    class Meta:
        model = ReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'code',
            'app_section_code',
            'category',
            'metadata',
            'is_base',
            )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        preset_key = None
        if request:
            raw = request.query_params.get('filter_preset')
            if raw is not None:
                preset_key = raw.strip() or None
        if preset_key:
            metadata = apply_filter_preset_to_report_metadata(
                data['metadata'],
                instance.filter_presets,
                preset_key,
            )
        else:
            metadata = copy.deepcopy(data['metadata'])
        data['metadata'] = apply_default_active_date_filter_values(metadata)
        return data

# ПОЛЬЗОВАТЕЛЬСКИЕ НАСТРОЙКИ ОТЧЕТОВ
class UserReportSettingsCreateSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField()
    class Meta:
        model = UserReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'app_section_code',
            'metadata',
            'base_report',
            )
    def create(self, validated_data):
        metadata = validated_data.pop('metadata', {})
        instance = super().create(validated_data)
        instance.metadata = metadata  # вызовет @metadata.setter
        instance.save()
        return instance


class UserReportSettingsUpdateSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField()
    class Meta:
        model = UserReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'app_section_code',
            'metadata',
            'base_report',
            )

    def update(self, instance, validated_data):
        metadata = validated_data.pop('metadata', None)
        instance = super().update(instance, validated_data)
        if metadata is not None:
            instance.metadata = metadata  # вызовет @metadata.setter
            instance.save()
        return instance


class UserReportSettingsListSerializer(serializers.ModelSerializer):
    is_base = serializers.BooleanField(read_only=True, default=False)
    category = ReportCategorySerializer(source='base_report.category', read_only=True)

    class Meta:
        model = UserReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'app_section_code',
            'base_report',
            'category',
            'is_base',
            )
        
class UserReportSettingsDetailSerializer(serializers.ModelSerializer):
    is_base = serializers.BooleanField(read_only=True, default=False)
    
    class Meta:
        model = UserReportSettingsModel
        fields = (
            'id',
            'name',
            'description',
            'app_section_code',
            'metadata',
            'base_report',
            'is_base',
            )