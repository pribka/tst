from rest_framework import serializers, exceptions as drf_exceptions

from . import models


class ColorNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ColorNoteModel
        fields = (
            'id',
            'color',
            'oColor',
        )


class NoteModelListSerializer(serializers.ModelSerializer):
    color = ColorNoteSerializer()

    class Meta:
        model = models.NoteModel
        fields = (
            'id',
            'title',
            'content',
            'color',
        )


class NoteModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NoteModel
        fields = (
            'id',
            'title',
            'content',
            'color',
            'related_object',
        )

    def validate_related_object(self, related_object):
        if related_object:
            original_object = related_object.original_object
            request = self.context.get('request')
            try:
                result = original_object.get_note_permission(request)
            except AttributeError:
                result = original_object.get_update_permission(request)
            if not result:
                raise drf_exceptions.PermissionDenied()
        return related_object

    def to_representation(self, instance):
        return NoteModelListSerializer(instance, context=self.context).data


class NoteModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NoteModel
        fields = (
            'id',
            'title',
            'content',
            'color',
        )

    def to_representation(self, instance):
        return NoteModelListSerializer(instance, context=self.context).data
