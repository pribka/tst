from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.cache import cache

from rest_framework import serializers

from haystack import indexes
from django.db.models.signals import (
    # class_prepared,
    # m2m_changed,
    post_delete,
    # post_init,
    # post_migrate,
    # post_save,
    # pre_delete,
    # pre_init,
    # pre_migrate,
    # pre_save,
)

from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog


class PVH(BaseAbstractModel):
    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE,
                                     verbose_name='Для какой модели делаем ПВХ')
    attr_names = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Список атрибутов',
        help_text='Атрибуты объекта, от которых зависит наличие ПВХ (список)'
    )

    def __str__(self):
        return self.content_type.name


class PVHProperty(BaseAbstractModel):
    """ Описание поля ПВХ """
    REFERENCE = 0
    STRING = 1
    TEXT = 2
    BOOLEAN = 3
    DATE = 4
    DATETIME = 5
    TIME = 6
    NUMBER_INT = 7
    NUMBER_FLOAT = 8
    NUMBER_DECIMAL = 9

    PROPERTY_TYPE_CHOICES = [
        (REFERENCE, 'Ссылка'),
        (STRING, 'Строка'),
        (TEXT, 'Текст'),
        (BOOLEAN, 'Булево'),
        (DATE, 'Дата'),
        (DATETIME, 'Дата и время'),
        (TIME, 'Время'),
        (NUMBER_INT, 'Целое число'),
        (NUMBER_FLOAT, 'Float число'),
        (NUMBER_DECIMAL, 'Decimal число (для точных вычислений)'),

    ]
    # pvh = models.ForeignKey(PVH, on_delete=models.CASCADE)
    pvhs = models.ManyToManyField(
        PVH,
        related_name='pvh_properties',
        through='PVHPropertyThrough',
    )
    multi = models.BooleanField(default=False, verbose_name='Мультизначение')
    code = models.CharField(max_length=255,
                            blank=False,
                            unique=True,
                            verbose_name='Символьный код поля')

    property_type = models.IntegerField(choices=PROPERTY_TYPE_CHOICES,
                                        default=0,
                                        verbose_name='Тип значения поля')
    fk_model = models.ForeignKey(ContentType,
                                 null=True,
                                 blank=True,
                                 on_delete=models.CASCADE,
                                 verbose_name='Модель для типа "Ссылка"')

    extra_catalogs = models.ManyToManyField(
        to='ExtraCatalogModel',
        through='ExtraCatalogPropertyThroughModel',
        through_fields=('pvh_property', 'extra_catalog',)
    )

    def __str__(self):
        property_type = ''
        for code, name in self.PROPERTY_TYPE_CHOICES:
            if code == self.property_type:
                property_type = name
                break

        return f"{self.code} {property_type}"

    def get_name(self):
        return f'x_{self.code}'

    @property
    def name(self):
        return self.get_name()

    def get_value_field_name(self):
        """
        Тестировал относительно BasePropertyValue
         Тесты: website_bakery/pvh/tests.py
         """
        if self.property_type == PVHProperty.REFERENCE:
            return 'value_fk'
        elif self.property_type == PVHProperty.STRING:
            return 'value_str'
        elif self.property_type == PVHProperty.TEXT:
            return 'value_text'
        elif self.property_type == PVHProperty.BOOLEAN:
            return 'value_bool'
        elif self.property_type == PVHProperty.DATE:
            return 'value_date'
        elif self.property_type == PVHProperty.DATETIME:
            return 'value_datetime'
        elif self.property_type == PVHProperty.TIME:
            return 'value_time'
        elif self.property_type == PVHProperty.NUMBER_INT:
            return 'value_int'
        elif self.property_type == PVHProperty.NUMBER_FLOAT:
            return 'value_float'
        elif self.property_type == PVHProperty.NUMBER_DECIMAL:
            return 'value_decimal'
        raise ValueError('No such property_type')

    def get_field_serializer(self, required=True):
        """
        allow_null нужно, чтобы в validated_data попадали такие значения как "x_prop_date": None
        """
        from .serializers import FastModelSerializer
        if self.property_type == PVHProperty.REFERENCE:
            # print(self, 'self.fk_model:', self.fk_model, 'model_class:',self.fk_model.model_class())
            return FastModelSerializer(self.fk_model.model_class(), required=required, allow_null=True)

        elif self.property_type == PVHProperty.STRING:
            return serializers.CharField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.TEXT:
            return serializers.CharField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.BOOLEAN:
            return serializers.BooleanField(required=required, allow_null=True)

        elif self.property_type == PVHProperty.DATE:
            return serializers.DateField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.DATETIME:
            return serializers.DateTimeField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.TIME:
            return serializers.TimeField(required=required, allow_null=True)

        elif self.property_type == PVHProperty.NUMBER_INT:
            return serializers.IntegerField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.NUMBER_FLOAT:
            return serializers.FloatField(required=required, allow_null=True)
        elif self.property_type == PVHProperty.NUMBER_DECIMAL:
            return serializers.DecimalField(max_digits=10, decimal_places=3, required=required, allow_null=True)

        else:
            return serializers.CharField(required=required, allow_null=True)

    def get_haystack_field_type(self):
        if self.multi:
            return indexes.CharField(null=True)
        if self.property_type == PVHProperty.REFERENCE:
            return indexes.CharField(null=True)
        elif self.property_type == PVHProperty.STRING:
            return indexes.CharField(null=True)
        elif self.property_type == PVHProperty.TEXT:
            return indexes.CharField(null=True)
        elif self.property_type == PVHProperty.BOOLEAN:
            return indexes.BooleanField(null=True)

        elif self.property_type == PVHProperty.DATE:
            return indexes.DateField(null=True)
        elif self.property_type == PVHProperty.DATETIME:
            return indexes.DateTimeField(null=True)
        elif self.property_type == PVHProperty.TIME:
            return indexes.CharField(null=True)

        elif self.property_type == PVHProperty.NUMBER_INT:
            return indexes.IntegerField(null=True)
        elif self.property_type == PVHProperty.NUMBER_FLOAT:
            return indexes.FloatField(null=True)
        elif self.property_type == PVHProperty.NUMBER_DECIMAL:
            return indexes.CharField(null=True)  # Десятичные все равно как строка сохраняются
        else:
            return serializers.CharField(null=True)

    @classmethod
    def add_serializer_fields(cls, serializer_instance, model, required=True):
        properties = cls.get_properties_for(model)
        for prop in properties:
            prop_name = prop.get_name()
            if prop.multi:
                """
                Чтобы посмотреть поля сериализатора, в отладке в сериализаторе наберите self.__repr__()
                """
                if prop.property_type == PVHProperty.REFERENCE:
                    from .serializers import FastModelSerializer
                    serializer_instance.fields[prop_name] = FastModelSerializer(prop.fk_model.model_class(), required=required, allow_null=True, many=True)
                else:
                    """
                    Делаем serializers.ListField(..., required=False), чтобы пускал в сериализатор.
                    Путь: ListSerializer.is_valid() ->  self.run_validation() -> self.validate_empty_values() -> if data is empty -> if self.required
                    """
                    serializer_instance.fields[prop_name] = serializers.ListField(child=prop.get_field_serializer(required=required), required=required)
            else:
                serializer_instance.fields[prop_name] = prop.get_field_serializer(required=required)

    @classmethod
    def get_properties(cls, model, multi=None):
        lookup = Q(pvhs__content_type=ContentType.objects.get_for_model(model))
        if multi is not None:
            assert type(multi) == bool, "get_properties: параметр multi должен быть bool"
            lookup &= Q(multi=multi)
        return cls.objects.filter(lookup)

    @classmethod
    def get_properties_for(cls, model):
        return cls._get_cached_property_queryset_for(model)

    @classmethod
    def get_property_queryset_cache_key_for(cls, model):
        return model.get_default_cache_key() + '_properties'

    @classmethod
    def set_property_queryset_cache_for(cls, model):
        queryset = PVHProperty.objects.filter(pvhs__content_type=ContentType.objects.get_for_model(model)).distinct()
        key = cls.get_property_queryset_cache_key_for(model)
        cache.set(key, queryset, BaseAbstractModel.cache_timeout_one_week())

    @classmethod
    def _get_cached_property_queryset_for(cls, model):
        key = cls.get_property_queryset_cache_key_for(model)
        queryset = cache.get(key)
        # Странное поведение, если сделать if queryset is None:
        if not queryset:
            cls.set_property_queryset_cache_for(model)
        return cache.get(key)

    @classmethod
    def remove_pvh_fields(cls, validated_data, model):
        """Убрать поля ПВХ в сериализаторе"""
        props = PVHProperty.get_properties_for(model)
        result = {}
        for prop in props:
            val = validated_data.pop(prop.get_name(), None)
            result[prop.code] = val
        return result

    @classmethod
    def get_property(cls, model, prop_code):
        key = PVHProperty.get_cache_key(model, prop_code)
        value = cache.get(key)
        if value is not None:
            return value
        PVHProperty.set_property_cache(model, prop_code)
        return cache.get(key)

    @classmethod
    def set_property_cache(cls, model, prop_code):
        value = PVHProperty.objects.get(pvhs__content_type=ContentType.objects.get_for_model(model), code=prop_code)
        key = PVHProperty.get_cache_key(model, prop_code)
        cache_timeout = PVHProperty.cache_timeout_one_day()
        cache.set(key, value, cache_timeout)

    @classmethod
    def get_cache_key(cls, model, prop_code):
        return model._meta.label_lower + '_' + prop_code

    def save(self, *args, **kwargs):
        if self.created_at:
            # Случай когда у существующей записи что-то меняют
            old_obj = PVHProperty.objects.get(pk=self.pk)
            if PVHProperty.objs_are_different(old_obj, self):
                pvhs = old_obj.pvhs.all()
                for pvh in pvhs:
                    model = pvh.content_type.model_class()
                    key = PVHProperty.get_cache_key(model, old_obj.code)
                    cache.delete(key)
        super().save(*args, **kwargs)
        pvhs = self.pvhs.all()
        for pvh in pvhs:
            model = pvh.content_type.model_class()
            PVHProperty.set_property_cache(model, self.code)
            PVHProperty.set_property_queryset_cache_for(model)

    @classmethod
    def objs_are_different(cls, old_obj, new_obj):
        fields = ['multi', 'code', 'property_type', 'fk_model']
        for field in fields:
            old_value = getattr(old_obj, field)
            new_value = getattr(new_obj, field)
            if old_value != new_value:
                return True
        return False


@receiver(post_delete, sender=PVHProperty)
def clear_property_cache(sender, instance, **kwargs):
    pvhs = instance.pvhs.all()
    for pvh in pvhs:
        model = pvh.content_type.model_class()
        key = PVHProperty.get_cache_key(model, instance.code)
        cache.delete(key)
        key = PVHProperty.get_property_queryset_cache_key_for(model)
        cache.delete(key)


class PVHPropertyThrough(BaseAbstractModel):
    pvh = models.ForeignKey(
        PVH,
        null=True,
        blank=False,
        on_delete=models.CASCADE,
        related_name='pvh_property_through'
    )
    name = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
    )
    property = models.ForeignKey(
        PVHProperty,
        null=True,
        blank=False,
        on_delete=models.CASCADE,
        related_name='pvh_property_through'
    )
    condition = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Условие',
        help_text='Условие наличе атрибута. Словарь. Ключи использовать из attr_names у pvh'
    )

    widget = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Виджет',
        help_text='Метаданные для фронтенда'
    )

    class Meta:
        unique_together = (('pvh', 'property',),)


class BasePVHPropertyValue(BaseAbstractModel):
    """Базовый класс для таблицы значений ПВХ"""

    class Meta:
        abstract = True
        unique_together = ['owner', 'prop', 'value_index']
    owner = models.ForeignKey(BaseModel,
                              on_delete=models.CASCADE,
                              related_name='property_values')
    prop = models.ForeignKey(PVHProperty, on_delete=models.CASCADE)

    value_fk = models.ForeignKey(BaseModel, null=True, blank=True, on_delete=models.CASCADE,
                                 related_name='in_property_values')
    value_str = models.CharField(max_length=255, null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    value_bool = models.BooleanField(null=True,blank=True)
    value_date = models.DateField(null=True, blank=True)
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_time = models.TimeField(null=True, blank=True)
    value_int = models.IntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_decimal = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=10)

    value_index = models.IntegerField(default=0, blank=True, verbose_name='Индекс множественного значения')

    @property
    def value(self):
        return self.get_value()

    def get_value(self):
        if self.prop.property_type == PVHProperty.STRING:
            return self.value_str, None
        if self.prop.property_type == PVHProperty.TEXT:
            return self.value_text, None
        elif self.prop.property_type == PVHProperty.NUMBER_INT:
            return self.value_int, None
        elif self.prop.property_type == PVHProperty.NUMBER_FLOAT:
            return self.value_float, None
        elif self.prop.property_type == PVHProperty.NUMBER_DECIMAL:
            return self.value_decimal, None
        elif self.prop.property_type == PVHProperty.BOOLEAN:
            return self.value_bool, None
        elif self.prop.property_type == PVHProperty.DATE:
            return self.value_date, None
        elif self.prop.property_type == PVHProperty.DATETIME:
            return self.value_datetime, None
        elif self.prop.property_type == PVHProperty.TIME:
            return self.value_time, None
        elif self.prop.property_type == PVHProperty.REFERENCE:
            return self.value_fk, self.value_fk.id
        else:
            return None

    def save(self, *args, **kwargs):
        self.full_clean()  # Вызываем метод full_clean() перед сохранением
        super().save(*args, **kwargs)

    def full_clean(self, *args, **kwargs):
        if self.prop.property_type == PVHProperty.STRING and self.value_str is None:
            raise ValidationError({'value_str': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.TEXT and self.value_text is None:
            raise ValidationError({'value_text': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.NUMBER_INT and self.value_int is None:
            raise ValidationError({'value_int': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.NUMBER_FLOAT and self.value_float is None:
            raise ValidationError({'value_float': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.NUMBER_DECIMAL and self.value_decimal is None:
            raise ValidationError({'value_decimal': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.BOOLEAN and self.value_bool is None:
            raise ValidationError({'value_bool': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.DATE and self.value_date is None:
            raise ValidationError({'value_date': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.DATETIME and self.value_datetime is None:
            raise ValidationError({'value_datetime': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.TIME and self.value_time is None:
            raise ValidationError({'value_time': 'Это поле обязательно для заполнения.'})
        elif self.prop.property_type == PVHProperty.REFERENCE and self.value_fk is None:
            raise ValidationError({'value_fk': 'Это поле обязательно для заполнения.'})
        super().full_clean(*args, **kwargs)


class PVHPropertyValue(BasePVHPropertyValue):
    """
    Хранить ПВХ значения любой базовой модели
    """
    pass


class ExtraCatalogModel(BaseCatalog, BaseAbstractCatalog):

    pvh_properties = models.ManyToManyField(
        to='PVHProperty',
        through='ExtraCatalogPropertyThroughModel',
        through_fields=('extra_catalog', 'pvh_property')
    )

    @classmethod
    def get_select_queryset(cls, request=None):
        if request:
            pvh_property_code = request.query_params.get('property')
            if pvh_property_code:
                qs = cls.objects.filter(is_active=True, pvh_properties__code=pvh_property_code)
            else:
                qs = cls.objects.none()
        else:
            qs = cls.objects.none()
        return qs

    class Meta:
        verbose_name = 'Дополнительная запись'
        verbose_name_plural = 'Дополнительные записи'
        ordering = ('sort', 'name',)


class ExtraCatalogPropertyThroughModel(BaseAbstractModel):
    extra_catalog = models.ForeignKey(
        to='ExtraCatalogModel',
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name='extracatalog_property_through'
    )
    pvh_property = models.ForeignKey(
        to='PVHProperty',
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name='extracatalog_property_through'
    )

    class Meta:
        verbose_name = 'M2M связь атрибута ПВХ с дополнительной записью'
        verbose_name_plural = 'M2M связи атрибута ПВХ с дополнительными записями'
        unique_together = (('extra_catalog', 'pvh_property',),)
        ordering = ('sort', '-created_at',)
