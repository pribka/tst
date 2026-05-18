import datetime
from bs4 import BeautifulSoup

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Avg, Q

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, exceptions as drf_exceptions

from django_q.tasks import async_task

from common.models import File
from common.catalogs.serializers import (
    ContractorModelShortSerializer,
    MeasureUnitListSerializer,
    AppNomenclatureSerializer
)
from common.catalogs.models import ContractorModel, ExternalCustomerModel, ContractorProfileModel

from common.accounting_catalogs.serializers import BudgetProgramAdministratorModelSerializer
from common.utils import get_serialized_attachments
from common.serializers import CachedBaseModelSerializer, CachedBaseCatalogSerializer, SelectListSerializer

from users.models import ProfileModel
from users.serializers import CachedAppUserPreviewSerializer
from users.utils import get_tree_departments_related_organizations, get_ancestor_departments_related_organizations

from bpms.voting.serializers import RatingReadSerializer
from bpms.chat.serializers import ChatListShortSerializer

from contractor_permissions.utils import check_contractor_permission, contractors_where_user_has_permission
from customer_contracts.models import CustomerContractProjectModel

from tags.serializers import TagModelListSerializer

from bkz3.settings import BACKEND_URL

from sla.models import SLAModel, SLARelatedObjectModel
from sla.serializers import SLAMixin, SLAListSerializer, AppSLAValueSerializer, SLAValueSerializer

from . import models, utils, notifications


class VacationDateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VacationDateModel
        fields = (
            'start_date',
            'end_date',
        )


class CustomerCardStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class CustomerSpecialistListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')
    vacation_dates = VacationDateListSerializer(many=True)

    class Meta:
        model = models.CustomerSupportSpecialistModel
        fields = (
            'id',
            'user',
            'is_reserve',
            'created_at',
            'updated_at',
            'comment',
            'start_date',
            'end_date',
            'vacation_dates',
            'duration_plan',
            'accepts_calls',
            'call_priority',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        action_info = {
            'can_move_up': bool(getattr(instance, 'can_move_up', False)),
            'can_move_down': bool(getattr(instance, 'can_move_down', False)),
        }
        request = self.context.get('request')
        if request:
            display = request.query_params.get('display', '')
            if display == 'user':
                data = data['user']
                data['is_reserve'] = instance.is_reserve
        try:
            duration_fact_sec = instance.duration_fact
        except AttributeError:
            duration_fact_sec = instance.instance_duration_fact
        if duration_fact_sec is None:
            duration_fact_sec = 0
        data['duration_fact'] = duration_fact_sec
        data['action_info'] = action_info
        return data


class CustomerCardStatusUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CustomerCardModel
        fields = (
            'id',
            'status',
        )


class CustomerCardForTicketSerializer(serializers.ModelSerializer):
    customer = ContractorModelShortSerializer()
    tags = serializers.SerializerMethodField()
    org_admin = ContractorModelShortSerializer()
    status = CustomerCardStatusSerializer()

    class Meta:
        model = models.CustomerCardModel
        fields = (
            # Поля контрагента
            'name',
            'full_name',
            'inn',
            'legal_address',
            # / Поля контрагента
            'id',
            'status',
            'customer',
            'created_at',
            'tags',
            'org_admin',
            'unknown',
        )

    def get_tags(self, instance):
        tags = instance.object_tags.all().order_by('name')
        if tags.exists():
            data = TagModelListSerializer(
                tags,
                many=True,
                context={'related_object': instance.pk}
            ).data
        else:
            data = []
        return data


class CustomerSpecialistShortSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')

    class Meta:
        model = models.CustomerSupportSpecialistModel
        fields = (
            'id',
            'is_reserve',
            'user',
        )


class CustomerCardAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardAdminModel
        fields = (
            'id',
            'name',
            'bin',
        )


class CustomerCardModelListSerializer(serializers.ModelSerializer):
    admins = CustomerCardAdminListSerializer(many=True)
    customer = ContractorModelShortSerializer()
    status = CachedBaseCatalogSerializer(
        serializer_class=CustomerCardStatusSerializer,
        model=models.CustomerCardStatusModel,
        source='status_id',
    )

    # tags = serializers.SerializerMethodField()

    class Meta:
        model = models.CustomerCardModel
        fields = (
            # Поля контрагента
            'name',
            'full_name',
            'inn',
            'legal_address',
            # # / Поля контрагента
            'id',
            'status',
            'customer',
            'created_at',
            # 'tags',
            'unknown',
            'admins',
        )

    # def get_tags(self, instance):
    #     tags = instance.object_tags.all()
    #     if tags.exists():
    #         data = TagModelListSerializer(
    #             tags,
    #             many=True,
    #             context={'related_object': instance.pk}
    #         ).data
    #     else:
    #         data = []
    #     return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'pref_actual_specialists'):
            actual_specialists = instance.pref_actual_specialists
        else:
            actual_specialists = instance.actual_specialists.all()
        data['actual_specialists'] = [
            {
                "id": _.pk,
                "is_reserve": _.is_reserve,
                "user": CachedAppUserPreviewSerializer(_.user_id).data
            }
            for _ in actual_specialists
        ]
        main_contact_person = instance.main_contact_person
        if main_contact_person:
            data['main_contact_person'] = MainContactPersonSerializer(main_contact_person).data
        else:
            data['main_contact_person'] = None
        object_tag_through = instance.object_tag_through.all()
        data['tags'] = [{"id": _.tag_id, "name": _.tag.name, "color": _.color} for _ in object_tag_through]
        return data


class CustomerCardForContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardModel
        fields = (
            'id',
            'name',
            'org_admin',
            'unknown',
        )


class ContactPersonPostSerializer(serializers.ModelSerializer, SLAMixin):
    class Meta:
        model = models.ContactPersonPostModel
        fields = (
            'id',
            'name',
            'code',
            'contractor',
        )


class MainContactPersonSerializer(serializers.ModelSerializer):
    post_inst = ContactPersonPostSerializer()

    class Meta:
        model = models.ContactPersonModel

        fields = (
            'id',
            'name',
            'post_inst',
        )


class ContactPersonPostCreateSerializer(serializers.ModelSerializer):
    sla = serializers.PrimaryKeyRelatedField(
        queryset=SLAModel.objects.filter(is_default=False),
        required=False,
        allow_empty=True,
        allow_null=True
    )

    class Meta:
        model = models.ContactPersonPostModel
        fields = (
            'id',
            'name',
            'contractor',
            'sla'
        )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('Contractor is required')
        user = self.context.get('request').user.profile
        contractors_id = utils.get_help_desk_admin_contractors(user)
        from users.utils import get_ancestor_departments_related_organizations
        contractors_id = get_ancestor_departments_related_organizations(contractors_id, include_self=True)
        if contractor.pk not in contractors_id:
            raise drf_exceptions.ValidationError('Invalid contractor')
        return attrs

    def create(self, validated_data):
        sla = validated_data.pop('sla', None)
        instance = super().create(validated_data)
        if sla:
            SLARelatedObjectModel.objects.create(related_object=instance, sla=sla)
        return instance


class ContactPersonPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContactPersonPostModel
        fields = (
            'id',
            'name',
        )


class ContactPersonPostDetailSerializer(serializers.ModelSerializer, SLAMixin):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = models.ContactPersonPostModel
        fields = (
            'id',
            'name',
            'code',
            'contractor',
        )


class ContactPersonModelListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')
    customer_card = CustomerCardForContactSerializer()
    post_inst = ContactPersonPostSerializer()

    class Meta:
        model = models.ContactPersonModel
        fields = (
            'id',
            'user',
            'name',
            # 'post',
            'post_inst',
            'phone',
            'telegram',
            'email',
            'letter_sent',
            'letter_sent_date',
            'unknown',
            'customer_card',
            'comment',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor_id = instance.customer_card.org_admin_id
        sla_rel = instance.sla_rels.filter(sla__contractor_id=contractor_id).order_by('created_at').first()
        sla_data = None
        if sla_rel:
            sla_data = SLAListSerializer(sla_rel.sla).data
        else:
            post_inst = instance.post_inst
            if post_inst:
                sla_rel = post_inst.sla_rels.filter(sla__contractor_id=contractor_id).order_by('created_at').first()
                if sla_rel:
                    sla_data = SLAListSerializer(sla_rel.sla).data
                    sla_data['from'] = 'Должность'
        data['sla'] = sla_data

        # Проверка прав для скрытия полей
        can_update_customer_card = self.context.get('can_update_customer_card')
        if can_update_customer_card is None:
            request = self.context.get('request')
            if request and hasattr(instance, 'customer_card'):
                can_update_customer_card = instance.customer_card.get_update_permission(request)
            else:
                can_update_customer_card = False

        if not can_update_customer_card:
            hidden_text = _("Скрыто")
            data['email'] = hidden_text
            data['telegram'] = hidden_text
            data['phone'] = hidden_text
            # data['post'] = hidden_text
            data['post_inst'] = None

        if hasattr(instance, 'is_main'):
            data['is_main'] = instance.is_main
        else:
            data['is_main'] = instance.pk == instance.customer_card.main_contact_person_id
        return data


class ContactPersonModelShortSerializer(serializers.ModelSerializer):
    # user = CachedAppUserPreviewSerializer(source='user_id')
    # post_inst = ContactPersonPostSerializer()

    class Meta:
        model = models.ContactPersonModel
        fields = (
            'id',
            # 'user',
            'name',
            # 'post',
            # 'post_inst',
            # 'phone',
            # 'telegram',
            # 'email',
            # 'letter_sent',
            # 'letter_sent_date',
            'unknown',
            # 'customer_card',
            # 'comment',
        )


class ContactPersonModelCreateSerializer(serializers.ModelSerializer):
    sla = serializers.PrimaryKeyRelatedField(
        queryset=SLAModel.objects.filter(is_default=False),
        required=False,
        allow_empty=True,
        allow_null=True
    )
    is_main = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.ContactPersonModel
        fields = (
            'id',
            'name',
            'is_main',
            # 'post',
            'post_inst',
            'phone',
            'telegram',
            'email',
            'customer_card',
            'comment',
            'sla',
        )

    def create(self, validated_data):
        sla = validated_data.pop('sla', None)
        is_main = validated_data.pop('is_main', False)
        with transaction.atomic():
            instance = super().create(validated_data)
            if is_main:
                customer_card = instance.customer_card
                customer_card.main_contact_person = instance
                customer_card.save()
            if sla:
                SLARelatedObjectModel.objects.create(related_object=instance, sla=sla)
        return instance


class ContactPersonModelUpdateSerializer(serializers.ModelSerializer):
    is_main = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.ContactPersonModel
        fields = (
            'id',
            'is_main',
            'name',
            'phone',
            'telegram',
            'email',
            # 'post',
            'post_inst',
            'comment',
        )

    def update(self, instance, validated_data):
        is_main = validated_data.pop('is_main', None)
        instance = super().update(instance, validated_data)
        customer_card = instance.customer_card
        if is_main is not None:
            if is_main is True:
                customer_card.main_contact_person = instance
                customer_card.save()
            elif customer_card.main_contact_person_id == instance.pk:
                customer_card.main_contact_person = None
                customer_card.save()
        return instance


class CustomerCardAdminCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardAdminModel
        fields = (
            'id',
            'name',
            'bin',
            'org_admin',
        )

    def validate_org_admin(self, org_admin):
        if not org_admin:
            raise drf_exceptions.ValidationError('Org_admin is required')
        user = self.context.get('request').user.profile
        check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin', 'help_desk_manager'), None)
        return org_admin


class CustomerCardAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardAdminModel
        fields = (
            'id',
            'name',
        )


class CustomerCardModelCreateSerializer(serializers.ModelSerializer):
    contact_persons = ContactPersonModelCreateSerializer(many=True, allow_null=True, required=False)
    admins = serializers.PrimaryKeyRelatedField(
        queryset=models.CustomerCardAdminModel.objects.all(),
        allow_null=True,
        allow_empty=True,
        required=False,
        many=True,
    )
    lead = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        allow_empty=True,
        queryset=models.HelpDeskTicketModel.objects.filter(ticket_type_id='lead', is_active=True)
    )

    class Meta:
        model = models.CustomerCardModel
        fields = (
            # Поля контрагента
            'name',
            'full_name',
            'inn',
            'legal_address',
            # / Поля контрагента
            'id',
            'description',
            'org_admin',
            'admins',
            'created_at',
            'description',
            'contact_persons',
            'lead',
        )

    def validate_org_admin(self, org_admin):
        if not org_admin:
            raise drf_exceptions.ValidationError('Org_admin is required')
        user = self.context.get('request').user.profile
        try:
            check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            try:
                check_contractor_permission(user.pk, org_admin.pk, ('help_desk_manager',), None)
            except drf_exceptions.PermissionDenied:
                allowed_contractors = contractors_where_user_has_permission(
                    user.pk,
                    ('create_workgroup', 'admin',),
                    None
                )
                ancestors = get_ancestor_departments_related_organizations(allowed_contractors, include_self=True)
                if org_admin.pk not in ancestors:
                    raise drf_exceptions.PermissionDenied()
            else:
                self.context['create_specialist'] = user

        return org_admin

    def validate(self, attrs):
        admins = attrs.get('admins')
        org_admin = attrs.get('org_admin')
        if admins:
            for admin in admins:
                if not admin.org_admin == org_admin:
                    raise drf_exceptions.ValidationError(f'Invalid admin {admin.bin}')
        return attrs

    def create(self, validated_data):
        contact_persons = validated_data.pop('contact_persons', None)
        lead = validated_data.pop('lead', None)
        create_specialist = self.context.get('create_specialist', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            if lead:
                lead.customer_card = instance
                lead.save(update_fields=('customer_card',))
                lead_contact_person = lead.contact_person
                if lead_contact_person:
                    lead_contact_person.customer_card = instance
                    lead_contact_person.unknown = False
                    lead_contact_person.save(update_fields=('customer_card', 'unknown'))
            if contact_persons:
                for each in contact_persons:
                    each['customer_card'] = instance.pk
                    serializer = ContactPersonModelCreateSerializer(data=each)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
            if create_specialist:
                models.CustomerSupportSpecialistModel.objects.create(
                    customer_card=instance,
                    user=create_specialist,
                )
        return instance

    def to_representation(self, instance):
        return CustomerCardModelDetailSerializer(instance, context=self.context).data


class CustomerCardCreateFrom1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardModel
        fields = (
            'id',
            'external_id',
            'name',
            'full_name',
            'inn',
            'legal_address',
            'description',
            'org_admin',
        )


class CustomerCardModelUpdateSerializer(serializers.ModelSerializer):
    admins = serializers.PrimaryKeyRelatedField(
        queryset=models.CustomerCardAdminModel.objects.all(),
        allow_null=True,
        allow_empty=True,
        required=False,
        many=True,
    )

    class Meta:
        model = models.CustomerCardModel
        fields = (
            # Поля контрагента
            'name',
            'full_name',
            'inn',
            'legal_address',
            # / Поля контрагента
            'id',
            'description',
            'admins',
        )

    def validate(self, attrs):
        admins = attrs.get('admins')
        org_admin = self.instance.org_admin
        if admins:
            for admin in admins:
                if not admin.org_admin == org_admin:
                    raise drf_exceptions.ValidationError(f'Invalid admin {admin.bin}')
        return attrs


class CustomerCardModelDetailSerializer(serializers.ModelSerializer):
    customer = ContractorModelShortSerializer()
    org_admin = ContractorModelShortSerializer()
    actual_specialists = CustomerSpecialistListSerializer(many=True)
    status = CustomerCardStatusSerializer()
    admins = CustomerCardAdminListSerializer(many=True)

    class Meta:
        model = models.CustomerCardModel
        fields = (
            # Поля контрагента
            'name',
            'full_name',
            'inn',
            'legal_address',
            # / Поля контрагента
            'id',
            'status',
            'customer',
            'created_at',
            'description',
            'org_admin',
            'actual_specialists',
            'admins',
            'unknown',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tabs'] = [
            {
                'code': "info",
                'name': "Основная информация"
            },
            {
                'code': "specialists",
                'name': "Специалисты поддержки"
            },
            {
                'code': "history",
                'name': "История обращений"
            },
            {
                'code': "knowledge-base",
                'name': "База знаний"
            },
            {
                'code': "notes",
                'name': "Заметки"
            },
            {
                'code': "files",
                'name': "Файлы"
            }
        ]
        main_contact_person = instance.main_contact_person
        if main_contact_person:
            data['main_contact_person'] = MainContactPersonSerializer(main_contact_person).data
        else:
            data['main_contact_person'] = None
        return data


class VacationDateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VacationDateModel
        fields = (
            'specialist',
            'start_date',
            'end_date',
        )


class CustomerSpecialistCreateSerializer(serializers.ModelSerializer):
    duration_plan = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=0,
    )

    class Meta:
        model = models.CustomerSupportSpecialistModel
        fields = (
            'id',
            'user',
            'customer_card',
            'start_date',
            'end_date',
            'comment',
            'duration_plan',
            'is_reserve',
            'accepts_calls',
            'call_priority',
        )
        read_only_fields = (
            'call_priority',
        )

    def validate_customer_card(self, customer_card):
        request = self.context.get('request')
        if not customer_card.get_specialist_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        return customer_card

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            vacation_dates = self.initial_data.get('vacation_dates')
            if vacation_dates:
                for vacation_date in vacation_dates:
                    vacation_date['specialist'] = instance.pk
                    vacation_serializer = VacationDateCreateSerializer(data=vacation_date,)
                    vacation_serializer.is_valid(raise_exception=True)
                    vacation_serializer.save()
        return instance

    def validate(self, attrs):
        customer_card = attrs.get('customer_card')
        user = attrs.get('user')
        org_admin_id = str(customer_card.org_admin_id)
        try:
            check_contractor_permission(user.pk, org_admin_id, ('help_desk_manager', 'help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            raise drf_exceptions.ValidationError(
                f'Пользователь {user.full_name}  не может быть специалистом тех. поддержки'
            )
        duration_plan = attrs.get('duration_plan')
        if not duration_plan:
            attrs['duration_plan'] = 0
        return attrs
        return attrs


class CustomerSpecialistUpdateSerializer(serializers.ModelSerializer):

    duration_plan = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=0,
    )

    class Meta:
        model = models.CustomerSupportSpecialistModel
        fields = (
            'id',
            'user',
            'is_reserve',
            'start_date',
            'end_date',
            'comment',
            'duration_plan',
            'accepts_calls',
            'call_priority',
        )
        read_only_fields = (
            'call_priority',
        )

    def validate(self, attrs):
        instance = self.instance
        org_admin_id = str(instance.customer_card.org_admin_id)
        user = attrs.get('user')
        if user and not user == instance.user:
            try:
                check_contractor_permission(user.pk, org_admin_id, ('help_desk_manager', 'help_desk_admin',), None)
            except drf_exceptions.PermissionDenied:
                raise drf_exceptions.ValidationError(
                    f'Пользователь {user.full_name}  не может быть специалистом тех. поддержки'
                )
        duration_plan = attrs.get('duration_plan')
        if not duration_plan:
            attrs['duration_plan'] = 0
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            vacation_dates = self.initial_data.get('vacation_dates')
            instance = super().update(instance, validated_data)
            if vacation_dates is not None:
                instance.vacation_dates.all().delete()
                for vacation_date in vacation_dates:
                    vacation_date['specialist'] = instance.pk
                    vacation_serializer = VacationDateCreateSerializer(data=vacation_date,)
                    vacation_serializer.is_valid(raise_exception=True)
                    vacation_serializer.save()
        return instance


class HelpDeskConfigModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskConfigModel
        fields = (
            'id',
            'telegram_user',
            'telegram_token',
            'email_username',
            'imap_server',
            'email_pass',
            'created_at',
            'updated_at',
        )


class HelpDeskChannelModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.HelpDeskChannelModel
        fields = (
            'id',
            'name',
            'code',
            'icon',
        )


class ContactPersonMessageNotifySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'short_text',
        )


class ContactPersonMessageReplySerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'author',
            'text',
            'contact_person',
            'channel',
            'message_date',
            'is_help_desk',
        )


class ContactPersonMessageListSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()
    reply = ContactPersonMessageReplySerializer()

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'author',
            'text',
            'contact_person',
            'channel',
            'created_at',
            'message_date',
            'is_help_desk',
            'reply',
            'attachments',
            'created_at',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        attachments = get_serialized_attachments(instance)
        data['attachments'] = attachments
        try:
            data['is_new'] = instance.is_new
        except AttributeError:
            pass
        return data


class ContactPersonMessageCreateSerializer(serializers.ModelSerializer):

    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    ticket = serializers.PrimaryKeyRelatedField(
        required=True,
        allow_null=False,
        queryset=models.HelpDeskTicketModel.objects.filter(is_active=True)
    )
    text = serializers.CharField(allow_blank=True,)

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'text',
            'contact_person',
            'channel',
            'source_message',
            'is_help_desk',
            'reply',
            'attachments',
            'ticket',
        )

    def validate_ticket(self, ticket):
        request = self.context.get('request')
        if not ticket.get_create_message_permission(request):
            raise drf_exceptions.ValidationError('Вы не можете отправлять сообщения в этом обращении')
        return ticket

    def validate_contact_person(self, contact_person):
        org_admin_id = contact_person.customer_card.org_admin.pk
        user_id = self.context.get('request').user.profile.pk
        check_contractor_permission(user_id, org_admin_id, ('help_desk_manager', 'help_desk_admin',), None)
        return contact_person

    def validate(self, attrs):
        text = attrs.get('text')
        attachments = attrs.get('attachments')
        if not text and not attachments:
            raise drf_exceptions.ValidationError('text is required')
        return attrs

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        ticket = validated_data.pop('ticket', None)

        with transaction.atomic():
            instance = models.ContactPersonMessageModel()
            for key, value in validated_data.items():
                setattr(instance, key, value)
            if instance.channel.code == 'email':
                try:
                    config = instance.contact_person.customer_card.org_admin.help_desk_config
                except ObjectDoesNotExist:
                    raise drf_exceptions.ValidationError('Отсутствует настройка подключения к почтовому серверу')
                instance.message_id = utils.get_message_id(config)
                email_subject = getattr(instance.reply, 'email_subject', '')
                if not email_subject:
                    last_message = ticket.messages.filter(is_active=True).order_by('-created_at').first()
                    email_subject = last_message.email_subject
                    if not email_subject:
                        email_subject = f"Обращение #{ticket.number}"
                if email_subject.lower().startswith('re: '):
                    instance.email_subject = email_subject
                else:
                    instance.email_subject = f"Re: {email_subject}"
            instance.save(ticket=ticket)
            if attachments:
                instance.attachments.set(attachments)
        instance.cluts()
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_new_ticket_specialist_message, str(ticket.pk), str(instance.pk)
            )
        )
        return instance

    def to_representation(self, instance):
        return ContactPersonMessageListSerializer(instance, context=self.context).data


class ContactPersonMessageClientReplySerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'author',
            'text',
            'channel',
            'message_date',
            'is_help_desk',
        )


class ContactPersonMessageClientListSerializer(serializers.ModelSerializer):
    reply = ContactPersonMessageClientReplySerializer()
    attachments = serializers.SerializerMethodField()
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'author',
            'attachments',
            'text',
            'reply',
            'is_help_desk',
            'channel',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class ContactPersonMessageClientCreateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(allow_blank=True,)

    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    org_admin = serializers.PrimaryKeyRelatedField(
        required=True,
        allow_null=False,
        allow_empty=False,
        queryset=ContractorModel.objects.filter(is_active=True)
    )
    ticket = serializers.PrimaryKeyRelatedField(
        required=True,
        allow_null=False,
        queryset=models.HelpDeskTicketModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ContactPersonMessageModel
        fields = (
            'id',
            'text',
            'org_admin',
            'reply',
            'attachments',
            'ticket',
        )

    def validate(self, attrs):
        text = attrs.get('text')
        attachments = attrs.get('attachments')
        if not text and not attachments:
            raise drf_exceptions.ValidationError('text is required')
        return attrs

    def validate_ticket(self, ticket):
        from .utils import get_create_message_for_client_permission
        if not get_create_message_for_client_permission(ticket):
            raise drf_exceptions.ValidationError('Вы не можете отправлять сообщения в этом обращении')
        return ticket

    def create(self, validated_data):
        ticket = validated_data.pop('ticket', None)
        org_admin = validated_data.pop('org_admin', None)
        user = self.context.get('request').user.profile
        contact_person = models.ContactPersonModel.objects.filter(
            customer_card__org_admin=org_admin,
            user=user,
            is_active=True,
            customer_card__is_active=True,
            customer_card__org_admin__is_active=True,
        ).order_by('-created_at').first()
        if not contact_person:
            raise drf_exceptions.ValidationError('Организация техподдержки не найдена')
        attachments = validated_data.pop('attachments', None)
        with transaction.atomic():
            instance = models.ContactPersonMessageModel()
            instance.contact_person = contact_person
            instance.channel_id = ticket.channel_id
            instance.ticket = ticket
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.save(ticket=ticket)
            if attachments:
                instance.attachments.set(attachments)
        instance.cluts()
        return instance

    def to_representation(self, instance):
        return ContactPersonMessageListSerializer(instance, context=self.context).data


class HelpDeskTicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class HelpDeskTicketCategorySerializer(serializers.ModelSerializer, SLAMixin):
    class Meta:
        model = models.HelpDeskTicketCategoryModel
        fields = (
            'id',
            'name',
            'code',
            'contractor'
        )


class TicketCategoryDetailSerializer(serializers.ModelSerializer, SLAMixin):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = models.HelpDeskTicketCategoryModel
        fields = (
            'id',
            'name',
            'code',
            'contractor',
        )


class TicketCategoryCreateSerializer(serializers.ModelSerializer):
    sla = serializers.PrimaryKeyRelatedField(
        queryset=SLAModel.objects.filter(is_default=False),
        required=False,
        allow_empty=True,
        allow_null=True
    )

    class Meta:
        model = models.HelpDeskTicketCategoryModel
        fields = (
            'id',
            'name',
            'contractor',
            'sla'
        )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('Contractor is required')
        user = self.context.get('request').user.profile
        if not utils.check_ticket_category_create_permission(user, contractor.pk):
            raise drf_exceptions.ValidationError('Invalid contractor')
        return attrs

    def create(self, validated_data):
        sla = validated_data.pop('sla', None)
        instance = super().create(validated_data)
        if sla:
            SLARelatedObjectModel.objects.create(related_object=instance, sla=sla)
        return instance


class TicketCategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketCategoryModel
        fields = (
            'id',
            'name',
        )


class HelpDeskTicketPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketPriorityModel
        fields = (
            'id',
            'name',
            'code',
        )


class HelpDeskTicketNotifySerializer(serializers.ModelSerializer):
    category = HelpDeskTicketCategorySerializer()
    priority = HelpDeskTicketPrioritySerializer()
    customer_card = CustomerCardModelListSerializer()
    contact_person = ContactPersonModelListSerializer()
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'category',
            'priority',
            'customer_card',
            'contact_person',
            'number',
            'name',
            'specialist',
            'receipt_date',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.contact_person:
            data['contact_person'] = ContactPersonModelListSerializer(
                instance.contact_person,
                context={**self.context, 'can_update_customer_card': True}
            ).data
        data['dead_line'] = timezone.localtime(instance.dead_line).strftime('%d.%m.%Y %H:%M')
        data['created_at'] = timezone.localtime(instance.created_at).strftime('%d.%m.%Y %H:%M')
        data['priority_emoji'] = utils.get_priority_emoji(instance.priority.code)
        try:
            sla_value = instance.sla_value
        except ObjectDoesNotExist:
            data['sla'] = None
        else:
            sla_data = AppSLAValueSerializer(sla_value).data
            sla_color = sla_value.sla.color
            if sla_color:
                sla_color_emoji = utils.status_color_to_emoji(sla_color)
                if sla_color_emoji:
                    sla_data['color_emoji'] = sla_color_emoji
                else:
                    sla_data['color_emoji'] = ''
            first_reaction_time = sla_value.first_reaction_time
            if first_reaction_time:
                sla_data['first_reaction_time_str'] = self.get_sla_duration(first_reaction_time)
                receipt_date = instance.receipt_date
                if receipt_date:
                    in_work_to = receipt_date + datetime.timedelta(seconds=first_reaction_time)
                    sla_data['in_work_to'] = timezone.localtime(in_work_to).strftime('%d.%m.%Y %H:%M')
            solve_time = sla_value.solve_time
            if solve_time:
                sla_data['solve_time_str'] = self.get_sla_duration(solve_time)
            data['sla'] = sla_data
        return data

    def get_sla_duration(self, duration_sec):
        duration_min = duration_sec // 60
        duration_str = f"{duration_min} мин"
        duration_remainder = duration_sec % 60
        if duration_remainder:
            duration_str = duration_str + f" {duration_remainder} сек"
        return duration_str


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class TicketForClientListSerializer(serializers.ModelSerializer):

    status = CachedBaseCatalogSerializer(source='status_id', model=models.HelpDeskTicketStatusModel, serializer_class=HelpDeskTicketStatusSerializer)
    category = CachedBaseModelSerializer(source='category_id', serializer_class=HelpDeskTicketCategorySerializer)
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = CachedBaseCatalogSerializer(source='channel_id', model=models.HelpDeskChannelModel, serializer_class=HelpDeskChannelModelSerializer)
    ticket_type = CachedBaseCatalogSerializer(source='ticket_type_id', model=models.HelpDeskTicketTypeModel, serializer_class=TicketTypeSerializer)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'author',
            'channel',
            'status',
            'status_from_client',
            'category',
            'specialist',
            'dead_line',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
            'created_from_messages',
            'ticket_type',
            'receipt_date',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'avg_rating'):
            data['rating'] = instance.avg_rating
        else:
            data['rating'] = instance.ratings.all().aggregate(avg_rating=Avg('rating'))['avg_rating']
        data['work_log_duration'] = instance.duration
        try:
            contact_person_user = instance.contact_person.user_id
        except AttributeError:
            contact_person_user_data = None
        else:
            contact_person_user_data = CachedAppUserPreviewSerializer(contact_person_user).data
        data['contact_person_user'] = contact_person_user_data
        return data


class TicketForClientDetailSerializer(serializers.ModelSerializer):
    status = HelpDeskTicketStatusSerializer()
    category = HelpDeskTicketCategorySerializer()
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()
    ticket_type = TicketTypeSerializer()
    priority = CachedBaseCatalogSerializer(source='priority_id', model=models.HelpDeskTicketPriorityModel, serializer_class=HelpDeskTicketPrioritySerializer)
    members = CachedAppUserPreviewSerializer(many=True)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'description',
            'author',
            'channel',
            'status',
            'status_from_client',
            'category',
            'specialist',
            'dead_line',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
            'created_from_messages',
            'ticket_type',
            'metadata',
            'priority',
            'members',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        specialist_data = data.get('specialist')
        specialist_is_reserve = None
        if specialist_data and instance.specialist_id and instance.customer_card_id:
            specialist_link = instance.customer_card.actual_specialists.filter(
                user_id=instance.specialist_id
            ).order_by('-created_at').first()
            if specialist_link:
                specialist_is_reserve = specialist_link.is_reserve
        if specialist_data is not None:
            specialist_data['is_reserve'] = specialist_is_reserve
        customer_card = instance.customer_card
        org_admin_data = None
        if customer_card:
            org_admin = customer_card.org_admin
            if org_admin:
                org_admin_data = MyOrgAdminSerializer(org_admin).data
        data['org_admin'] = org_admin_data
        data['work_log_duration'] = instance.duration
        rating = instance.ratings.all().first()
        if rating:
            rating_data = RatingReadSerializer(rating).data
        else:
            rating_data = None
        data['rating'] = rating_data
        try:
            contact_person_user = instance.contact_person.user_id
        except AttributeError:
            contact_person_user_data = None
        else:
            contact_person_user_data = CachedAppUserPreviewSerializer(contact_person_user).data
        data['contact_person_user'] = contact_person_user_data
        return data


class TicketForClientCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=ProfileModel.objects.filter(is_active=True),
        write_only=True,
    )
    org_admin = serializers.PrimaryKeyRelatedField(
        required=True,
        allow_null=False,
        queryset=ContractorModel.objects.filter(is_active=True)
    )
    channel = serializers.SlugRelatedField(
        slug_field='code',
        required=False,
        allow_null=True,
        queryset=models.HelpDeskChannelModel.objects.filter(is_active=True),
    )
    request_callback = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'user',
            'name',
            'description',
            'metadata',
            'org_admin',
            'channel',
            'request_callback',
        )

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        org_admin = validated_data.pop('org_admin', None)
        channel = validated_data.pop('channel', None)
        request_callback = validated_data.pop('request_callback', False)
        if not user:
            user = self.context.get('request').user.profile
        if channel is None:
            channel = models.HelpDeskChannelModel.objects.get(code='internal')

        if not validated_data.get('name'):
            validated_data['name'] = f'Обращение от клиента {user.full_name}'
        contact_person = models.ContactPersonModel.objects.filter(
            is_active=True,
            customer_card__org_admin=org_admin,
            user=user,
        ).order_by('-created_at').first()
        if not contact_person:
            raise drf_exceptions.ValidationError(
                'Контактное лицо не найдено'
            )
        customer_card = contact_person.customer_card
        actual_specialists = customer_card.actual_specialists
        if actual_specialists.count() == 1:
            specialist = actual_specialists.first().user
        else:
            specialist = None
        instance = models.HelpDeskTicketModel.objects.create(
            contact_person=contact_person,
            customer_card=customer_card,
            channel=channel,
            specialist=specialist,
            **validated_data
        )
        instance.set_sla_value()

        if request_callback:
            from bpms.meetings.models import CallModel
            CallModel.objects.create(
                ticket=instance,
                chat=None,
                meeting=None,
                status_id='waiting_callback',
                initiator=user,
                ring_attempt=0,
                ring_started_at=None,
                started_at=timezone.now(),
            )

        transaction.on_commit(lambda: async_task(notifications.notify_about_new_ticket, str(instance.pk)))
        return instance

    def to_representation(self, instance):
        return TicketForClientDetailSerializer(instance, context=self.context).data


class RelatedTaskSerializer(serializers.Serializer):
    """Минимальный сериализатор для связанных задач."""
    id = serializers.UUIDField()
    counter = serializers.CharField()


class HelpDeskTicketListSerializer(serializers.ModelSerializer):

    specialist = CachedAppUserPreviewSerializer(source='specialist_id')
    author = CachedAppUserPreviewSerializer(source='author_id')
    status = CachedBaseCatalogSerializer(source='status_id', model=models.HelpDeskTicketStatusModel, serializer_class=HelpDeskTicketStatusSerializer)
    priority = CachedBaseCatalogSerializer(source='priority_id', model=models.HelpDeskTicketPriorityModel, serializer_class=HelpDeskTicketPrioritySerializer)
    ticket_type = CachedBaseCatalogSerializer(source='ticket_type_id', model=models.HelpDeskTicketTypeModel, serializer_class=TicketTypeSerializer)
    channel = CachedBaseCatalogSerializer(source='channel_id', model=models.HelpDeskChannelModel, serializer_class=HelpDeskChannelModelSerializer)

    category = CachedBaseModelSerializer(source='category_id', serializer_class=HelpDeskTicketCategorySerializer)
    customer_card = CustomerCardForContactSerializer()
    contact_person = ContactPersonModelShortSerializer()
    analytics_key = SelectListSerializer(read_only=True)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'specialist',
            'dead_line',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
            'created_from_messages',
            'author',
            'status',
            'status_from_client',
            'priority',
            'ticket_type',
            'category',
            'channel',

            'customer_card',
            'contact_person',
            'analytics_key',
            'receipt_date',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'avg_rating'):
            data['rating'] = instance.avg_rating
        else:
            data['rating'] = instance.ratings.all().aggregate(avg_rating=Avg('rating'))['avg_rating']
        data['work_log_duration'] = instance.duration
        try:
            sla_value = instance.sla_value
        except ObjectDoesNotExist:
            data['sla'] = None
        else:
            data['sla'] = AppSLAValueSerializer(sla_value).data

        # related_tasks выводим только если были загружены во view (list)
        if hasattr(instance, 'related_tasks'):
            data['related_tasks'] = RelatedTaskSerializer(instance.related_tasks, many=True).data

        return data


class HelpDeskTicketMyDaySerializer(serializers.Serializer):
    """Сериализатор для аналитики тикетов в 'Моём дне'."""
    id = serializers.UUIDField()
    number = serializers.CharField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    duration = serializers.IntegerField()
    status = CachedBaseCatalogSerializer(source='status_id', model=models.HelpDeskTicketStatusModel, serializer_class=HelpDeskTicketStatusSerializer)
    priority = CachedBaseCatalogSerializer(source='priority_id', model=models.HelpDeskTicketPriorityModel, serializer_class=HelpDeskTicketPrioritySerializer)
    ticket_type = CachedBaseCatalogSerializer(source='ticket_type_id', model=models.HelpDeskTicketTypeModel, serializer_class=TicketTypeSerializer)
    channel = CachedBaseCatalogSerializer(source='channel_id', model=models.HelpDeskChannelModel, serializer_class=HelpDeskChannelModelSerializer)
    category = CachedBaseModelSerializer(source='category_id', serializer_class=HelpDeskTicketCategorySerializer)
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')
    author = CachedAppUserPreviewSerializer(source='author_id')
    customer_card = CustomerCardForContactSerializer()
    contact_person = ContactPersonModelShortSerializer()
    analytics_key = SelectListSerializer( read_only=True)
    dead_line = serializers.DateTimeField(allow_null=True)
    start_date = serializers.DateTimeField(allow_null=True)
    end_date = serializers.DateTimeField(allow_null=True)
    receipt_date = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField()

    # Поля аналитики
    actual_duration_days = serializers.IntegerField(allow_null=True, read_only=True)
    duration_total_all = serializers.IntegerField(read_only=True)
    duration_total_range = serializers.IntegerField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)
    duration_incomplete = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        analytics_data_map = self.context.get('analytics_data_map', {})
        data = analytics_data_map.get(str(instance.id), {})

        representation = super().to_representation(instance)
        representation['actual_duration_days'] = data.get('actual_duration_days')
        representation['duration_total_all'] = data.get('duration_total_all', 0)
        representation['duration_total_range'] = data.get('duration_total_range', 0)
        representation['is_current'] = data.get('is_current', False)
        representation['duration_incomplete'] = data.get('duration_incomplete', 0)

        try:
            sla_value = instance.sla_value
        except ObjectDoesNotExist:
            representation['sla'] = None
        else:
            representation['sla'] = AppSLAValueSerializer(sla_value).data

        return representation


class HelpDeskTicketShortSerializer(serializers.ModelSerializer):

    status = CachedBaseCatalogSerializer(source='status_id', model=models.HelpDeskTicketStatusModel, serializer_class=HelpDeskTicketStatusSerializer)
    priority = CachedBaseCatalogSerializer(source='priority_id', model=models.HelpDeskTicketPriorityModel, serializer_class=HelpDeskTicketPrioritySerializer)
    customer_card = CustomerCardForContactSerializer()
    contact_person = ContactPersonModelShortSerializer()
    analytics_key = SelectListSerializer(read_only=True)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'dead_line',
            'start_date',
            'end_date',
            'status',
            'status_from_client',
            'priority',
            'customer_card',
            'contact_person',
            'analytics_key',
            'receipt_date',
        )


class HelpDeskTicketCallShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'customer_card',
        )


class HelpDeskTicketChatShareSerializer(serializers.ModelSerializer):
    category = HelpDeskTicketCategorySerializer()
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'category',
            'specialist',
            'dead_line',
        )


class HelpDeskTicketDetailSerializer(serializers.ModelSerializer):

    status = HelpDeskTicketStatusSerializer()
    category = HelpDeskTicketCategorySerializer()
    priority = HelpDeskTicketPrioritySerializer()
    visors = CachedAppUserPreviewSerializer(many=True)
    members = CachedAppUserPreviewSerializer(many=True)
    customer_card = CustomerCardForTicketSerializer()
    contact_person = ContactPersonModelListSerializer()
    analytics_key = SelectListSerializer( read_only=True)
    author = CachedAppUserPreviewSerializer(source='author_id')
    channel = HelpDeskChannelModelSerializer()
    specialist = CachedAppUserPreviewSerializer(source='specialist_id')
    ticket_type = TicketTypeSerializer()
    meeting = serializers.SerializerMethodField()

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'description',
            'author',
            'status',
            'status_from_client',
            'channel',
            'priority',
            'category',
            'customer_card',
            'specialist',
            'contact_person',
            'analytics_key',
            'customer_card',
            'dead_line',
            'start_date',
            'end_date',
            'visors',
            'members',
            'created_at',
            'updated_at',
            'created_from_messages',
            'execution_result',
            'metadata',
            'ticket_type',
            'receipt_date',
            'meeting',
        )

    def get_meeting(self, instance):
        """Возвращает данные для подключения к связанной встрече."""
        from bpms.meetings.utils import get_related_meeting
        meeting = get_related_meeting(instance)
        if not meeting:
            return None
        return meeting.get_connect_info()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        rating = instance.ratings.all().first()
        if rating:
            rating_data = RatingReadSerializer(rating).data
        else:
            rating_data = None
        data['rating'] = rating_data
        data['work_log_duration'] = instance.duration
        request = self.context.get('request')
        if request:
            user = request.user.profile
            data['started_timer'] = instance.work_logs.filter(user=user, is_active=True, is_current=True).exists()
            if instance.channel_id == 'internal_chat':
                chat_message = utils.get_ticket_first_chat_message(instance)
                if chat_message:
                    chat = chat_message.chat
                    if chat:
                        data['related_chat'] = ChatListShortSerializer(chat, context=self.context).data
        return data


class HelpDeskTicketCreateSerializer(serializers.ModelSerializer):
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    message = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.ContactPersonMessageModel.objects.filter(is_active=True)
    )
    in_work = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=False,
    )
    analytics_key = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=CustomerContractProjectModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'name',
            'description',
            'priority',
            'category',
            'specialist',
            'contact_person',
            'customer_card',
            'analytics_key',
            'dead_line',
            'visors',
            'members',
            'message',
            'created_from_messages',
            'metadata',
            'channel',
            'receipt_date',
            'in_work',
        )

    def validate(self, attrs):
        contact_person = attrs.get('contact_person')
        message = attrs.get('message')
        if contact_person and message:
            if not contact_person == message.contact_person:
                raise drf_exceptions.ValidationError('Invalid message')
        specialist = attrs.get('specialist')
        customer_card = attrs.get('customer_card')
        analytics_key = attrs.get('analytics_key')
        request = self.context.get('request')
        # if not customer_card.get_create_ticket_permission(request):
        #     raise drf_exceptions.ValidationError('Вы не можете создать обращение для этого контрагента')
        if specialist:
            if not customer_card.actual_specialists.filter(user=specialist).exists():
                raise drf_exceptions.ValidationError("Ответственный тикета не является ответственным карточки клиента")
        self._validate_analytics_key(analytics_key=analytics_key, customer_card=customer_card, request=request)
        in_work = attrs.get('in_work')
        if in_work:
            user = request.user.profile
            if attrs.get('specialist') and attrs.get('specialist') == user:
                pass
            else:
                attrs.pop('in_work', None)
        members = attrs.get('members')
        if members:
            org_admin = customer_card.org_admin
            tree_org_admin = get_tree_departments_related_organizations((org_admin.pk,))
            for each in members:
                if not ContractorProfileModel.objects.filter(user=each, contractor_id__in=tree_org_admin).exists():
                    raise drf_exceptions.ValidationError(
                        f'Пользователь {each.full_name} не может быть участником обращения.'
                    )

        return attrs

    @staticmethod
    def _validate_analytics_key(analytics_key, customer_card, request):
        if not analytics_key:
            return

        contract = analytics_key.customer_contract
        if not contract:
            raise drf_exceptions.ValidationError('Ключ аналитики не связан с контрактом.')

        if request and not analytics_key.get_detail_permission(request):
            raise drf_exceptions.ValidationError('Нет доступа к выбранному ключу аналитики.')

        if customer_card and not contract.serviced_cards_relations.filter(
            customer_card=customer_card,
            is_active=True,
        ).exists():
            raise drf_exceptions.ValidationError('Выбранный ключ аналитики не относится к контрагенту обращения.')

    def create(self, validated_data):
        visors = validated_data.pop('visors', None)
        members = validated_data.pop('members', None)
        message = validated_data.pop('message', None)
        in_work = validated_data.pop('in_work', None)
        with transaction.atomic():
            if message:
                validated_data['created_from_messages'] = True
            else:
                validated_data['created_from_messages'] = False
            name = validated_data.get('name')
            if not name:
                name = ''
                category = validated_data.get('category')
                if category:
                    name = category.name
                description = validated_data.get('description')
                if description:
                    soup = BeautifulSoup(description, 'lxml').get_text(separator=" ").strip()[:50]
                    if soup:
                        name = name + ': ' + soup
                        name = name.strip(':')
                validated_data['name'] = name
            if not validated_data.get('channel'):
                validated_data['channel'] = models.HelpDeskChannelModel.objects.get(code='internal')
            instance = super().create(validated_data)
            if visors:
                instance.visors.set(visors)
            if members:
                instance.members.set(members)
                members_id = [str(_.pk) for _ in members]
                transaction.on_commit(lambda: async_task(notifications.notify_about_assign_member, str(instance.pk), members_id))
            if in_work:
                utils.change_ticket_status(instance, instance.specialist, 'in_work')
            if message:
                messages = list(models.ContactPersonMessageModel.objects.filter(
                    is_active=True,
                    created_at__gte=message.created_at,
                    contact_person=message.contact_person,
                ).order_by('created_at',).values_list('pk', flat=True))
                instance.messages.set(messages)
            instance.set_sla_value()
            transaction.on_commit(lambda: async_task(notifications.notify_about_new_ticket, str(instance.pk)))
        return instance

    def to_representation(self, instance):
        return HelpDeskTicketDetailSerializer(instance, context=self.context).data


class HelpDeskTicketUpdateSerializer(serializers.ModelSerializer):
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    analytics_key = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=CustomerContractProjectModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'name',
            'description',
            'priority',
            'category',
            'specialist',
            'customer_card',
            'contact_person',
            'analytics_key',
            'dead_line',
            'visors',
            'members',
            'metadata',
            'receipt_date',
            'contact_person',
        )

    def validate(self, attrs):
        instance = self.instance
        specialist = attrs.get('specialist')
        customer_card = attrs.get('customer_card')
        if customer_card and not customer_card == instance.customer_card:
            if instance.channel_id not in ('internal', 'internal_chat',):
                raise drf_exceptions.ValidationError('Нельзя изменить контрагента для этого канала связи.')
        contact_person = attrs.get('contact_person')
        if contact_person and not contact_person == instance.contact_person:
            if instance.channel_id not in ('internal', 'internal_chat',):
                raise drf_exceptions.ValidationError('Нельзя изменить контактное лицо для этого канала связи.')
            if not customer_card:
                customer_card = instance.customer_card
            if not customer_card.contact_persons.filter(pk=contact_person.pk).exists():
                raise drf_exceptions.ValidationError('Контактное лицо не относится к контрагенту обращения')
        if specialist:
            if not specialist == instance.specialist:
                ticket_type_id = instance.ticket_type_id
                customer_card = instance.customer_card
                if ticket_type_id == 'issue':
                    if not customer_card.actual_specialists.filter(user=specialist).exists():
                        raise drf_exceptions.ValidationError(
                            "Ответственный тикета не является ответственным карточки клиента"
                        )
                else:
                    org_admin = customer_card.org_admin
                    try:
                        check_contractor_permission(
                            specialist.pk,
                            org_admin.pk,
                            ('help_desk_admin', 'help_desk_manager',),
                            None
                        )
                    except drf_exceptions.PermissionDenied:
                        raise drf_exceptions.ValidationError(
                            f'Пользователя {specialist.full_name} нельзя назначить ответственного за этим лидом'
                        )
        selected_customer_card = attrs.get('customer_card') if 'customer_card' in attrs else instance.customer_card
        selected_analytics_key = attrs.get('analytics_key') if 'analytics_key' in attrs else instance.analytics_key
        HelpDeskTicketCreateSerializer._validate_analytics_key(
            analytics_key=selected_analytics_key,
            customer_card=selected_customer_card,
            request=self.context.get('request')
        )
        members = attrs.get('members')
        if members:
            org_admin = instance.customer_card.org_admin
            tree_org_admin = get_tree_departments_related_organizations((org_admin.pk,))
            for each in members:
                if not ContractorProfileModel.objects.filter(user=each, contractor_id__in=tree_org_admin).exists():
                    raise drf_exceptions.ValidationError(
                        f'Пользователь {each.full_name} не может быть участником обращения.'
                    )
        return attrs

    def update(self, instance, validated_data):
        visors = validated_data.pop('visors', None)
        members = validated_data.pop('members', None)
        old_specialist = instance.specialist
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if visors is not None:
                instance.visors.clear()
                instance.visors.set(visors)
            if members is not None:

                instance.members.clear()
                if members:
                    old_members_id = set(instance.members.all().values_list('pk', flat=True))
                    new_members_id = set(_.pk for _ in members)
                    diff_members_id = new_members_id - old_members_id
                    instance.members.set(members)
                    if diff_members_id:
                        transaction.on_commit(
                            lambda: async_task(
                                notifications.notify_about_assign_member,
                                str(instance.pk),
                                [str(_) for _ in diff_members_id]
                            )
                        )
            instance.set_sla_value()
        new_specialist = instance.specialist
        if new_specialist and not old_specialist == new_specialist:
            utils.stop_work_log_timer(old_specialist, instance,)
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_about_assign_specialist, str(instance.pk), str(new_specialist.pk)
                )
            )
        return instance

    def to_representation(self, instance):
        data = HelpDeskTicketDetailSerializer(instance, context=self.context).data
        try:
            sla = instance.sla_value
        except ObjectDoesNotExist:
            data['sla'] = None
        else:
            data['sla'] = SLAValueSerializer(sla).data
        return data


class UpdateTicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'status',
            'execution_result',
        )

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        completed_statuses = utils.get_completed_statuses_id()
        if status.code not in completed_statuses:
            validated_data.pop('execution_result', None)

        if status.code in completed_statuses:
            validated_data['end_date'] = timezone.now()

        if status.code == 'in_work' and not instance.start_date:
            validated_data['start_date'] = timezone.now()

        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        empty_return = self.context.get('empty_return')
        if empty_return:
            return dict()
        return HelpDeskTicketDetailSerializer(instance, context=self.context).data


class UpdateTicketExecutionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'execution_result',
        )


class WorkLogListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')

    class Meta:
        model = models.HelpDeskWorkLogModel
        fields = (
            'id',
            'date',
            'description',
            'duration',
            'created_at',
            'user',
            'is_current',
            'edited',
            'is_result',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_current:
            now = self.context.get('now')
            if not now:
                now = timezone.now()
            data['duration'] = utils.get_incomplete_duration(now, instance.created_at)
        return data


class WorkLogUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskWorkLogModel
        fields = (
            'id',
            'duration',
            'description',
            'edited',
            'date',
            'user',
            'is_result',
        )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if not instance.edited:
            instance.edited = True
            instance.save(update_fields=('edited',))
        return instance

    def to_representation(self, instance):
        return WorkLogListSerializer(instance, context=self.context).data


class WorkLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskWorkLogModel
        fields = (
            'id',
            'ticket',
            'duration',
            'description',
            'edited',
            'is_current',
            'date',
            'user',
            'is_result',
        )

    def validate(self, attrs):
        ticket = attrs.get('ticket')
        user = attrs.get('user')
        profile = self.context.get('request').user.profile
        if user and ticket and not profile == user:
            check_contractor_permission(profile.pk, ticket.customer_card.org_admin.pk, 'help_desk_admin', None)
        return attrs

    def create(self, validated_data):
        validated_data['edited'] = True
        validated_data['is_current'] = False
        instance = super().create(validated_data)
        return instance

    def to_representation(self, instance):
        return WorkLogListSerializer(instance, context=self.context).data


class MyOrgAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name',
        )

# Материальные затраты:

class HelpDeskCostDetailSerializer(serializers.ModelSerializer):
    measure_unit = MeasureUnitListSerializer()
    goods = AppNomenclatureSerializer()

    class Meta:
        model = models.HelpDeskCostModel
        fields = (
            'id',
            'goods',
            'name',
            'name_short',
            'article_number',
            'quantity',
            'measure_unit',
            'amount',
            'period',
        )


class HelpDeskCostListSerializer(serializers.ModelSerializer):
    measure_unit = MeasureUnitListSerializer()
    goods = AppNomenclatureSerializer()

    class Meta:
        model = models.HelpDeskCostModel
        fields = (
            'id',
            'goods',
            'name',
            'name_short',
            'article_number',
            'quantity',
            'measure_unit',
            'amount',
            'period',
        )


class HelpDeskCostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskCostModel
        fields = (
            'id',
            'owner',
            'goods',
            'quantity',
            'amount',
            'period',
        )

    def validate(self, attrs):
        owner = attrs.get('owner')
        if not owner:
            raise drf_exceptions.ValidationError('Обращение не указано')
        request = self.context.get('request')
        customer_card = owner.customer_card
        if not customer_card.get_update_permission(request):
            raise drf_exceptions.ValidationError('Вы не можете добавлять запись для этого обращения')
        goods = attrs.get('goods')
        org_admin = customer_card.org_admin
        if not org_admin == goods.contractor:
            raise drf_exceptions.ValidationError('Вы не можете указывать этот материал')
        return attrs

    def create(self, validated_data):
        goods = validated_data.get('goods')
        validated_data['measure_unit'] = goods.base_measure_unit
        validated_data['base_measure_unit'] = goods.base_measure_unit
        validated_data['article_number'] = goods.article_number
        validated_data['name'] = goods.name
        validated_data['name_short'] = goods.name_short
        instance = super().create(validated_data)
        return instance

    def to_representation(self, instance):
        data = HelpDeskCostListSerializer(instance, context=self.context).data
        return data


class HelpDeskCostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpDeskCostModel
        fields = (
            'id',
            'goods',
            'quantity',
            'amount',
            'period',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        instance = self.instance
        owner = instance.owner
        customer_card = owner.customer_card
        if not customer_card.get_update_permission(request):
            raise drf_exceptions.ValidationError('Вы не можете изменять запись для этого обращения')
        goods = attrs.get('goods')
        old_goods = instance.goods
        if not old_goods == goods:
            org_admin = customer_card.org_admin
            if not org_admin == goods.contractor:
                raise drf_exceptions.ValidationError('Вы не можете указывать этот материал')

    def update(self, instance, validated_data):
        new_goods = validated_data.get('goods')
        if new_goods:
            old_goods = instance.goods
            if not old_goods == new_goods:
                validated_data['measure_unit'] = new_goods.base_measure_unit
                validated_data['base_measure_unit'] = new_goods.base_measure_unit
                validated_data['article_number'] = new_goods.article_number
                validated_data['name'] = new_goods.name
                validated_data['name_short'] = new_goods.name_short
        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        data = HelpDeskCostListSerializer(instance, context=self.context).data
        return data


class HelpDeskTicketFireSerializer(serializers.ModelSerializer):
    specialist = CachedAppUserPreviewSerializer(source='specialist_id',)

    class Meta:
        model = models.HelpDeskTicketModel
        fields = (
            'id',
            'number',
            'name',
            'specialist',
        )


class CustomerCardModelShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerCardModel
        fields = (
            'id',
            'name',
            'inn',
        )


class UnrelatedExternalCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalCustomerModel
        fields = (
            'id',
            'name',
            'full_name',
            'external_id',
            'inn',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        org_admin_id = self.context.get('request').query_params.get('org_admin')
        suggestion_customer_cards = models.CustomerCardModel.objects.filter(
            inn=instance.inn,
            org_admin_id=org_admin_id,
        )
        suggestion_count = suggestion_customer_cards.count()
        if suggestion_count == 1:
            suggestion = suggestion_customer_cards.first()
            data['suggestion'] = {'id': suggestion.pk, 'name': suggestion.name}
        return data

