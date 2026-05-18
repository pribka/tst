from django.utils.dateparse import parse_date
from rest_framework import serializers

from bpms.tasks import models as t_models
from common.serializers import BaseCatalogListSerializer

from . import models as wl_models


class WorkScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = wl_models.WorkScheduleModel
        fields = (
            'id',
            'profile',
            'work_days',
            'start_hour',
            'end_hour',
            'break_exist',
            'break_start',
            'break_end',
            'work_hours',
        )


class ExceptionListSerializer(BaseCatalogListSerializer):
    class Meta(BaseCatalogListSerializer.Meta):
        model = wl_models.ExceptionModel
        fields = (
            'id',
            'profile',
            'exception_type',
            'start_date',
            'end_date',
            'is_repeatable',
            'repeat_frequency',
            'repeat_end',
            'start_hour',
            'end_hour',
        )


class ExceptionDatesListSerializer(BaseCatalogListSerializer):
    class Meta(BaseCatalogListSerializer.Meta):
        model = wl_models.ExceptionDatesModel
        fields = (
            'start_date',
            'end_date',
        )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        exception = instance.exception
        rep['parent_id'] = exception.id
        rep['name'] = exception.name
        rep['profile'] = exception.profile.id
        rep['exception_type'] = exception.exception_type.alias
        rep['is_repeatable'] = exception.is_repeatable
        rep['repeat_frequency'] = exception.repeat_frequency
        rep['start_hour'] = exception.start_hour
        rep['end_hour'] = exception.end_hour
        rep['repeat_end'] = exception.repeat_end
        return rep


class ExceptionCUDSerializer(BaseCatalogListSerializer):
    exception_type = serializers.SlugRelatedField(
        slug_field='alias', queryset=wl_models.ExceptionTypeModel.objects.all()
    )
    parent_id = serializers.UUIDField(source='id', required=False)

    class Meta(BaseCatalogListSerializer.Meta):
        model = wl_models.ExceptionModel
        fields = (
            'parent_id',
            'name',
            'profile',
            'exception_type',
            'start_date',
            'end_date',
            'is_repeatable',
            'repeat_frequency',
            'repeat_end',
            'start_hour',
            'end_hour',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        print('=-=-=', request)
        if request and request.method == 'POST':
            errors = {}
            required_fields = (
                'profile',
                'name',
                'exception_type',
                'start_date',
                'end_date',
            )
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'Is required.'
            if attrs.get('is_repeatable'):
                if not attrs.get('repeat_frequency'):
                    errors['repeat_frequency'] = 'Is required for repeatable.'
                if not attrs.get('repeat_end'):
                    errors['repeat_end'] = 'Is required for repeatable.'
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = t_models.TaskModel
        fields = (
            'id',
            'name',
            'dead_line',
            'date_start_plan',
        )


class OverloadSerializer(serializers.Serializer):
    date = serializers.DateField()
    overload = serializers.BooleanField()


class MembersSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    checked = serializers.BooleanField()
    color = serializers.CharField()
    overload_days = serializers.SerializerMethodField()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['full_name'] = instance.user.full_name
        rep['color'] = instance.schedule.color
        return rep

    def get_overload_days(self, obj):
        overload = wl_models.WorkLoadModel.objects.filter(
            profile=obj, percents__gt=100.0
        )
        request = self.context.get('request')
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        if start:
            overload = overload.filter(date__gte=parse_date(start))
        if end:
            overload = overload.filter(date__lte=parse_date(end))
        if (start and end) is not None:
            overload = overload.filter(
                date__gte=parse_date(start), date__lte=parse_date(end)
            )
        return OverloadSerializer(overload, many=True).data


class WorkHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = wl_models.WorkScheduleModel
        fields = (
            'start_hour',
            'end_hour',
            'work_hours'
        )


class WorkLoadSerializer(serializers.ModelSerializer):
    tasks = serializers.ListSerializer(child=TaskSerializer())
    total_duration = serializers.ReadOnlyField()
    percents = serializers.ReadOnlyField()
    overload = serializers.ReadOnlyField()

    class Meta:
        model = wl_models.WorkLoadModel
        fields = (
            'id',
            'date',
            'profile',
            'tasks',
            'total_duration',
            'percents',
            'overload',
        )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['hours'] = WorkHoursSerializer(instance.profile.schedule).data
        rep['color'] = instance.profile.schedule.color
        return rep


class TaskDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = wl_models.TaskDurationModel
        fields = (
            'id',
            'task',
            'is_distributed',
            'durations'
        )
