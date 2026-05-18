from django.core.exceptions import ObjectDoesNotExist
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bpms.bpms_common.serializers import AppUserSerializer
from bpms.tasks.models import TaskStatusModel
from bpms.tasks.serializers import TaskStatusModelSerializer
from common.current_profile.middleware import get_current_authenticated_profile

from . import models, notifications, utils


class Configuration1cSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Configuration1cModel
        fields = (
            'id',
            'name',
        )


class TicketTypeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TicketTypeOptionModel
        fields = (
            'id',
            'code',
            'name',
        )


class Tariff1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tariff1CModel
        fields = (
            'id',
            'name',
            'disk_space',
            'cpu_cores',
            'ram',
            'subscribers',
            'software',
            'price',
            'name',
            'additional_user_price',
        )


class TicketDetailSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    tarif = Tariff1CSerializer()
    config_1c = Configuration1cSerializer()
    connection_option = TicketTypeOptionSerializer()
    author = AppUserSerializer()
    processed_by = AppUserSerializer()

    class Meta:
        model = models.TicketModel
        fields = (
            'id',
            'ticket_type',
            'connection_option',
            'author',
            'config_1c',
            'tarif',
            'phone',
            'email',
            'company',
            'activity_type',
            'description',
            'user_count',
            'start_date',
            'end_date',
            'status',
            'rental_period',
            'processed_by',
        )

    def get_status(self, instance):
        user = get_current_authenticated_profile()
        if user.check_profile_types({"administrator_1c"}):
            return TaskStatusModelSerializer(instance.admin_status).data
        else:
            return TaskStatusModelSerializer(instance.user_status).data


class CreateTicketSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = models.TicketModel
        fields = (
            'id',
            'ticket_type',
            'connection_option',
            'config_1c',
            'tarif',
            'phone',
            'email',
            'company',
            'activity_type',
            'description',
            'user_count',
            'rental_period',
        )

    def create(self, validated_data):
        ticket_type = validated_data.get('ticket_type')
        try:
            ticket_is_under_review = TaskStatusModel.objects.get(
                is_active=True,
                code='ticket_is_under_review'
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                'Проверьте что статус ticket_is_under_review существует'
            )
        try:
            ticket_type_obj = models.TicketTypeModel.objects.get(
                is_active=True,
                code='base_1c'
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                'Проверьте что тип обращения base_1c существует'
            )
        ticket = models.TicketModel.objects.create(
            **validated_data
        )
        if ticket_type is None:
            ticket.ticket_type = ticket_type_obj
        ticket.admin_status = ticket_is_under_review
        ticket.user_status = ticket_is_under_review
        ticket.save()
        async_task(
            notifications.notify_about_new_base_1c_ticket,
            ticket,
            ticket.author
        )
        if ticket.email:
            async_task(
                utils.send_new_ticket_confirmation_email,
                ticket
            )
        return ticket

    def to_representation(self, instance):
        request = self.context['request']
        return TicketDetailSerializer(
            instance,
            context={
                'request': request
            }
        ).data


class UpdateTicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TicketModel
        fields = (
            'id',
            'ticket_type',
            'connection_option',
            'config_1c',
            'tarif',
            'phone',
            'email',
            'company',
            'activity_type',
            'description',
            'user_count',
            'rental_period',
        )

    def update(self, instance, validated_data):
        ticket = super().update(instance, validated_data)
        return ticket

    def to_representation(self, instance):
        request = self.context['request']
        return TicketDetailSerializer(
            instance,
            context={
                'request': request
            }
        ).data


class TicketListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    config_1c = Configuration1cSerializer()
    author = AppUserSerializer()
    connection_option = TicketTypeOptionSerializer()
    processed_by = AppUserSerializer()

    class Meta:
        model = models.TicketModel
        fields = (
            'id',
            'config_1c',
            'user_count',
            'status',
            'author',
            'connection_option',
            'processed_by',
        )

    def get_status(self, instance):
        if self.context.get('is_administrator_1c'):
            return TaskStatusModelSerializer(instance.admin_status).data
        else:
            return TaskStatusModelSerializer(instance.user_status).data


class NotificationTicketDetailSerializer(serializers.ModelSerializer):
    connection_option = serializers.SerializerMethodField()
    tarif = serializers.SerializerMethodField()

    def get_connection_option(self, instance):
        if instance.connection_option:
            return instance.connection_option.name
        else:
            return ''

    def get_tarif(self, instance):
        if instance.tarif:
            return instance.tarif.name
        else:
            return ''

    class Meta:
        model = models.TicketModel
        fields = (
            'id',
            'connection_option',
            'tarif',
        )
