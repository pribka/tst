from django.core.exceptions import ValidationError, ObjectDoesNotExist

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from . import models


class SLAMixin(serializers.Serializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            contractor_id = request.query_params.get('contractor')
            if contractor_id:
                sla_rel = instance.sla_rels.filter(sla__contractor_id=contractor_id).order_by('created_at').first()
                if sla_rel:
                    data['sla'] = SLAListSerializer(sla_rel.sla).data
                else:
                    data['sla'] = None
        return data


# class SLACreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.SLAModel
#         fields = (
#             'id',
#             'related_object',
#             'organization',
#             'first_reaction_time',
#             'solve_time',
#         )
#
#     def validate(self, attrs):
#         # TODO добавить проверку related_object и organization на права создания sla
#         return attrs
#
#
# class SLAUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.SLAModel
#         fields = (
#             'id',
#             'first_reaction_time',
#             'solve_time',
#         )
#
#
class SLADetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SLAModel
        fields = (
            'id',
            'level',
            'name',
            'color',
            'contractor',
            'first_reaction_time',
            'solve_time',
        )


class SLAListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SLAModel
        fields = (
            'id',
            'level',
            'color',
            'name',
            'first_reaction_time',
            'solve_time',
        )


class SLAValueSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SLAValueSourceModel
        fields = (
            'id',
            'description',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sla = instance.sla
        sla_data = SLAListSerializer(sla).data
        sla_data['first_reaction_time'] = instance.first_reaction_time
        sla_data['solve_time'] = instance.solve_time
        data['sla'] = sla_data
        related_object = instance.related_object
        if related_object:
            original_obj = related_object.original_object
            serializer = original_obj.get_serializer_class(action='list')
            data['related_object'] = serializer(original_obj).data
        return data


class SLAValueSerializer(serializers.ModelSerializer):
    sla = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = models.SLAValueModel
        fields = (
            'sla',
            'sources',
        )

    def get_sla(self, instance):
        sla = instance.sla
        sla_data = SLAListSerializer(sla).data
        sla_data['first_reaction_time'] = instance.first_reaction_time
        sla_data['solve_time'] = instance.solve_time
        return sla_data

    def get_sources(self, instance):
        data = SLAValueSourceSerializer(instance.value_sources.all().order_by('created_at'), many=True).data
        return data


class AppSLAValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SLAValueModel
        fields = (
            'id'
        )

    def to_representation(self, instance):
        sla = instance.sla
        data = SLAListSerializer(sla).data
        data['first_reaction_time'] = instance.first_reaction_time
        data['solve_time'] = instance.solve_time
        return data


class SLARelatedObjectSerializer(serializers.ModelSerializer):
    sla = SLAListSerializer()
    related_object = serializers.SerializerMethodField()

    class Meta:
        model = models.SLARelatedObjectModel
        fields = (
            'sla',
            'related_object',
        )

    def get_related_object(self, instance):
        related_object = instance.related_object.original_object
        rel_serializer = related_object.get_serializer_class(action='list')
        data = rel_serializer(related_object).data
        data['obj_type'] = related_object.get_label()
        return data
