from abc import abstractmethod

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Model

from bkz3.settings import URLS
from bpms.bpms_common.models import NewsModel
from bpms.comments.models import CommentModel
from bpms.event_calendar.models import EventCalendarModel
from bpms.meetings.models import CallModel, PlannedMeetingModel
from bpms.tasks.models import TaskModel, TaskSprintModel
from bpms.workgroups.models import WorkgroupMembershipRole, WorkgroupModel
from common.catalogs.models import ContractorModel
from consolidation.models import ConsolidationModel, ReportModel
from contractor_invites.models import ContractorInviteModel
from crm.models import GoodsOrderModel
from tickets.models import TicketModel
from users.models import ProfileModel
from invest_projects_info.models import InvestProjectInfoModel
from tags.models import TagModel
# from sports_facilities_info.models import SportFacilityInfoModel
from contractor_permissions.utils import users_that_have_app_section_role_in_contractors


class BaseEventType:
    """
    Базовый класс типа события уведомления.
    code - код события. Записывается в уведомление в поле event_type. По нему получаем класс события для увдеомления.
    color - цвет уведомления. Возможные значения: default, primary, warning, danger, success.
    icon - иконка уведомления. Возможные значения см. в https://www.antdv.com/components/icon/
    color и icon используются фронтендом для отображения уведомления с соответствующей иконкой и цветом.
    """

    def __init__(self, data: dict = None, *args, **kwargs):
        self.data = data

    code: str
    verbose_name: str
    verbose_name_kk: str
    color: str = 'default'
    icon: str = 'info'
    template_html: str
    template_text: str
    template_html_kk: str
    template_text_kk: str
    category_code: str = None  # Код категории для группировки в UI
    show_in_settings: bool = True  # Видимость в настройках пользователя
    default_enabled: bool = True  # Включено по умолчанию
    is_mention: bool = False
    is_personalized_notification: bool = False
    # Имя kwarg, из которого брать объект для группировки уведомлений (заполнения content_type/object_id).
    # None — уведомление не группируется. По умолчанию берётся из subj.
    subject_source: str = 'subj'

    url: str = f"{URLS.get('notifications', '')}"

    
    def create_notification(self, recipients: tuple = tuple(), **kwargs):
        """Создаёт и возвращает уведомление с данным event_type.
        Фильтрует получателей по их настройкам уведомлений."""
        from .models import WebNotificationModel

        filtered_recipient_ids = self.get_filtered_recipient_ids(
            recipients=recipients,
        )

        if not filtered_recipient_ids:
            return None

        subject = self.get_subject(**kwargs)
        content_type = None
        object_id = None
        if isinstance(subject, Model) and subject.pk is not None:
            content_type = ContentType.objects.get_for_model(subject.__class__)
            object_id = subject.pk

        notifications = []
        buckets = {}

        if self.is_personalized_notification:
            recipients_map = ProfileModel.objects.in_bulk(filtered_recipient_ids)
            for recipient_id in filtered_recipient_ids:
                recipient_profile = recipients_map.get(recipient_id)
                collect_context = self.get_collect_context(recipient=recipient_profile, **kwargs)
                if not collect_context:
                    context_key = tuple()
                else:
                    context_key = tuple(
                        (key, repr(value))
                        for key, value in sorted(collect_context.items(), key=lambda item: item[0])
                    )
                if context_key not in buckets:
                    buckets[context_key] = {
                        'recipient_ids': [],
                        'collect_context': collect_context,
                    }
                buckets[context_key]['recipient_ids'].append(recipient_id)
        else:
            context_key = tuple()
            buckets[context_key] = {
                'recipient_ids': filtered_recipient_ids,
                'collect_context': dict(),
            }

        with transaction.atomic():
            for context_key, bucket in buckets.items():
                collect_context = bucket['collect_context']
                current_recipient_ids = bucket['recipient_ids']
                collected_data = self.collect_data(collect_context=collect_context, **kwargs)
                notification = WebNotificationModel.objects.create(
                    event_type_id=self.code,
                    data=collected_data,
                    content_type=content_type,
                    object_id=object_id,
                )
                notification.recipients.set(current_recipient_ids)
                transaction.on_commit(lambda notify=notification: notify.send_message_about_new_notify())
                transaction.on_commit(lambda notify=notification: notify.send_messages_to_tg())
                notifications.append(notification)

        if not notifications:
            return None
        return notifications[-1]

    @abstractmethod
    def collect_data(self, collect_context: dict = None, **kwargs) -> dict:
        """
        Принимает на вход объекты, и возвращает data уведомления, соответствующее этому event_type.
        Применяется при создании уведомления с этим event_type.
        """
        if kwargs:
            data = {}
            for key, instance in kwargs.items():
                serializer_class = instance.get_serializer_class(action='notify')
                if collect_context:
                    data[key] = serializer_class(instance, context=collect_context).data
                else:
                    data[key] = serializer_class(instance).data
            return data
        else:
            return dict()

    def get_filtered_recipient_ids(self, recipients):
        """Фильтрует получателей по настройкам категории и типа уведомления."""
        from .models import (
            EventTypeModel,
            NotificationCategoryPreferenceModel,
            NotificationEventTypePreferenceModel,
        )

        recipient_ids = []
        for recipient in recipients:
            if hasattr(recipient, 'id'):
                recipient_ids.append(recipient.id)
            else:
                recipient_ids.append(recipient)

        if not recipient_ids:
            return []

        event_type = EventTypeModel.objects.get(code=self.code)
        disabled_category_users = set()
        if event_type.category_id:
            disabled_category_users = set(
                NotificationCategoryPreferenceModel.objects.filter(
                    user_id__in=recipient_ids,
                    category_id=event_type.category_id,
                    is_enabled=False,
                ).values_list('user_id', flat=True)
            )

        user_preferences = {
            preference.user_id: preference.is_enabled
            for preference in NotificationEventTypePreferenceModel.objects.filter(
                user_id__in=recipient_ids,
                event_type_id=self.code
            )
        }

        filtered_recipient_ids = []
        for profile_id in recipient_ids:
            if profile_id in disabled_category_users:
                continue
            if profile_id in user_preferences:
                is_enabled = user_preferences[profile_id]
            else:
                is_enabled = event_type.default_enabled

            if is_enabled:
                filtered_recipient_ids.append(profile_id)

        return filtered_recipient_ids

    def get_collect_context(self, recipient: ProfileModel = None, **kwargs) -> dict:
        """Метод для переопределения: возвращает контекст сериализации для конкретного получателя."""
        return dict()

    def get_subject(self, **kwargs):
        """Возвращает инстанс модели для группировки уведомлений.
        По умолчанию — kwargs[self.subject_source]. Переопределяй для вычисляемых случаев."""
        if not self.subject_source:
            return None
        return kwargs.get(self.subject_source)


class TestSignal(BaseEventType):
    """
    Тестовый сигнал.
    """

    code: str = 'test_signal'
    verbose_name: str = 'Тестовый сигнал'
    verbose_name_kk: str = ''
    color: str = 'success'
    category_code: str = 'system'
    subject_source = None
    template_html = "Тестовый сигнал от пользователя <a href={{urls.tasks}}>{{initiator.full_name}}</a>"
    template_text = "Тестовый сигнал от пользователя {{initiator.full_name}} {{urls.tasks}}"
    # Казахский
    template_html_kk = "Тестовый сигнал от пользователя <a href={{urls.tasks}}>{{initiator.full_name}}</a>"
    template_text_kk = "Тестовый сигнал от пользователя {{initiator.full_name}} {{urls.tasks}}"

    def collect_data(self, initiator: ProfileModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator)


# Уведомления по задачам:
class TaskAssignOperator(BaseEventType):
    """
    Назначен ответственным задачи.
    """
    code: str = 'task_assign_operator_notify'
    verbose_name: str = 'Назначение ответственным задачи'
    verbose_name_kk: str = 'Тапсырмаға жауаптыны тағайындау'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) Вам задачу ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) Вам задачу #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} сізге тапсырма берді ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text_kk = '{{initiator.full_name}} сізге тапсырма берді #{{subj.counter}} "{{subj.name}}".'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class LogisticTaskAssignOperator(BaseEventType):
    """
        Назначен ответстенным логистической задачи.
        """
    code: str = 'logistic_task_assign_operator_notify'
    verbose_name: str = 'Назначение задания на доставку'
    verbose_name_kk: str = 'Жеткізу жұмысын тағайындау'
    color: str = 'primary'
    icon: str = 'environment'
    category_code: str = 'logistic_tasks'
    template_html = '{{initiator.full_name}} назначил(-а) Вам задание на доставку ' \
                    '<span class="n_link" data-link-type="logistic"' \
                    ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>. '
    template_text = '{{initiator.full_name}} назначил(-а) Вам задание на доставку #{{subj.counter}} "{{subj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} сізге жеткізу тапсырмасын берді ' \
                    '<span class="n_link" data-link-type="logistic"' \
                    ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>. '
    template_text_kk = '{{initiator.full_name}} сізге жеткізу тапсырмасын берді #{{subj.counter}} "{{subj.name}}"'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskAssignOperatorForVisors(BaseEventType):
    """
    Назначен ответственным задачи. Уведомление для наблюдателей.
    """
    code: str = 'task_assign_operator_for_visors_notify'
    verbose_name: str = 'Назначение ответственным задачи (для наблюдателей)'
    verbose_name_kk: str = 'Тапсырмаға жауаптыны тағайындау (бақылаушылар үшін)'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) ответственным пользователя {{obj.full_name}} в задаче ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) ответственным пользователя {{obj.full_name}} ' \
                    'в задаче #{{subj.counter}} "{{subj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} #{{subj.counter}} тапсырмада {{obj.full_name}} пайдаланушыны жауапты етіп тағайындады ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true"> "{{subj.name}}"</span>.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} тапсырмада {{obj.full_name}} ' \
                    'пайдаланушыны жауапты етіп тағайындады "{{subj.name}}"'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: ProfileModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class TaskAssignCooperatorForVisors(BaseEventType):
    """
    Назначен соисполнителем задачи. Уведомление для наблюдателей.
    """
    code: str = 'task_assign_cooperator_for_visors_notify'
    verbose_name: str = 'Назначение соисполнителем задачи (для наблюдателей)'
    verbose_name_kk: str = 'Тапсырмаға бірлесіп орындаушы ретінде тағайындау (бақылаушылар үшін)'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) соисполнителем пользователя {{obj.full_name}} в задаче ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) соисполнителем пользователя {{obj.full_name}} ' \
                    'в задаче #{{subj.counter}} "{{subj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} {{obj.full_name}} пайдаланушысын ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> тапсырмасына бірлесіп орындаушы ретінде тағайындады'
    template_text_kk = '{{initiator.full_name}} {{obj.full_name}} ' \
                    'пайдаланушысын #{{subj.counter}} "{{subj.name}}" тапсырмасына бірлесіп орындаушы ретінде тағайындады'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: ProfileModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class TaskAssignOwner(BaseEventType):
    """
    Назначен постановщиком задачи.
    """
    code: str = 'task_assign_owner_notify'
    verbose_name: str = 'Назначение постановщиком задачи'
    verbose_name_kk: str = 'Тапсырма беруші ретінде тағайындау'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) Вас постановщиком задачи ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) Вас постановщиком задачи #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} Сізді ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>. ' \
                    'тапсырманың бастамашысы етіп тағайындады'
    template_text_kk = '{{initiator.full_name}} Сізді #{{subj.counter}} "{{subj.name}}" тапсырманың бастамашысы етіп тағайындады.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskAssignVisor(BaseEventType):
    """
    Назначен наблюдателем задачи.
    """
    code: str = 'task_assign_visors'
    verbose_name: str = 'Назначение наблюдателем задачи'
    verbose_name_kk: str = 'Тапсырма бақылаушы етіп тағайындауы'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) Вас наблюдателем задачи ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) Вас наблюдателем задачи #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} Сізді тапсырма бақылаушы етіп тағайындады ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text_kk = '{{initiator.full_name}} Сізді тапсырма бақылаушы етіп тағайындады #{{subj.counter}} "{{subj.name}}".'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskAssignCooperator(BaseEventType):
    """
    Назначен соисполнителем задачи.
    """
    code: str = 'task_assign_cooperators'
    verbose_name: str = 'Назначение соисполнителем задачи'
    verbose_name_kk: str = 'Тапсырмаға бірлесіп орындаушы ретінде тағайындау (бақылаушылар үшін)'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} назначил(-а) Вас соисполнителем задачи ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} назначил(-а) Вас соисполнителем задачи #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} Сізді ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> тапсырмасының бірлесіп орындаушысы етіп тағайындады'
    template_text_kk = '{{initiator.full_name}} Сізді #{{subj.counter}} "{{subj.name}}" тапсырмасының бірлесіп орындаушысы етіп тағайындады'
    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeDescription(BaseEventType):
    """
    Изменено описание задачи.
    """
    code: str = 'task_change_description'
    verbose_name: str = 'Изменение описания задачи'
    verbose_name_kk: str = 'Тапсырманың сипаттамасын өзгерту'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} изменил(-а) описание задачи ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} изменил(-а) описание задачи #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> тапсырмасының сипаттамасын өзгертті.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасының сипаттамасын өзгертті.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class NewWorkgroupTask(BaseEventType):
    """
    Новая задача в проекте/команде.
    """
    code: str = 'new_workgroup_task'
    verbose_name: str = 'Новая задача'
    verbose_name_kk: str = 'Жаңа тапсырма'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = (
        '{{initiator.full_name}} добавил(-а) новую задачу '
        '<span class="n_link" data-link-type="tasks" '
        'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' '
        'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>'
        '{% if subj.project %} в проект {{subj.project.name}}{% endif %}'
        '{% if subj.workgroup %} для команды {{subj.workgroup.name}}{% endif %}'
    )
    template_text = (
        '{{initiator.full_name}} добавил(-а) новую задачу '
        '#{{subj.counter}} "{{subj.name}}"'
        '{% if subj.project %} в проект {{subj.project.name}}{% endif %}'
        '{% if subj.workgroup %} для команды {{subj.workgroup.name}}{% endif %}'
    )
    # Казахский
    template_html_kk = (
        '{{initiator.full_name}} жаңа '
        '<span class="n_link" data-link-type="tasks" '
        'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' '
        'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>'
        ' тапсырмасын қосты '
        '{% if subj.project and subj.workgroup %} {{subj.project.name}} жобасында {{subj.workgroup.name}} командалары үшін'
        '{% elif subj.project %} {{subj.project.name}} жобасында'
        '{% elif subj.workgroup %} {{subj.workgroup.name}} командалары үшін'
        '{% endif %}'
    )
    template_text_kk = (
        '{{initiator.full_name}} жаңа '
        '#{{subj.counter}} "{{subj.name}}"'
        ' тапсырмасын қосты '
        '{% if subj.project and subj.workgroup %} {{subj.project.name}} жобасында {{subj.workgroup.name}} командалары үшін'
        '{% elif subj.project %} {{subj.project.name}} жобасында'
        '{% elif subj.workgroup %} {{subj.workgroup.name}} командалары үшін'
        '{% endif %}'
    )
    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskTakeAuction(BaseEventType):
    """
    Забираем задачу в аукционе
    """
    code: str = 'task_take_auction'
    verbose_name: str = 'Самоназначение через аукцион'
    verbose_name_kk: str = 'Аукцион арқылы өзін-өзі тағайындау'
    color: str = 'default'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} выиграл(-а) в аукционе ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'' \
                    '{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} выиграл(-а) в аукционе #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} аукционда жеңіске жетті ' \
                    '<span class="n_link" data-link-type="tasks" data-link-query=\'' \
                    '{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text_kk = '{{initiator.full_name}}  аукционда жеңіске жетті #{{subj.counter}} "{{subj.name}}".'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusGeneric(BaseEventType):
    """Общее уведомление о смене статуса (если для него нет специального уведомления)."""
    code: str = 'task_change_status_generic'
    verbose_name: str = 'Смена статуса задачи'
    verbose_name_kk: str = 'Тапсырма күйінің өзгеруі'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html: str = '{{initiator.full_name}} сменил(-а) статус задачи ' \
                         '<span class="n_link" data-link-type="tasks" ' \
                         'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         'на <strong>{{subj.status.name}}</strong>.'
    template_text: str = '{{initiator.full_name}} сменил(-а) статус задачи #{{subj.counter}} "{{subj.name}}". \n' \
                         'Новый статус: {{subj.status.name}}.'
    template_html_kk: str = '{{initiator.full_name}} ' \
                         '<span class="n_link" data-link-type="tasks" ' \
                         'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         'тапсырманың күйін <strong>{{subj.status.name}}</strong> етіп өзгертті.'

    template_text_kk: str = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}". \n' \
                         'тапсырманың күйін өзгертті. Жаңа күйі: {{subj.status.name}}.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeCooperatorStatusGeneric(BaseEventType):
    """Общее уведомление о смене статуса соисполнителя."""
    code: str = 'task_change_coop_status_generic'
    verbose_name: str = 'Смена статуса соисполнителя'
    verbose_name_kk: str = 'Бірлесіп орындаушының күйінің өзгеруі'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html: str = 'Соисполнитель {{initiator.full_name}} сменил(-а) свой статус в задаче ' \
                         '<span class="n_link" data-link-type="tasks" ' \
                         'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         'на <strong>{{obj.name_ru}}</strong>.'
    template_text: str = 'Соисполнитель {{initiator.full_name}} сменил(-а) свой статус в задаче #{{subj.counter}} "{{subj.name}}". \n' \
                         'Новый статус: {{obj.name_ru}}.'
    template_html_kk: str = 'Бірлесіп орындаушы {{initiator.full_name}} ' \
                            '<span class="n_link" data-link-type="tasks" ' \
                            'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                            'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                            'тапсырмасындағы өзінің күйін <strong>{{obj.name_kk}}</strong> деп өзгертті.'

    template_text_kk: str = 'Бірлесіп орындаушы {{initiator.full_name}} #{{subj.counter}} тапсырмасындағы өзінің күйін ' \
                            '"{{obj.name_kk}}" деп өзгертті.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj=None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class TaskCooperatorSetTaskStatus(BaseEventType):
    #  TODO добавить переводы
    code: str = 'task_coop_set_task_status'
    verbose_name: str = 'Соисполнитель начал работу'
    verbose_name_kk: str = 'Бірлесіп орындаушы жұмысты бастады'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html: str = 'Соисполнитель {{initiator.full_name}} начал(-а) работу над задачей ' \
                         '<span class="n_link" data-link-type="tasks" ' \
                         'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         'Статус задачи автоматически изменен на: <strong>В работе</strong>.'
    template_text: str = 'Соисполнитель {{initiator.full_name}} начал(-а) работу над задачей #{{subj.counter}} "{{subj.name}}". \n' \
                         'Статус задачи автоматически изменен на: "В работе".'
    template_html_kk: str = 'Бірлесіп орындаушы {{initiator.full_name}} ' \
                            '<span class="n_link" data-link-type="tasks" ' \
                            'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                            'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                            'тапсырмасы бойынша жұмысын бастады. Тапсырманың күйі автоматты түрде ' \
                            '<strong>«Жұмыс барысында»</strong> болып өзгертілді.'

    template_text_kk: str = 'Бірлесіп орындаушы {{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" ' \
                            'тапсырмасы бойынша жұмысын бастады. Тапсырманың күйі автоматты түрде «Жұмыс барысында» ' \
                            'болып өзгертілді.' \

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class LogisticTaskChangeStatusGeneric(BaseEventType):
    """Общее уведомление о смене статуса логистической задачи (если для него нет специального уведомления)."""
    code: str = 'logistic_task_change_status_generic'
    verbose_name: str = 'Смена статуса'
    verbose_name_kk: str = 'Күйінің өзгеруі'
    color: str = 'primary'
    icon: str = 'environment'
    category_code: str = 'logistic_tasks'
    template_html: str = '{{initiator.full_name}} сменил(-а) статус задания на доставку ' \
                         '<span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         'на <strong>"{{subj.status.name}}"</strong>.'
    template_text: str = '{{initiator.full_name}} сменил(-а) статус задания на доставку ' \
                         '#{{subj.counter}} "{{subj.name}}". \n' \
                         'Новый статус: {{subj.status.name}}.'
    # Казахский
    template_html_kk: str = '{{initiator.full_name}} ' \
                         '<span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                         ' жеткізу тапсырмасының күйін ' \
                         '<strong>"{{subj.status.name}}"</strong> күйіне өзгертті.'
    template_text_kk: str = '{{initiator.full_name}} ' \
                         '#{{subj.counter}} "{{subj.name}}" \n' \
                         'жеткізу тапсырмасының күйін өзгертті. Жаңа мәртебе: {{subj.status.name}}.'

    url: str = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusInWork(BaseEventType):
    """
    Смена статуса задачи: "в работе".
    """
    code: str = 'task_changed_status_in_work'
    verbose_name: str = 'Смена статуса задачи: "в работе"'
    verbose_name_kk: str = 'Тапсырманың күйі өзгертілді "жұмыс барысында"'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} приступил(-а) к работе над задачей ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} приступил(-а) к работе над задачей #{{subj.counter}} "{{subj.name}}". '
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмасымен жұмыс істуді бастады.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасымен жұмыс істуді бастады.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusOnCheck(BaseEventType):
    """
    Смена статуса задачи: "на проверке"
    """
    code: str = 'task_changed_status_on_check'
    verbose_name: str = 'Смена статуса задачи: "на проверке"'
    verbose_name_kk: str = 'Тапсырманың күйі өзгертілді: "тексерілуде"'
    color: str = 'success'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} отправил(-а) на проверку задачу ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} отправил(-а) на проверку задачу #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмасын тексерілуге жіберді.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасын тексерілуге жіберді.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusOnPause(BaseEventType):
    """
    Смена статуса задачи: "на паузе"
    """
    code: str = 'task_changed_status_on_pause'
    verbose_name: str = 'Смена статуса задачи: "на паузе"'
    verbose_name_kk: str = 'Тапсырманың күйі өзгертілді: "үзілісте"'
    color: str = 'warning'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} поставил(-а) на паузу задачу ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} поставил(-а) на паузу задачу #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмасын үзіліске қойды.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасын үзіліске қойды.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusOnRework(BaseEventType):
    """
    Смена статуса задачи: "на переделку."
    """
    code: str = 'task_changed_status_on_rework'
    verbose_name: str = 'Смена статуса задачи: "на переделке"'
    verbose_name_kk: str = 'Тапсырманың мәртебесін өзгерту: "қайта өңдеуде"'
    color: str = 'error'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} отправил(-а) на переделку задачу ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} отправил(-а) на переделку задачу #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмасын қайта орындауға жіберді.'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасын қайта орындауға жіберді.'
    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskChangeStatusCompleted(BaseEventType):
    """
    Смена статуса задачи: "завершена".
    """
    code: str = 'task_changed_status_completed'
    verbose_name: str = 'Смена статуса задачи: "завершена"'
    verbose_name_kk: str = 'Тапсырманың күйі өзгертілді: "аяқталды"'
    color: str = 'success'
    icon: str = 'profile'
    category_code: str = 'tasks'

    template_html = '{{initiator.full_name}} завершил(-а) задачу ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text = '{{initiator.full_name}} завершил(-а) задачу #{{subj.counter}} "{{subj.name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks" ' \
                    'data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмасын аяқтады.'

    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}}" тапсырмасын аяқтады.'
    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class UpdateTaskDeliveryPoints(BaseEventType):
    """Изменение точек доставки в задании на доставку."""
    code: str = 'task_update_delivery_points'
    verbose_name: str = 'Изменение точек доставки'
    verbose_name_kk: str = 'Жеткізу нүктелерін өзгерту'
    color: str = 'warning'
    icon: str = 'environment'
    category_code: str = 'logistic_tasks'

    template_html: str = '{{initiator.full_name}} внес(-ла) изменения в список точек доставки задания на доставку' \
                         '<span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>.'
    template_text: str = '{{initiator.full_name}} внес(-ла) изменения в список точек доставки задания на доставку' \
                         ' #{{subj.counter}} "{{subj.name}}". \n' \
                         'Новый статус: {{subj.status.name}}.'
    # Казахский
    template_html_kk: str = '{{initiator.full_name}} ' \
                         '<span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' ' \
                         'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> жеткізу тапсырмасының жеткізу нүктелері тізіміне өзгерістер енгізді'
    template_text_kk: str = '{{initiator.full_name}} ' \
                         ' #{{subj.counter}} "{{subj.name}}" жеткізу тапсырмасының жеткізу нүктелері тізіміне өзгерістер енгізді \n' \
                         'Жаңа күй: {{subj.status.name}}.'
    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class TaskGoodsLoaded(BaseEventType):
    """Уведомление о погрузке со склада"""
    code: str = 'task_goods_loaded'
    verbose_name: str = 'Погрузка со склада'
    verbose_name_kk: str = 'Қоймадан тиеу'
    color: str = 'primary'
    icon: str = 'environment'
    category_code: str = 'logistic_tasks'

    template_html: str = 'Рейс <span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' data-link-open="true">' \
                         '#{{subj.counter}} "{{subj.name}}"</span>: {{initiator.full_name}} ' \
                         'погрузил(-а) товар со склада "{{obj.name}}".'
    template_text: str = 'Рейс #{{subj.counter}} "{{subj.name}}": {{initiator.full_name}} погрузил(-а) товар со склада ' \
                         '{{obj.name}}.'
    # Казахский
    template_html_kk: str = '<span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{subj.id}}"}\' data-link-open="true">' \
                         '#{{subj.counter}} "{{subj.name}}"</span> рейсі: {{initiator.full_name}} ' \
                         '"{{obj.name}}" қоймасынан тауарды тиеді.'
    template_text_kk: str = '#{{subj.counter}} "{{subj.name}}" рейсі: {{initiator.full_name}} ' \
                         '{{obj.name}} қоймасынан тауарды тиеді.'

    url = '{{urls.notifications}}?task={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class TaskNewComment(BaseEventType):
    code: str = 'task_new_comments_notification'
    verbose_name: str = 'Новый комментарий к задаче'
    verbose_name_kk: str = 'Тапсырмаға жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'tasks'

    template_html = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к <strong>задаче</strong> ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}", "comment":true}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к задаче #{{subj.counter}} "{{subj.name}}":\n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}", "comment":true}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    '<strong>тапсырмасына</strong> {% if obj.is_personal %} құпия {% endif %} пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} "{{subj.name}} тапсырмасына ' \
                    '{% if obj.is_personal %} құпия {% endif %}' \
                    ' пікір қалдырды ":\n {{obj.text}}'

    url = '{{urls.notifications}}?task={{subj.id}}&stab={{subj.task_type}}&comment=true'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj: TaskModel = None,
                            obj: CommentModel = None):
        if obj.is_personal:
            recipients = set(list(obj.readers.all()))
        else:
            from bpms.tasks.notifications import get_task_participants, get_workgroup_founders_and_moderators
            recipients = get_task_participants(subj)
            recipients.update(get_workgroup_founders_and_moderators(subj))
            recipients.discard(initiator.pk)
            recipients.discard(None)
            mentions = set(obj.mentions.all().values_list('pk', flat=True))
            recipients = recipients - mentions
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class TaskNewCommentMention(BaseEventType):
    code: str = 'task_new_comments_mention'
    verbose_name: str = 'Упоминание в комментарии к задаче'
    verbose_name_kk: str = 'Тапсырмаға қалдырылған пікірде атап өту'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'tasks'
    is_mention: bool = True

    template_html = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к <strong>задаче</strong> ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}", "comment":true}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к задаче #{{subj.counter}} ' \
                    '"{{subj.name}}":\n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} сізді ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}", "comment":true}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}" </span> ' \
                       'тапсырмасына қалдырылған пікірде атап өтті: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} сізді #{{subj.counter}} «{{subj.name}}» ' \
                       'тапсырмасына қалдырылған пікірде атап өтті:\n {{obj.text}}'

    url = '{{urls.notifications}}?task={{subj.id}}&stab={{subj.task_type}}&comment=true'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj: TaskModel = None,
                            obj: CommentModel = None):
        recipients = set(list(obj.mentions.all()))
        if recipients:
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class TaskNewBlocker(BaseEventType):
    code: str = 'task_new_blocker'
    verbose_name: str = 'К задаче добавлен блокер'
    verbose_name_kk: str = 'Тапсырмаға блокер қосылды'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'tasks'

    template_html = '{{initiator.full_name}} добавил(-а) блокер ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.name}} ' \
                    '</blockquote>' \
                    'к <strong>задаче</strong> ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>'
    template_text = '{{initiator.full_name}} поставил(-а) блокер' \
                    '{{obj.name}} к задаче #{{subj.counter}} "{{subj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                        '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.name}} ' \
                        '</blockquote>' \
                        'блокерін ' \
                        '<span class="n_link" data-link-type="tasks"' \
                        ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                        'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                        '<strong>тапсырмасына</strong> қосты'
    template_text_kk = '{{initiator.full_name}} {{obj.name}} блокерін ' \
                        '#{{subj.counter}} "{{subj.name}}" тапсырмасына қосты'

    url = '{{urls.notifications}}?task={{subj.id}}&stab={{subj.task_type}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: TagModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj: TaskModel = None,
                            obj: TagModel = None):
        from bpms.tasks.notifications import get_task_participants, get_workgroup_founders_and_moderators
        recipients = get_task_participants(subj)
        recipients.update(get_workgroup_founders_and_moderators(subj))
        recipients.discard(initiator.pk)
        recipients.discard(None)
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class TaskRemoveBlocker(BaseEventType):
    code: str = 'task_remove_blocker'
    verbose_name: str = 'Из задачи удалён блокер'
    verbose_name_kk: str = 'Тапсырмадан блокер жойылды'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'tasks'

    template_html = '{{initiator.full_name}} удалил(-а) блокер ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.name}} ' \
                    '</blockquote>' \
                    'из <strong>задачи</strong> ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span>'
    template_text = '{{initiator.full_name}} удалил(-а) блокер' \
                    '{{obj.name}} из задачи #{{subj.counter}} "{{subj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                        '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.name}} ' \
                        '</blockquote>' \
                        'блокерін ' \
                        '<span class="n_link" data-link-type="tasks"' \
                        ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                        'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                        '<strong>тапсырмасынан</strong> жойды'
    template_text_kk = '{{initiator.full_name}} {{obj.name}} блокерін ' \
                        '#{{subj.counter}} "{{subj.name}}" тапсырмасынан жойды'

    url = '{{urls.notifications}}?task={{subj.id}}&stab={{subj.task_type}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: TagModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj: TaskModel = None,
                            obj: TagModel = None):
        from bpms.tasks.notifications import get_task_participants, get_workgroup_founders_and_moderators
        recipients = get_task_participants(subj)
        recipients.update(get_workgroup_founders_and_moderators(subj))
        recipients.discard(initiator.pk)
        recipients.discard(None)
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class TaskSetSprint(BaseEventType):
    code = 'set_task_in_sprint_notification'
    verbose_name: str = 'Ваша задача добавлена в спринт!'
    verbose_name_kk: str = 'Сіздің тапсырмаңыз спринтке қосылды!'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'tasks'
    template_html = '{{initiator.full_name}} добавил(-а) Вашу задачу ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    ' к спринту' \
                    '<span class="n_link" data-link-type="sprint" data-link-query=' \
                    '{"sprint":"{{obj.id}}"} ' \
                    'data-link-open="true"> "{{obj.name}}"</span>'
    template_text = '{{initiator.full_name}} добавил(-а) Вашу задачу #{{subj.counter}} "{{subj.name}}" к спринту "{{obj.name}}"'
    # Казахский
    template_html_kk = '{{initiator.full_name}} Сіздің ' \
                    '<span class="n_link" data-link-type="tasks"' \
                    ' data-link-query=\'{"task":"{{subj.id}}", "stab": "{{subj.task_type}}"}\' ' \
                    'data-link-open="true">#{{subj.counter}} "{{subj.name}}"</span> ' \
                    'тапсырмаңызды ' \
                    '<span class="n_link" data-link-type="sprint" data-link-query=' \
                    '{"sprint":"{{obj.id}}"} ' \
                    'data-link-open="true"> "{{obj.name}}"</span> спринтіне қосты.'
    template_text_kk = '{{initiator.full_name}} Сіздің #{{subj.counter}} "{{subj.name}}" тапсырмаңызды "{{obj.name}}" спринтіне қосты.'
    url = '{{urls.notifications}}?sprint={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TaskModel = None, obj: TaskSprintModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class NewsNewComment(BaseEventType):
    code: str = 'news_new_comment'
    verbose_name: str = 'Новый комментарий к новости'
    verbose_name_kk: str = 'Жаңалыққа жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'system'

    template_html = '{{initiator.full_name}} оставил(-а) комментарий к <strong>новости</strong> ' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query=\'{"newsItem":"{{subj.id}}"}\' ' \
                    'data-link-open="true">"{{subj.string_view}}"</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к новости  "{{subj.string_view}}": ' \
                    '{{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query=\'{"newsItem":"{{subj.id}}"}\' ' \
                    'data-link-open="true">"{{subj.string_view}}"</span> <strong>жаңалығына</strong> пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} "{{subj.string_view}}" жаңалығына пікір қалдырды:' \
                    '{{obj.text}}'
    url = '{{urls.dashboard}}?newsItem={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: NewsModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None,
                            subj: NewsModel = None,
                            obj: CommentModel = None):
        work_groups = subj.work_groups.filter(is_active=True)
        recipients = []
        for work_group in work_groups:
            recipients = recipients + [member.member for member in
                                       work_group.workgroupmembersmodel_set.select_related('member').filter(
                                           is_active=True, )]
        recipients = set(recipients)
        recipients.discard(subj.author)
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj,
                                           obj=obj)


class NewIndependentNewsCreated(BaseEventType):
    code: str = 'new_important_independent_news'
    verbose_name: str = 'Новая важная новостная публикация!'
    verbose_name_kk: str = 'Маңызды жаңа жаңалық жарияланды!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'system'
    template_html = '{{initiator.full_name}} добавил(-а) новую новостную публикацию! ' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>'
    template_text = '{{initiator.full_name}} добавил(-а) новую новостную публикацию!{{subj.string_view}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} жаңа жаңалық жариялады! ' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>'
    template_text_kk = '{{initiator.full_name}} жаңа жаңалық жариялады! {{subj.string_view}}'
    url = '{{urls.dashboard}}?newsItem={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: NewsModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class NewWorkgroupNewsCreated(BaseEventType):
    code: str = 'new_workgroup_news'
    verbose_name: str = 'Новость в команде'
    verbose_name_kk: str = 'Командадағы жаңалық'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'groups'
    subject_source = 'workgroup'
    template_html = '{{initiator.full_name}} добавил(-а) новостную публикацию в команду ' \
                    '<span class="n_link" data-link-type="groups" ' \
                    ' data-link-query={"viewGroup":"{{workgroup.id}}"}' \
                    ' data-link-open="true">{{workgroup.name}}</span>! ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} добавил(-а) новостную публикацию в команду {{workgroup.name}}! {{subj.string_view}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} командаға ' \
                    '<span class="n_link" data-link-type="groups" ' \
                    ' data-link-query={"viewGroup":"{{workgroup.id}}"}' \
                    ' data-link-open="true">{{workgroup.name}}</span> ' \
                    'жаңа жаңалық жариялады! ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} командаға {{workgroup.name}} жаңа жаңалық жариялады! {{subj.string_view}}'
    url = '{{urls.dashboard}}?newsItem={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: NewsModel = None, workgroup: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, workgroup=workgroup)


class NewProjectNewsCreated(BaseEventType):
    code: str = 'new_project_news'
    verbose_name: str = 'Новость в проекте'
    verbose_name_kk: str = 'Жоба жаңалықтары'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'projects'
    subject_source = 'workgroup'
    template_html = '{{initiator.full_name}} добавил(-а) новостную публикацию в проект ' \
                    '<span class="n_link" data-link-type="projects" ' \
                    ' data-link-query={"viewProject":"{{workgroup.id}}"}' \
                    ' data-link-open="true">{{workgroup.name}}</span>! ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} добавил(-а) новостную публикацию в проект {{workgroup.name}}! {{subj.string_view}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} жобаға ' \
                    '<span class="n_link" data-link-type="projects" ' \
                    ' data-link-query={"viewProject":"{{workgroup.id}}"}' \
                    ' data-link-open="true">{{workgroup.name}}</span>! ' \
                    'жаңа жаңалық жарияланымын қосты! ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">' \
                    '<span class="n_link" data-link-type="dashboard" data-link-query={"newsItem":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.string_view}}</span>' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} жобаға {{workgroup.name}} жаңа жаңалық жарияланымын қосты! {{subj.string_view}}'
    url = '{{urls.dashboard}}?newsItem={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: NewsModel = None, workgroup: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, workgroup=workgroup)


class InviteToMeeting(BaseEventType):
    code: str = 'meetings_invite_to_meeting_notify'
    verbose_name: str = 'Вас пригласили на собрание!'
    verbose_name_kk: str = 'Сізді жиналысқа шақырды!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'meetings'
    template_html = '{{initiator.full_name}} отправил(-а) вам приглашение на собрание ' \
                    '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.name}}</span>'
    template_text = '{{initiator.full_name}} отправил(-а) вам приглашение на собрание {{subj.name}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} сізге ' \
                    '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.name}}</span> жиналысына шақыру жолдады'
    template_text_kk = '{{initiator.full_name}} сізге {{subj.name}} жиналысына шақыру жолдады'
    url = '{{urls.notifications}}?meeting={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: PlannedMeetingModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class MeetingStart(BaseEventType):
    code: str = 'meetings_start_new_meeting_notification'
    verbose_name: str = 'Началось собрание!'
    verbose_name_kk: str = 'Жиналыс басталды!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'meetings'
    template_html = 'Началось собрание "{{subj.name}}" ' \
                    'Подключиться к <a href="{{subj.target}}" target="_blank">СОБРАНИЮ</a>'
    template_text = 'Началось собрание {{subj.name}}.'
    # Казахский
    template_html_kk = '"{{subj.name}}" жиналысы басталды ' \
                    'Жиналысқа қосылу <a href="{{subj.target}}" target="_blank">ЖИНАЛЫСҚА</a>'
    template_text_kk = '{{subj.name}} жиналысы басталды.'
    url = '{{subj.target}}'

    def collect_data(self, initiator: ProfileModel = None, subj: PlannedMeetingModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class CallStart(BaseEventType):
    code: str = 'call_start_notification'
    verbose_name: str = 'Начался звонок'
    verbose_name_kk: str = 'Қоңырау басталды'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'calls'
    subject_source = 'ticket'
    template_html = 'Входящий звонок от {{initiator.full_name}}' \
                    '{% if ticket %} по обращению ' \
                    '<span class="n_link" data-link-query=\'{"requestView":"{{ticket.id}}"}\' data-link-open="true">' \
                    '#{{ticket.number}} "{{ticket.name}}"</span>{% endif %}.'
    template_text = 'Входящий звонок от {{initiator.full_name}}' \
                    '{% if ticket %} по обращению #{{ticket.number}} "{{ticket.name}}"{% endif %}.'
    template_html_kk = '{{initiator.full_name}} пайдаланушысынан кіріс қоңырау' \
                       '{% if ticket %} <span class="n_link" data-link-query=\'{"requestView":"{{ticket.id}}"}\' data-link-open="true">' \
                       '#{{ticket.number}} "{{ticket.name}}"</span> өтініші бойынша{% endif %}.'
    template_text_kk = '{{initiator.full_name}} пайдаланушысынан кіріс қоңырау' \
                       '{% if ticket %} #{{ticket.number}} "{{ticket.name}}" өтініші бойынша{% endif %}.'
    url = '{% if ticket %}{{urls.notifications}}?requestView={{ticket.id}}{% endif %}'

    def collect_data(self, initiator: ProfileModel = None, subj: CallModel = None, ticket=None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, ticket=ticket)


class CallUpdated(BaseEventType):
    code: str = 'call_updated_notification'
    verbose_name: str = 'Изменился звонок'
    verbose_name_kk: str = 'Қоңырау күйі өзгерді'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'calls'
    subject_source = 'ticket'
    template_html = 'Входящий звонок от {{subj.initiator.full_name}} изменил статус на "{{subj.status.name}}"' \
                    '{% if ticket %} по обращению ' \
                    '<span class="n_link" data-link-query=\'{"requestView":"{{ticket.id}}"}\' data-link-open="true">' \
                    '#{{ticket.number}} "{{ticket.name}}"</span>{% endif %}.'
    template_text = 'Входящий звонок от {{subj.initiator.full_name}} изменил статус на "{{subj.status.name}}"' \
                    '{% if ticket %} по обращению #{{ticket.number}} "{{ticket.name}}"{% endif %}.'
    template_html_kk = '{{subj.initiator.full_name}} пайдаланушысынан кіріс қоңырау күйі "{{subj.status.name}}" болып өзгерді' \
                       '{% if ticket %} <span class="n_link" data-link-query=\'{"requestView":"{{ticket.id}}"}\' data-link-open="true">' \
                       '#{{ticket.number}} "{{ticket.name}}"</span> өтініші бойынша{% endif %}.'
    template_text_kk = '{{subj.initiator.full_name}} пайдаланушысынан кіріс қоңырау күйі "{{subj.status.name}}" болып өзгерді' \
                       '{% if ticket %} #{{ticket.number}} "{{ticket.name}}" өтініші бойынша{% endif %}.'
    url = '{% if ticket %}{{urls.notifications}}?requestView={{ticket.id}}{% endif %}'

    def collect_data(self, initiator: ProfileModel = None, subj: CallModel = None, ticket=None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, ticket=ticket)


class MeetingSetRecordReady(BaseEventType):
    code: str = 'meetings_set_record_ready'
    verbose_name: str = 'Готова видеозапись'
    verbose_name_kk: str = 'Бейнежазба дайын'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'meetings'
    template_html = 'Готова видеозапись собрания ' \
                    '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.name}}</span>'
    template_text = 'Готова видеозапись собрания {{subj.name}}'
    # Казахский
    template_html_kk = '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.name}}</span> ' \
                    'жиналысының бейнежазбасы дайын'
    template_text_kk = '{{subj.name}} жиналысының бейнежазбасы дайын'
    url = '{{urls.notifications}}?meeting={{subj.id}}'

    def collect_data(self, subj: PlannedMeetingModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(subj=subj)


class MeetingSummaryReady(BaseEventType):
    code: str = 'meetings_summary_ready'
    verbose_name: str = 'Саммари встречи готово'
    verbose_name_kk: str = 'Жиналыс саммари дайын'
    color: str = 'success'
    icon: str = 'file-text'
    category_code: str = 'meetings'
    template_html = 'Саммари встречи ' \
                    '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                    ' data-link-open="true">{{subj.name}}</span> готово'
    template_text = 'Саммари встречи {{subj.name}} готово'
    template_html_kk = '<span class="n_link" data-link-type="meetings" data-link-query={"meeting":"{{subj.id}}"}' \
                       ' data-link-open="true">{{subj.name}}</span> жиналысының саммари дайын'
    template_text_kk = '{{subj.name}} жиналысының саммари дайын'
    url = '{{urls.notifications}}?meeting={{subj.id}}'

    def collect_data(self, subj: PlannedMeetingModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(subj=subj)


class NewMemberInWorkGroup(BaseEventType):
    code: str = 'workgroup_new_member_notify'
    verbose_name: str = 'Новый участник в команде!'
    verbose_name_kk: str = 'Жұмыс тобына жаңа қатысушы!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'groups'
    subject_source = 'obj'
    template_html = 'В команду <span class="n_link" data-link-type="groups" ' \
                    'data-link-query={"viewGroup":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> вступил' \
                    ' новый участник {{subj.full_name}} '
    template_text = 'В команду {{obj.name}} вступил новый участник {{subj.full_name}}'
    # Казахский
    template_html_kk = '<span class="n_link" data-link-type="groups" ' \
                    'data-link-query={"viewGroup":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> ' \
                    'жұмыс тобына жаңа қатысушы {{subj.full_name}} қосылды'
    template_text_kk = '{{obj.name}} жұмыс тобына жаңа қатысушы {{subj.full_name}} қосылды'
    url = '{{urls.notifications}}?viewGroup={{obj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ProfileModel = None, obj: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class MemberRemovedFromWorkGroup(BaseEventType):
    code: str = 'workgroup_removed_member_notify'
    verbose_name: str = 'Рабочую группу покинул один из участников!'
    verbose_name_kk: str = 'Жұмыс тобынан бір қатысушы шықты!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'groups'
    subject_source = 'obj'
    template_html = 'Рабочую группу <span class="n_link" data-link-type="groups" ' \
                    'data-link-query={"viewGroup":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> покинул(-а)' \
                    ' {{initiator.full_name}} '
    template_text = 'Рабочую группу {{obj.name}} покинул(-а) {{initiator.full_name}}.'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="groups" ' \
                    'data-link-query={"viewGroup":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> жұмыс тобынан шықты'
    template_text_kk = '{{initiator.full_name}} {{obj.name}} жұмыс тобынан шықты.'
    url = '{{urls.notifications}}?viewGroup={{obj.id}}'

    def collect_data(self, initiator: ProfileModel = None, obj: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, obj=obj)


class NewMemberInProject(BaseEventType):
    code: str = 'new_member_in_project_notify'
    verbose_name: str = 'Новый участник в проекте!'
    verbose_name_kk: str = 'Жобада жаңа қатысушы!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'projects'
    subject_source = 'obj'
    template_html = 'В проект <span class="n_link" data-link-type="projects" ' \
                    'data-link-query={"viewProject":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> вступил(-а)' \
                    ' новый участник {{subj.full_name}}'
    template_text = 'В проект {{obj.name}} вступил(-а) новый участник {{subj.full_name}}'
    # Казахский
    template_html_kk = '<span class="n_link" data-link-type="projects" ' \
                    'data-link-query={"viewProject":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> жобасына жаңа қатысушы ' \
                    '{{subj.full_name}} қосылды'
    template_text_kk = '{{obj.name}} жобасына жаңа қатысушы {{subj.full_name}} қосылды'
    url = '{{urls.notifications}}?viewProject={{obj.id}}'
    def collect_data(self, initiator: ProfileModel = None, subj: ProfileModel = None, obj: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class MemberRemovedFromProject(BaseEventType):
    code: str = 'project_removed_member_notify'
    verbose_name: str = 'Проект покинул один из участников!'
    verbose_name_kk: str = 'Жобадан бір қатысушы шықты!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'projects'
    subject_source = 'obj'
    template_html = 'Проект <span class="n_link" data-link-type="projects" ' \
                    'data-link-query={"viewProject":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> покинул(-а)' \
                    ' {{initiator.full_name}}'
    template_text = 'Проект {{obj.name}} покинул(-а) {{initiator.full_name}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="projects" ' \
                    'data-link-query={"viewProject":"{{obj.id}}"}' \
                    ' data-link-open="true">{{obj.name}}</span> жобасынан шықты'
    template_text_kk = '{{initiator.full_name}} {{obj.name}} жобасынан шықты'
    url = '{{urls.notifications}}?viewProject={{obj.id}}'

    def collect_data(self, initiator: ProfileModel = None, obj: WorkgroupModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, obj=obj)


class GoodsOrderComment(BaseEventType):
    code: str = 'goods_order_new_comment'
    verbose_name: str = 'Новый комментарий к заказу'
    verbose_name_kk: str = 'Тапсырысқа жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'orders'
    template_html = '{{initiator.full_name}} оставил(-а) комментарий к <strong>заказу</strong> ' \
                    '<span class="n_link" data-link-type="orders"' \
                    ' data-link-query=\'{"order":"{{subj.id}}", "stab":"comments"}\' ' \
                    'data-link-open="true">#{{subj.counter}}</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к заказу #{{subj.counter}} {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="orders"' \
                    ' data-link-query=\'{"order":"{{subj.id}}", "stab":"comments"}\' ' \
                    'data-link-open="true">#{{subj.counter}}</span> <strong>тапсырысқа</strong> пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} #{{subj.counter}} тапсырысқа пікір қалдырды: {{obj.text}}'
    url = '{{urls.notifications}}?order={{subj.id}}&stab=comments'

    def collect_data(self, initiator: ProfileModel = None, subj: GoodsOrderModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None,
                            subj: GoodsOrderModel = None,
                            obj: CommentModel = None):
        contractor = subj.contractor
        if contractor:
            curator = getattr(contractor, 'curator', None)
        else:
            curator = None
        recipients = {subj.user}
        if curator:
            recipients.add(curator)
        recipients.discard(obj.author)
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class SetNewPassword(BaseEventType):
    code: str = 'password_changed'
    verbose_name: str = 'Пароль успешно изменен!'
    verbose_name_kk: str = 'Құпиясөз сәтті өзгертілді!'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'system'
    subject_source = None
    template_html = 'Пароль успешно изменен!'
    template_text = 'Пароль успешно изменен!'
    template_html_kk = 'Құпиясөз сәтті өзгертілді!'
    template_text_kk = 'Құпиясөз сәтті өзгертілді!'
    url = ''

    def collect_data(self, initiator: ProfileModel = None, collect_context: dict = None, **kwargs):
        return {"initiator": "empty"}


class ZipFileCreated(BaseEventType):
    code: str = 'zipfile_created'
    verbose_name: str = 'Архив каталога доступен для скачивания'
    verbose_name_kk: str = 'Каталог мұрағаты жүктеп алуға қолжетімді'
    color: str = 'success'
    icon: str = 'file-zip'
    category_code: str = 'system'
    subject_source = None
    template_html = '<p>Архив каталога <strong>\"{{folder_name}}\"</strong>:</p>' \
                    '<p style="padding: 10px 0;"><a class="ant-btn ant-btn-dashed ant-btn-sm" href="{{url}}">' \
                    '<i class="fi fi-rr-download mr-2"></i> Скачать архив {{file_size}}</a></p>' \
                    '<p class="text-xs">Архив доступен до {{expire}}.</p>'
    template_text = 'Архив каталога {{folder_name}}. \n размер: {{file_size}}. \nАрхив доступен до {{expire}}.'
    # Казахский
    template_html_kk = '<p><strong>\"{{folder_name}}\"</strong> каталогының мұрағаты:</p>' \
                    '<p style="padding: 10px 0;"><a class="ant-btn ant-btn-dashed ant-btn-sm" href="{{url}}">' \
                    '<i class="fi fi-rr-download mr-2"></i> Мұрағатты жүктеп алу {{file_size}}</a></p>' \
                    '<p class="text-xs">Мұрағат {{expire}} дейін қолжетімді.</p>'
    template_text_kk = '{{folder_name}} каталогының мұрағаты. \n Өлшемі: {{file_size}}. \nМұрағат {{expire}} дейін қолжетімді.'
    url = '{{url}}'

    def collect_data(self, url: str = '', folder_name: str = '', expire: str = '', file_size: str = '', collect_context: dict = None, **kwargs):
        return {'url': url, 'folder_name': folder_name, 'expire': expire, 'file_size': file_size}


class OrderStartForOrderUser(BaseEventType):
    code: str = 'order_start_user'
    verbose_name: str = 'Заказ передан на доставку'
    verbose_name_kk: str = 'Тапсырыс жеткізуге берілді'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Заказ <span class="n_link" data-link-type="orders"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> передан на доставку.</p>' \
                         '<p>Водитель: {{obj.operator.full_name}}. ' \
                         'Тел. <a href=tel:{{operator_phone}}>{{operator_phone}}</a>.</p>'
    template_text: str = 'Заказ {{subj.number_1c}} передан на доставку.\n ' \
                         'Водитель: {{obj.operator.full_name}}. Тел. {{operator_phone}}'
    # Казахский
    template_html_kk: str = '<p><span class="n_link" data-link-type="orders"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> тапсырысты жеткізуге берілді.</p>' \
                         '<p>Жеткізуші: {{obj.operator.full_name}}. ' \
                         'Тел. <a href=tel:{{operator_phone}}>{{operator_phone}}</a>.</p>'
    template_text_kk: str = '{{subj.number_1c}} тапсырысты жеткізуге берілді.\n ' \
                         'Жеткізуші: {{obj.operator.full_name}}. Тел. {{operator_phone}}'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, obj: TaskModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        data['operator_phone'] = obj.operator.phone
        data['order_user_phone'] = subj.user.phone
        return data


class OrderStartForDriver(BaseEventType):
    code: str = 'order_start_driver'
    verbose_name: str = 'Новая доставка'
    verbose_name_kk: str = 'Жаңа жеткізу'
    color: str = 'primary'
    icon: str = 'environment'
    category_code: str = 'orders'
    template_html: str = '<p>Новая доставка <span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{obj.id}}"}\' ' \
                         'data-link-open="true">#{{obj.counter}} "{{obj.name}}"</span>. ' \
                         'Заказ <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span>. </p>' \
                         '<p>Контактное лицо: {{subj.user.full_name}}. ' \
                         'Тел. <a href=tel:{{order_user_phone}}>{{order_user_phone}}</a>.</p>'

    template_text: str = 'Новая доставка #{{obj.counter}} {{obj.name}}\n' \
                         '{{url.notifications}}/?task={{obj.id}}. \n' \
                         'Заказ № {{subj.number_1c}} \n' \
                         'Контактное лицо: {{subj.user.full_name}} тел. {{order_user_phone}}.'
    # Казахский
    template_html_kk: str = '<p>Жаңа жеткізу <span class="n_link" data-link-type="logistic"' \
                         ' data-link-query=\'{"task":"{{obj.id}}"}\' ' \
                         'data-link-open="true">#{{obj.counter}} "{{obj.name}}"</span>. ' \
                         'Тапсырыс № <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span>. </p>' \
                         '<p>Байланыс тұлғасы: {{subj.user.full_name}}. ' \
                         'Тел. <a href=tel:{{order_user_phone}}>{{order_user_phone}}</a>.</p>'
    template_text_kk: str = 'Жаңа жеткізу #{{obj.counter}} {{obj.name}}\n' \
                         '{{url.notifications}}/?task={{obj.id}}. \n' \
                         'Тапсырыс № {{subj.number_1c}} \n' \
                         'Байланыс тұлғасы: {{subj.user.full_name}} тел. {{order_user_phone}}.'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, obj: TaskModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        data['operator_phone'] = obj.operator.phone
        data['order_user_phone'] = subj.user.phone
        return data


class OrderUpdate(BaseEventType):
    code: str = 'order_update'
    verbose_name: str = 'Заказ изменен'
    verbose_name_kk: str = 'Тапсырыс өзгертілді'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>{{initiator.full_name}} внес(-ла) изменения в заказ ' \
                         '<span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> для "{{subj.contractor.name}}" ' \
                         'на сумму {{subj.amount}}.</p>'
    template_text: str = '{{initiator.full_name}} внес(-ла) изменения в заказ № {{subj.number_1c}} \n' \
                         'для "{{subj.contractor.name}}" на сумму {{subj.amount}}.'
    # Казахский
    template_html_kk: str = '<p>{{initiator.full_name}} "{{subj.contractor.name}}" үшін {{subj.amount}} сомаға № ' \
                         '<span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> ' \
                         'тапсырысына өзгерістер енгізді </p>'
    template_text_kk: str = '{{initiator.full_name}} "{{subj.contractor.name}}" үшін {{subj.amount}} \n' \
                         'сомаға № {{subj.number_1c}} тапсырысына өзгерістер енгізді.'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class OrderDeliveryInTransit(BaseEventType):
    code: str = 'order_delivery_in_transit'
    verbose_name: str = 'Заказ в пути'
    verbose_name_kk: str = 'Тапсырма жолда'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Заказ <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> для "{{subj.contractor.name}}" ' \
                         'на сумму {{subj.amount}} <strong>в пути</strong>. Водитель {{initiator.full_name}}, ' \
                         'тел. <a href=tel:{{operator_phone}}>{{operator_phone}}</a></p>'
    template_text: str = 'Заказ  {{subj.number_1c}} \n' \
                         'для "{{subj.contractor.name}}" на сумму {{subj.amount}} в пути. ' \
                         'Водитель {{initiator.full_name}}, тел. {{operator_phone}}.'
    # Казахский
    template_html_kk: str = '<p>"{{subj.contractor.name}}" үшін № ' \
                         '<span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> ' \
                         'тапсырысы, сома: {{subj.amount}} <strong>жолда</strong>. Жеткізуші: {{initiator.full_name}}, ' \
                         'тел. <a href=tel:{{operator_phone}}>{{operator_phone}}</a></p>'
    template_text_kk: str = '"{{subj.contractor.name}}" үшін №{{subj.number_1c}} \n' \
                         'тапсырысы, сома: {{subj.amount}}, жолда. ' \
                         'Жеткізуші: {{initiator.full_name}}, тел. {{operator_phone}}.'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, obj: TaskModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        data['operator_phone'] = obj.operator.phone
        return data


class OrderDelivered(BaseEventType):
    code: str = 'order_delivered'
    verbose_name: str = 'Заказ доставлен'
    verbose_name_kk: str = 'Тапсырыс жеткізілді'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Заказ <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> для "{{subj.contractor.name}}" ' \
                         'на сумму {{subj.amount}}  доставлен.</p>'
    template_text: str = 'Заказ  {{subj.number_1c}} для "{{subj.contractor.name}}" на сумму {{subj.amount}} доставлен.'
    # Казахский
    template_html_kk: str = '<p>"{{subj.contractor.name}}" үшін №<span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> ' \
                         'тапсырысы, сома: {{subj.amount}},  жеткізілді.</p>'
    template_text_kk: str = '"{{subj.contractor.name}}" үшін №{{subj.number_1c}} тапсырысы, сома: {{subj.amount}}, жеткізілді.'

    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class OrderLogisticManager(BaseEventType):
    code: str = 'order_logistic_manager'
    verbose_name = 'Новый заказ (для менеджера логистики)'
    verbose_name_kk = 'Жаңа тапсырыс (логистика менеджері үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Новый заказ для отправки <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span>.</p>'
    template_text: str = 'Новый заказ для отправки {{subj.number_1c}}'
    # Казахский
    template_html_kk: str = '<p>Жіберуге арналған жаңа тапсырыс <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span>.</p>'
    template_text_kk: str = 'Жіберуге арналған жаңа тапсырыс {{subj.number_1c}}'

    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, initiator: ProfileModel, subj: GoodsOrderModel, obj: ProfileModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        return data


class OrderCreated(BaseEventType):
    code: str = 'order_created'
    verbose_name = 'Новый заказ (для сотрудников)'
    verbose_name_kk = 'Жаңа тапсырыс (қызметкерлер үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Новый заказ <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> для "{{subj.contractor.name}}" на сумму ' \
                         '{{subj.amount}}.</p>'
    template_text: str = 'Новый заказ {{subj.number_1c}} для "{{subj.contractor.name}}" на сумму {{subj.amount}}.'
    # Казахский
    template_html_kk: str = '<p>"{{subj.contractor.name}}" үшін <span class="n_link" data-link-type="notifications"' \
                         ' data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span> ' \
                         'жаңа тапсырыс, сома: {{subj.amount}}.</p>'
    template_text_kk: str = '"{{subj.contractor.name}}" үшін {{subj.number_1c}} жаңа тапсырыс, сома: {{subj.amount}}'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, subj: GoodsOrderModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class OrderCreatedCashPayRecipient(BaseEventType):
    code: str = 'order_created_cash_pay_recipient'
    verbose_name = 'Назначение получателем денежных средств'
    verbose_name_kk = 'Ақша қаражатын алушыны тағайындау'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'orders'
    template_html: str = '<p>Вы назначены получателем денежных средств по заказу ' \
                         '<span class="n_link" data-link-type="notifications" ' \
                         'data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span></p>' \
                         'для клиента "{{subj.contractor.name}}" на сумму {{subj.amount}}.'
    template_text: str = 'Вы назначены получателем денежных средств по заказу {{subj.number_1c}} ' \
                         'для "{{subj.contractor.name}}" на сумму {{subj.amount}}.'
    # Казахский
    template_html_kk: str = '<p>Сіз "{{subj.contractor.name}}" үшін {{subj.amount}} сомаға №' \
                         '<span class="n_link" data-link-type="notifications" ' \
                         'data-link-query=\'{"order":"{{subj.id}}"}\' ' \
                         'data-link-open="true">{{subj.number_1c}}</span></p>' \
                         'тапсырысы бойынша қаражат алушы ретінде тағайындалдыңыз.'
    template_text_kk: str = 'Сіз "{{subj.contractor.name}}" үшін {{subj.amount}} сомаға №{{subj.number_1c}} ' \
                         'тапсырысы бойынша қаражат алушы ретінде тағайындалдыңыз.'
    url: str = '{{urls.notifications}}?order={{subj.id}}'

    def collect_data(self, subj: GoodsOrderModel, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


# class WorkgroupChangeRole(BaseEventType):
#     """
#     Смена роли в рабочей группе.
#     """
#     code: str = 'workgroup_change_role'
#     verbose_name: str = 'Смена роли в рабочей группе'
#     color: str = 'default'
#     icon: str = 'profile'
#
#     def get_message(self, *args, **kwargs):
#         return _("{initiator_name} в рабочей группе {subj_name} сменил Вам роль. Новая роль: {obj_name}.").format(
#             initiator_name=self.get_initiator_name(),
#             subj_name=self.get_subj_name(),
#             obj_name=self.get_obj_name(),
#         )
#     def create_notification(self, recipients: set, initiator: ProfileModel, subj: WorkgroupModel,
#                             obj: WorkgroupMembershipRole):
#         from .models import WebNotificationModel
#         with atomic():
#             notification = WebNotificationModel.objects.create(
#                 event_type=self.code,
#                 data=self.get_data(initiator=initiator, subj=subj, obj=obj),
#             )
#         notification.recipients.set(recipients)
#         notification.send_message_about_new_notify()
#         return notification
#
#
# class WorkGroupKick(BaseEventType):
#     """
#     Исключение из рабочей группы.
#     """
#     code: str = 'workgroup_kick'
#     verbose_name: str = 'Исключение из рабочей группы'
#     color: str = 'error'
#     icon: str = 'team'
#
#     def get_message(self, *args, **kwargs):
#         return _("{initiator_name} исключил Вас из рабочей группы {subj_name}.").format(
#             initiator_name=self.get_initiator_name(),
#             subj_name=self.get_subj_name(),
#         )
#
#     def create_notification(self, recipients: set, initiator: ProfileModel, subj: WorkgroupModel):
#         from .models import WebNotificationModel
#         notification = WebNotificationModel.objects.create(
#             event_type=self.code,
#             data=self.get_data(initiator=initiator, subj=subj)
#         )
#         notification.recipients.set(recipients)
#         notification.send_message_about_new_notify()
#         return notification


class New1CTicketEvent(BaseEventType):
    """
    Новая заявка на аренду сервера 1С
    """
    code: str = 'new_1c_ticket_event'
    verbose_name: str = 'Новая заявка на аренду сервера 1С'
    verbose_name_kk: str = '1С серверін жалға алуға жаңа өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'my-bases'
    template_html = '{{initiator.full_name}} отправил(-а) ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' '\
                    'data-link-open="true">заявку</span> на аренду сервера 1С.'
    template_text = '{{initiator.full_name}} отправил(-а) заявку на {{subj.connection_option}}, тариф - {{subj.tarif}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} 1С серверін жалға алуға ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' '\
                    'data-link-open="true">өтінім</span> жіберді.'
    template_text_kk = '{{initiator.full_name}} {{subj.connection_option}} бойынша өтінім жіберді, тариф - {{subj.tarif}}'
    url = '{{urls.notifications}}?ticket={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TicketModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class Ticket1CHasApprovedEvent(BaseEventType):
    """
    Заявка на аренду сервера 1С одобрена
    """
    code: str = 'new_1c_ticket_has_approved'
    verbose_name: str = 'Заявка на аренду сервера 1С одобрена'
    verbose_name_kk: str = '1С серверін жалға алуға өтінім мақұлданды'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'my-bases'
    template_html = '{{initiator.full_name}} одобрил(-а) <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' ' \
                    'data-link-open="true">заявку</span> на аренду сервера 1С.'

    template_text = '{{initiator.full_name}} одобрил(-а) заявку на аренду сервера 1С.'
    # Казахский
    template_html_kk = '{{initiator.full_name}} 1С серверін жалға алуға <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' ' \
                    'data-link-open="true">өтінімді</span> мақұлдады.'

    template_text_kk = '{{initiator.full_name}} 1С серверін жалға алуға өтінімді мақұлдады.'
    url = '{{urls.notifications}}?ticket={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TicketModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class Ticket1CHasRejectedEvent(BaseEventType):
    """
    Заявка на аренду сервера 1С отклонена
    """
    code: str = 'new_1c_ticket_has_rejected'
    verbose_name: str = 'Заявка на аренду сервера 1С отклонена'
    verbose_name_kk: str = '1С серверін жалға алуға өтінім қабылданбады'
    color: str = 'warning'
    icon: str = 'info'
    category_code: str = 'my-bases'
    template_html = '{{initiator.full_name}} отклонил(-а) <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' ' \
                    'data-link-open="true">заявку</span> на аренду сервера 1С.'

    template_text = '{{initiator.full_name}} отклонил(-а) заявку на аренду сервера 1С'
    # Казахский
    template_html_kk = '{{initiator.full_name}} 1С серверін жалға алуға <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"ticket": "{{subj.id}}"}\' ' \
                    'data-link-open="true">өтінімді</span> қабылдамады.'

    template_text_kk = '{{initiator.full_name}} 1С серверін жалға алуға өтінімді қабылдамады'
    url = '{{urls.notifications}}?ticket={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: TicketModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


# Приглашения на связь между организациями
class InviteContractor(BaseEventType):
    """
    Приглашение на связь между организациями.
    """
    code: str = 'invite_contractor'
    verbose_name: str = 'Приглашение'
    verbose_name_kk: str = 'Шақыру'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = '{{initiator.full_name}} от лица организации "{{subj.contractor_owner.name}}"' \
                    ' <span class="n_link" data-link-type="organization_invite" ' \
                    'data-link-query=\'{"orginvite":"{{subj.id}}"}\' data-link-open="true"> ' \
                    'приглашает Вашу организацию </span> "{{subj.contractor_notify.name}}" ' \
                    'в качестве {{subj.relation_notify}}.'

    template_text = '{{initiator.full_name}} от лица организации \"{{subj.contractor_owner.name}}\" ' \
                    'приглашает Вашу организацию \"{{subj.contractor_notify.name}}\" в качестве ' \
                    '{{subj.relation_notify}}.'
    # Казахский
    template_html_kk = '{{initiator.full_name}} "{{subj.contractor_owner.name}}"' \
                    ' <span class="n_link" data-link-type="organization_invite" ' \
                    'data-link-query=\'{"orginvite":"{{subj.id}}"}\' data-link-open="true"> ' \
                    'ұйымы атынан сіздің </span> \"{{subj.contractor_notify.name}}\" ' \
                    'ұйымыңызды {{subj.relation_notify}} ретінде қатысуға шақырады.'
    template_text_kk = '{{initiator.full_name}} "{{subj.contractor_owner.name}}" ' \
                    'ұйымы атынан сіздің \"{{subj.contractor_notify.name}}\" ұйымыңызды ' \
                    '{{subj.relation_notify}} ретінде қатысуға шақырады.'
    url = '{{urls.notifications}}?orginvite={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ContractorInviteModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class InviteContractorAccept(BaseEventType):
    """
    Приглашение принято.
    """
    code: str = 'invite_contractor_accept'
    verbose_name: str = 'Приглашение принято'
    verbose_name_kk: str = 'Шақыру қабылданды'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = 'Организация "{{subj.contractor_notify.name}}" приняла приглашение от Вашей организации ' \
                    '"{{subj.contractor_owner.name}}" в качестве {{subj.relation_notify}}.'
    template_text = 'Организация "{{subj.contractor_notify.name}}" приняла приглашение от Вашей организации ' \
                    '"{{subj.contractor_owner.name}}" в качестве {{subj.relation_notify}}.'
    # Казахский
    template_html_kk = '"{{subj.contractor_notify.name}}" ұйымы сіздің ' \
                    '"{{subj.contractor_owner.name}}" ұйымыңыздан {{subj.relation_notify}} ретінде шақыруды қабылдады.'
    template_text_kk = '"{{subj.contractor_notify.name}}" ұйымы сіздің ' \
                    '"{{subj.contractor_owner.name}}" ұйымыңыздан {{subj.relation_notify}} ретінде шақыруды қабылдады.'
    url = ''

    def collect_data(self, subj: ContractorInviteModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class InviteContractorReject(BaseEventType):
    """
    Приглашение отклонено.
    """
    code: str = 'invite_contractor_reject'
    verbose_name: str = 'Приглашение отклонено'
    verbose_name_kk: str = 'Шақыру қабылданбады'
    color: str = 'danger'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = 'Организация "{{subj.contractor_notify.name}}" отказалась от приглашения Вашей организации ' \
                    '"{{subj.contractor_owner.name}}" в качестве {{subj.relation_notify}}.'
    template_text = 'Организация "{{subj.contractor_notify.name}}" отказалась от приглашения Вашей организации ' \
                    '"{{subj.contractor_owner.name}}" в качестве {{subj.relation_notify}}.'
    # Казахский
    template_html_kk = '"{{subj.contractor_notify.name}}" ұйымы сіздің ' \
                    '"{{subj.contractor_owner.name}}" ұйымыңыздың {{subj.relation_notify}} ретінде шақыруынан бас тартты.'
    template_text_kk = '"{{subj.contractor_notify.name}}" ұйымы сіздің ' \
                    '"{{subj.contractor_owner.name}}" ұйымыңыздың {{subj.relation_notify}} ретінде шақыруынан бас тартты.'
    url = ''

    def collect_data(self, subj: ContractorInviteModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class OrganizationNewMember(BaseEventType):
    """
    Новый участник организации.
    """
    code: str = 'org_new_member'
    verbose_name: str = 'Новый участник организации'
    verbose_name_kk: str = 'Ұйымның жаңа қатысушысы'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = '{{subj.user.full_name}} стал(-а) новым участником организации ' \
                    '<span class="n_link" data-link-type="organization" ' \
                    'data-link-query=\'{"organization_id":"{{subj.contractor.id}}", "organization_drawer":"detail"}\'' \
                    'data-link-open="true">\"{{subj.contractor.name}}\"</span> и получил статус "Гость". ' \
                    'Необходимо назначить группу доступа для нового сотрудника'
    template_text = '{{subj.user.full_name}} стал(-а) новым участником организации {{subj.contractor.name}}.'
    # Казахский
    template_html_kk = '{{subj.user.full_name}} ' \
                    '<span class="n_link" data-link-type="organization" ' \
                    'data-link-query=\'{"organization_id":"{{subj.contractor.id}}", "organization_drawer":"detail"}\'' \
                    'data-link-open="true">\"{{subj.contractor.name}}\"</span>.' \
                    'ұйымының жаңа қатысушысы болды'  # TODO нужен новый перевод
    template_text_kk = '{{subj.user.full_name}} {{subj.contractor.name}} ұйымының жаңа қатысушысы болды.'
    url = '{{urls.team}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class UserNewMemberOrganization(BaseEventType):
    """
    Новому участнику организации, зарегистрированному по инвайту
    """
    code: str = 'user_new_member_org'
    verbose_name: str = 'Добро пожаловать'
    verbose_name_kk: str = 'Қош келдіңіз'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = 'Вы зарегистрировались по приглашению как <b>"Гость"</b> - пока у вас доступ только к профилю, ' \
                    'справке и поддержке. Скоро админ вашей организации назначит вам роль для начала работы ' \
                    'в организации'

    template_text = 'Вы зарегистрировались по приглашению как "Гость" - пока у вас доступ только к профилю, ' \
                    'справке и поддержке. Скоро админ вашей организации назначит вам роль для начала работы ' \
                    'в организации'
    # Казахский
    template_html_kk = 'Сіз шақыру арқылы «Қонақ» ретінде тіркелдіңіз — қазіргі уақытта тек профильге, ' \
                       'анықтамаға және қолдауға ғана қолжетімділігіңіз бар. Жақын арада ұйымыңыздың әкімшісі жұмысты ' \
                       'бастау үшін сізге рөл тағайындайды'
    template_text_kk = 'Сіз шақыру арқылы «Қонақ» ретінде тіркелдіңіз — қазіргі уақытта тек профильге, ' \
                       'анықтамаға және қолдауға ғана қолжетімділігіңіз бар. Жақын арада ұйымыңыздың әкімшісі жұмысты ' \
                       'бастау үшін сізге рөл тағайындайды'
    url = '{{urls.team}}'


class OrganizationLeaveMember(BaseEventType):
    """
    Участник покинул организацию.
    """
    code: str = 'ort_leave_member'
    verbose_name: str = 'Участник покинул организацию'
    verbose_name_kk: str = 'Қатысушы ұйымнан кетті'
    color: str = 'danger'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = '{{initiator.full_name}} покинул(-а) организацию ' \
                    '<span class="n_link" data-link-type="organization" ' \
                    'data-link-query=\'{"organization_id":"{{subj.id}}", "organization_drawer":"detail"}\'' \
                    'data-link-open="true">\"{{subj.name}}\"</span>.'
    template_text = '{{initiator.full_name}} покинул(-а) организацию {{subj.name}}.'

    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="organization" ' \
                    'data-link-query=\'{"organization_id":"{{subj.id}}", "organization_drawer":"detail"}\'' \
                    'data-link-open="true">\"{{subj.name}}\"</span> ұйымынан шықты.'
    template_text_kk = '{{initiator.full_name}} {{subj.name}} ұйымынан шықты.'
    url = '{{urls.team}}'

    def collect_data(self, initiator, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class OrganizationDeleteMember(BaseEventType):
    """
    Пользователя исключили из организации.
    """
    code: str = 'org_delete_member'
    verbose_name: str = 'Пользователя исключили из организации'
    verbose_name_kk: str = 'Пайдаланушы ұйымнан шығарылды'
    color: str = 'danger'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html: str = 'Вас исключили из организации "{{subj.name}}".'
    template_text: str = 'Вас исключили из организации "{{subj.name}}".'
    # Казахский
    template_html_kk: str = 'Сіз "{{subj.name}}" ұйымынан шығарылдыңыз.'
    template_text_kk: str = 'Сіз "{{subj.name}}" ұйымынан шығарылдыңыз.'
    url = ''

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


# Уведомление о предстоящем событии кландаря
class EventCalendarMention(BaseEventType):
    """
    Напоминание о предстоящем событии календаря.
    """
    code: str = 'event_calendar_mention'
    verbose_name: str = 'Напоминание о событии'
    verbose_name_kk: str = 'Оқиғаны еске салу'
    color: str = 'primary'
    icon: str = 'schedule'
    category_code: str = 'calendar'
    is_personalized_notification: bool = True
    template_html = '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    'Событие "{{subj.name}}"</span>. Дата начала: {{subj.start_at_humanized}}. ' \
                    'Организатор: {{subj.author.full_name}}'
    template_text = 'Напоминание о предстоящем событии: \"{{subj.name}}\". Дата начала: {{subj.start_at_humanized}}.' \
                    ' Организатор: {{subj.author.full_name}}.'
    # Казахский
    template_html_kk = '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    'Алдағы оқиға туралы еске салу: "{{subj.name}}"</span>. Басталу күні: {{subj.start_at_humanized}}. ' \
                    'Организатор: {{subj.author.full_name}}'
    template_text_kk = 'Алдағы оқиға туралы еске салу: \"{{subj.name}}\". Басталу күні: {{subj.start_at_humanized}}.' \
                    ' Ұйымдастырушы: {{subj.author.full_name}}.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def get_collect_context(self, recipient: ProfileModel = None, **kwargs) -> dict:
        if recipient is None:
            return dict()
        return {'timezone_code': recipient.timezone}

    def collect_data(self, subj=None, collect_context: dict = None, **kwargs):
        data = super().collect_data(collect_context=collect_context, subj=subj)
        return data


class EventCalendarCreate(BaseEventType):
    """
    Уведомление мембера о новом событии.
    """
    code: str = 'event_calendar_create'
    verbose_name: str = 'Новое событие'
    verbose_name_kk: str = 'Жаңа оқиға'
    color: str = 'primary'
    icon: str = 'calendar'
    category_code: str = 'calendar'
    is_personalized_notification: bool = True
    template_html = 'Новое событие: <span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span>. Дата начала: {{subj.start_at_humanized}}. ' \
                    'Организатор: {{subj.author.full_name}}'
    template_text = 'Новое событие: \"{{subj.name}}\". Дата начала: {{subj.start_at_humanized}}.' \
                    ' Организатор: {{subj.author.full_name}}.'
    # Казахский
    template_html_kk = 'Жаңа оқиға: <span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span>. Басталу күні: {{subj.start_at_humanized}}. ' \
                    'Ұйымдастырушы: {{subj.author.full_name}}'
    template_text_kk = 'Жаңа оқиға: \"{{subj.name}}\". Басталу күні: {{subj.start_at_humanized}}.' \
                    ' Ұйымдастырушы: {{subj.author.full_name}}.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def get_collect_context(self, recipient: ProfileModel = None, **kwargs) -> dict:
        if recipient is None:
            return dict()
        return {'timezone_code': recipient.timezone}

    def collect_data(self, subj=None, collect_context: dict = None, **kwargs):
        data = super().collect_data(collect_context=collect_context, subj=subj)
        return data


class EventCalendarEscape(BaseEventType):
    """Уведомление об отказе от события."""
    code: str = 'event_calendar_escape'
    verbose_name = 'Отказ от события'
    verbose_name_kk = 'Оқиғадан бас тарту'
    color: str = 'danger'
    icon: str = 'calendar'
    category_code: str = 'calendar'
    template_html = '{{obj.full_name}} отказался(-лась) от участия в событии: <span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span>.'
    template_text = '{{obj.full_name}} отказался(-лась) от участия в событии: \"{{subj.name}}\"'
    # Казахский
    template_html_kk = '{{obj.full_name}} <span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span> іс-шарасына қатысудан бас тартты'
    template_text_kk = '{{obj.full_name}} "{{subj.name}}" іс-шарасына қатысудан бас тартты'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class EventCalendarChangeDates(BaseEventType):
    """Уведомление об изменении даты события."""
    code: str = 'event_calendar_change_dates'
    verbose_name: str = 'Изменение даты начала события'
    verbose_name_kk: str = 'Оқиғаның басталу күнін өзгерту'
    color: str = 'warning'
    icon: str = 'calendar'
    category_code: str = 'calendar'
    is_personalized_notification: bool = True
    template_html = '{{obj.full_name}} <strong>перенес(-ла) событие</strong> ' \
                    '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span> на <strong>{{subj.start_at_humanized}}</strong>.'
    template_text = '{{obj.full_name}} перенес(-ла) событие {{subj.name}} на ' \
                    '{{subj.start_at_humanized}}.'
    # Казахский
    template_html_kk = '{{obj.full_name}} ' \
                    '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span> іс-шарасын <strong>{{subj.start_at_humanized}}</strong> уақытына шегерді.'
    template_text_kk = '{{obj.full_name}} {{subj.name}} іс-шарасын ' \
                    '{{subj.start_at_humanized}} уақытына шегерді.'

    url = '{{urls.notifications}}?event={{subj.id}}'

    def get_collect_context(self, recipient: ProfileModel = None, **kwargs) -> dict:
        if recipient is None:
            return dict()
        return {'timezone_code': recipient.timezone}

    def collect_data(self, subj=None, obj=None, collect_context: dict = None, **kwargs):
        data = super().collect_data(collect_context=collect_context, subj=subj, obj=obj)
        return data


class EventCalendarComment(BaseEventType):
    code: str = 'event_calendar_new_comment'
    verbose_name: str = 'Новый комментарий к событию'
    verbose_name_kk: str = 'Оқиғаға жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'calendar'
    template_html = '{{initiator.full_name}} оставил(-а) комментарий к <strong>событию</strong> ' \
                    '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к событию {{subj.name}}: \n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="event" ' \
                    'data-link-query=\'{"event":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.name}}"</span> <strong>іс-шарасына</strong> пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text_kk = '{{initiator.full_name}} {{subj.name}} іс-шарасына пікір қалдырды: \n {{obj.text}}'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: EventCalendarModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None,
                            subj: EventCalendarModel = None,
                            obj: CommentModel = None):
        recipients = set(subj.members.all())
        recipients.add(subj.author)
        recipients.discard(None)
        recipients.discard(obj.author)
        if recipients:
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


# Уведомления консолидации
class ReportHasApprovedEvent(BaseEventType):
    """
    Отчет организации утвержден
    """
    code: str = 'report_has_approved'
    verbose_name: str = 'Отчет организации утвержден'
    verbose_name_kk: str = 'Ұйымның есебі бекітілді'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} утвердил(-а) <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"report": "{{subj.id}}"}\' data-link-open="true">отчет {{subj.str_view}}</span>'

    template_text = '{{initiator.full_name}} утвердил(-а) отчет {{subj.str_view}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} {{subj.str_view}} <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"report": "{{subj.id}}"}\' data-link-open="true">есебін бекітті</span>'

    template_text_kk = '{{initiator.full_name}} {{subj.str_view}} есебін бекітті'
    url = '{{urls.notifications}}?report={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ReportModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class ReportHasRejectedEvent(BaseEventType):
    """
    Отчет организации направлен на доработку
    """
    code: str = 'report_has_rejected'
    verbose_name: str = 'Отчет направлен на доработку'
    verbose_name_kk: str = 'Есеп пысықтауға бағытталған'
    color: str = 'warning'
    icon: str = 'info'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} направил(-а) <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"report": "{{subj.id}}"}\' data-link-open="true">отчет {{subj.str_view}}' \
                    '</span> на доработку'
    template_text = '{{initiator.full_name}} направил(-а) отчет {{subj.str_view}} на доработку.'

    # Казахский
    template_html_kk = '{{initiator.full_name}} {{subj.str_view}} <span class="n_link" data-link-type="notifications" '\
                    'data-link-query=\'{"report": "{{subj.id}}"}\' data-link-open="true">есебін ' \
                    '</span> есебін пысықтауға жіберді'

    template_text_kk = '{{initiator.full_name}} {{subj.str_view}} есебін пысықтауға жіберді'
    url = '{{urls.notifications}}?report={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ReportModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class AllReportsAreUploadedEvent(BaseEventType):
    """
    Загружены все файлы отчетов консолидации
    """
    code: str = 'all_reports_are_uploaded'
    verbose_name: str = 'Загружены все файлы отчетов консолидации'
    verbose_name_kk: str = 'Барлық біріктіру есебі файлдары жүктелді'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'consolidation'
    template_html = 'Все отчеты консолидации "<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">{{subj.name}}"</span> '\
                    'загружены'

    template_text = 'Все отчеты консолидации {{subj.name}}"загружены.'

    # Казахский
    template_html_kk = '"<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">{{subj.name}}"</span> '\
                    'біріктіру есептерінің барлығы жүктелді'
    template_text_kk = '{{subj.name}} біріктіру есептерінің барлығы жүктелді'
    url = '{{urls.notifications}}?consolidation={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ConsolidationModel = None, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj)
        return data


class ConsolidationReportComment(BaseEventType):
    code: str = 'consolidation_report_new_comment'
    verbose_name: str = 'Новый комментарий к отчёту'
    verbose_name_kk: str = 'Есепке жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} оставил(-а) комментарий к ' \
                    '<span class="n_link" data-link-type="notifications" data-link-query=\'{"report": "{{subj.id}}"}\' ' \
                    'data-link-open="true">отчету {{subj.str_view}}</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к отчёту {{subj.str_view}}: {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="notifications" data-link-query=\'{"report": "{{subj.id}}"}\' ' \
                    'data-link-open="true"> қалдырды {{subj.str_view}}</span> есебіне пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text_kk = '{{initiator.full_name}} {{subj.str_view}} есебіне пікір қалдырды: {{obj.text}}'
    url = '{{urls.notifications}}?report={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ReportModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(),
                            initiator: ProfileModel = None,
                            subj: ReportModel = None,
                            obj: CommentModel = None):
        from contractor_permissions.models import ContractorPermissionModel
        from django.db.models import Q
        contractor = subj.parent.org_administrator
        report_form = subj.parent.report_form
        recipients = set(ContractorPermissionModel.objects.filter(
                (Q(aux_conditions=report_form) | Q(aux_conditions__isnull=True)),
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor=contractor,
                permission_type_id__in=['create_consolidation', 'send_report'],
            ).values_list(
                'contractor_permission_role__contractor_profiles__user',
                flat=True
            ))
        recipients.discard(obj.author.id)
        if recipients:
            return super().create_notification(
                recipients=tuple(recipients),
                initiator=initiator,
                subj=subj,
                obj=obj
            )


class ConsolidationComment(BaseEventType):
    code: str = 'consolidation_new_comment'
    verbose_name: str = 'Новый комментарий к консолидации'
    verbose_name_kk: str = 'Біріктіруге жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} оставил(-а) комментарий к ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' ' \
                    'data-link-open="true">консолидации {{subj.name}}</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к консолидации {{subj.name}}: \n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' ' \
                    'data-link-open="true">{{subj.name}} біріктіруге</span> пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text_kk = '{{initiator.full_name}} {{subj.name}} біріктіруге пікір қалдырды: \n {{obj.text}}'

    url = '{{urls.notifications}}?consolidation={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ConsolidationModel = None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None,
                            subj: ConsolidationModel = None,
                            obj: CommentModel = None):
        from contractor_permissions.models import ContractorPermissionModel
        from django.db.models import Q
        members = subj.members.all()
        report_form = subj.report_form
        recipients = set(ContractorPermissionModel.objects.filter(
                (Q(aux_conditions=report_form) | Q(aux_conditions__isnull=True)),
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor__in=members,
                permission_type_id__in=['create_consolidation', 'send_report'],
            ).values_list(
                'contractor_permission_role__contractor_profiles__user',
                flat=True
            ))
        recipients.add(subj.author.id)
        recipients.discard(None)
        recipients.discard(obj.author.id)
        if recipients:
            return super().create_notification(recipients=recipients, initiator=initiator, subj=subj, obj=obj)


class ConsolidationIsCompleteEvent(BaseEventType):
    code: str = 'consolidation_is_complete'
    verbose_name: str = 'Консолидация успешно завершена'
    verbose_name_kk: str = 'Біріктіру сәтті аяқталды'
    color: str = 'success'
    icon: str = 'info'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} завершил(-а) консолидацию ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">"{{subj.name}}"</span>'
    template_text = '{{initiator.full_name}} завершил(-а) консолидацию {{subj.name}}.'

    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">"{{subj.name}}" біріктіруді</span> аяқтады'
    template_text_kk = '{{initiator.full_name}} {{subj.name}} біріктіруді аяқтады'

    url = '{{urls.notifications}}?consolidation={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ConsolidationModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)

    def create_notification(self,
                            recipients: tuple = tuple(),
                            initiator: ProfileModel = None,
                            subj: ConsolidationModel = None):
        reports = set(subj.source_reports.filter(
            is_active=True
        ))
        recipients = set()
        for report in reports:
            report_files = report.report_files.all()
            for report_file in report_files:
                recipients.add(report_file.uploaded_by)
        recipients.discard(None)
        if recipients:
            return super().create_notification(
                recipients=recipients,
                initiator=initiator,
                subj=subj
            )


class NewConsolidationIsCreateEvent(BaseEventType):
    code: str = 'new_consolidation_is_create'
    verbose_name: str = 'Создана новая консолидация'
    verbose_name_kk: str = 'Жаңа біріктіру құрылды'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'consolidation'
    template_html = '{{initiator.full_name}} создал(-а) новую консолидацию ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">"{{subj.name}}"</span>'
    template_text = '{{initiator.full_name}} создал(-а) новую консолидацию {{subj.name}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="notifications" ' \
                    'data-link-query=\'{"consolidation": "{{subj.id}}"}\' data-link-open="true">"{{subj.name}}" атты жаңа біріктіруді</span> құрды'
    template_text_kk = '{{initiator.full_name}} {{subj.name}} атты жаңа біріктіруді құрды'

    url = '{{urls.notifications}}?consolidation={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj: ConsolidationModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)

    def create_notification(
            self,
            recipients: tuple = tuple(),
            initiator: ProfileModel = None,
            subj: ConsolidationModel = None):
        if recipients:
            return super().create_notification(
                recipients=recipients,
                initiator=initiator,
                subj=subj
            )


class RequestJoinToOrganization(BaseEventType):
    code: str = 'request_join_org'
    verbose_name: str = 'Запрос на добавление в организацию'
    verbose_name_kk: str = 'Ұйымға қосылу сұранысы'
    color: str = 'error'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = 'От пользователя {{subj.user.email}} поступила ' \
                    '<span class="n_link" data-link-type="moderation">заявка на модерацию' \
                    '</span>.'
    template_text = 'От пользователя {{subj.user.email}} поступила заявка на модерацию. ' \
                    'Организация {{subj.organization.name}}. ' \
                    'Ссылка: {{urls.moderation}}.'
    # Казахский
    template_html_kk = '{{subj.user.email}} пайдаланушысынан модерацияға ' \
                    '<span class="n_link" data-link-type="moderation">өтінім келіп түсті' \
                    '</span>'
    template_text_kk = '{{subj.user.email}} пайдаланушысынан модерацияға өтінім келіп түсті.' \
                    'Ұйым: {{subj.organization.name}}. ' \
                    'Сілтеме: {{urls.moderation}}.'
    url = '{{urls.moderation}}'

    def collect_data(self, subj=None, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class DIDSignEvent(BaseEventType):
    code: str = 'url_for_sign'
    verbose_name: str = 'Задание на подпись документа'
    verbose_name_kk: str = 'Құжатқа қол қою тапсырмасы'
    color: str = 'default'
    icon: str = 'info'
    category_code: str = 'tasks'
    subject_source = None
    template_html = 'Подпишите документ {{ subj.title }} по <a href={{subj.url}}>ссылке</a>. '
    template_text = 'Подпишите документ {{ subj.title }} по ссылке '
    # Казахский
    template_html_kk = '<a href={{subj.url}}>сілтеме</a> арқылы {{subj.title}} құжатына қол қойыңыз'
    template_text_kk = '{{ subj.title }} құжатына сілтеме арқылы қол қойыңыз'

    url = '{{subj.url}}'

    def collect_data(self, subj=None, collect_context: dict = None, **kwargs):
        return {'subj': subj}


# Смена статусов инвестпроектов.
class InvestProjectChangeStatusOnCheck(BaseEventType):
    """
    Смена статуса инвестпроекта: "на проверке"
    """
    code: str = 'invest_project_changed_status_on_check'
    verbose_name: str = 'Смена статуса инвестпроекта: "на проверке"'
    verbose_name_kk: str = 'Инвестициялық жобаның күйі өзгертілді: "тексерілуде"'
    color: str = 'success'
    icon: str = 'profile'
    category_code: str = 'invest-project'
    template_html = '{{initiator.full_name}} отправил(-а) на проверку инвестпроект ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span>.'
    template_text = '{{initiator.full_name}} отправил(-а) на проверку инвестпроект "{{subj.project_name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span> инвестициялық жобасын тексерілуге жіберді'
    template_text_kk = '{{initiator.full_name}} "{{subj.project_name}}" инвестициялық жобасын тексерілуге жіберді'

    def collect_data(self, initiator: ProfileModel = None, subj: InvestProjectInfoModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class InvestProjectChangeStatusOnRework(BaseEventType):
    """
    Смена статуса инвестпроекта: "на доработке"
    """
    code: str = 'invest_project_changed_status_on_rework'
    verbose_name: str = 'Смена статуса инвестпроекта: "на доработке"'
    verbose_name_kk: str = 'Инвестициялық жобаның күйі өзгертілді: "пысықтауда"'
    color: str = 'error'
    icon: str = 'profile'
    category_code: str = 'invest-project'
    template_html = '{{initiator.full_name}} отправил(-а) на доработку инвестпроект ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span>.'
    template_text = '{{initiator.full_name}} отправил(-а) на доработку инвестпроект "{{subj.project_name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span> инвестициялық жобасын пысықтауға жіберді'
    template_text_kk = '{{initiator.full_name}} "{{subj.project_name}}" инвестициялық жобасын пысықтауға жіберді'

    def collect_data(self, initiator: ProfileModel = None, subj: InvestProjectInfoModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class InvestProjectChangeStatusApproved(BaseEventType):
    """
    Смена статуса инвестпроекта: "одобрен"
    """
    code: str = 'invest_project_changed_status_approved'
    verbose_name: str = 'Смена статуса инвестпроекта: "одобрен"'
    verbose_name_kk: str = 'Инвестициялық жобаның күйі өзгертілді: "мақұлданды"'
    color: str = 'success'
    icon: str = 'profile'
    category_code: str = 'invest-project'
    template_html = '{{initiator.full_name}} одобрил(-а) инвестпроект ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span>.'
    template_text = '{{initiator.full_name}} одобрил(-а) инвестпроект "{{subj.project_name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span> инвестициялық жобасын мақұлдады'
    template_text_kk = '{{initiator.full_name}} "{{subj.project_name}}" инвестициялық жобасын мақұлдады'

    def collect_data(self, initiator: ProfileModel = None, subj: InvestProjectInfoModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class InvestProjectChangeStatusChangeRequested(BaseEventType):
    """
    Смена статуса инвестпроекта: "запрошено изменение"
    """
    code: str = 'invest_project_changed_status_change_requested'
    verbose_name: str = 'Смена статуса инвестпроекта: "запрошено изменение"'
    verbose_name_kk: str = 'Инвестициялық жобаның күйі өзгертілді: "өзгерту сұралды"'
    color: str = 'warning'
    icon: str = 'profile'
    category_code: str = 'invest-project'
    template_html = '{{initiator.full_name}} отправил(-а) заявку на изменение инвестпроекта ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span>.'
    template_text = '{{initiator.full_name}} отправил(-а) заявку на изменение инвестпроекта "{{subj.project_name}}".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-type="full_invest_project_info" ' \
                    'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                    'data-link-open="false">"{{subj.project_name}}"</span> инвестициялық жобасына өзгеріс енгізу туралы өтінім жіберді'
    template_text_kk = '{{initiator.full_name}} "{{subj.project_name}}" инвестициялық жобасына өзгеріс енгізу туралы өтінім жіберді'

    def collect_data(self, initiator: ProfileModel = None, subj: InvestProjectInfoModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class InvestProjectChangeStatusGeneric(BaseEventType):
    """Общее уведомление о смене статуса инвестпроекта (если для него нет специального уведомления)."""
    code: str = 'invest_project_change_status_generic'
    verbose_name: str = 'Смена статуса'
    verbose_name_kk: str = 'Күйдің өзгеруі'
    color: str = 'primary'
    icon: str = 'profile'
    category_code: str = 'invest-project'
    template_html: str = '{{initiator.full_name}} сменил(-а) статус инвестпроекта ' \
                         '<span class="n_link" data-link-type="full_invest_project_info" ' \
                         'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                         'data-link-open="false">"{{subj.project_name}}"</span>.' \
                         'на <strong>{{subj.status.name}}</strong>.'
    template_text: str = '{{initiator.full_name}} сменил(-а) статус инвестпроекта "{{subj.project_name}}". \n' \
                         'Новый статус: {{subj.status.name}}.'
    # Казахский
    template_html_kk: str = '{{initiator.full_name}} ' \
                         '<span class="n_link" data-link-type="full_invest_project_info" ' \
                         'data-link-query=\'{"id": "{{subj.id}}"}\' ' \
                         'data-link-open="false">"{{subj.project_name}}"</span> ' \
                         'инвестициялық жобаның күйін <strong>{{subj.status.name}}</strong> деп өзгертті'
    template_text_kk: str = '{{initiator.full_name}} "{{subj.project_name}}" инвестициялық жобаның күйін {{subj.status.name}} деп өзгертті'

    def collect_data(self, initiator: ProfileModel = None, subj: InvestProjectInfoModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class SportFacilityChangeStatusGeneric(BaseEventType):
    """
    Уведомление об изменении статуса.
    subj - экземпляр SportFacilityInfoModel
    obj - экземпляр SportFacilityStatusModel
    initiator - Экземпляр ProfileModel
    """
    code: str = 'sports_facility_change_status'
    verbose_name: str = 'Смена статуса'
    verbose_name_kk: str = 'Күйдің өзгеруі'
    color: str = 'primary'
    icon: str = 'info'  # TODO поменять иконку
    category_code: str = 'sports-facilities'
    # TODO прописать ссылку
    template_html = '{{initiator.full_name}} Изменил(-а) статус паспорта спортивного объекта ' \
                    '<a href="{{urls.frontend_url}}/sports-facilities/{{subj.id}}/info">{{subj.facility_type.full_name}} "{{subj.name}}"</a>. ' \
                    'Новый статус: <strong>{{obj.name}}</strong>.'
    template_text = '{{initiator.full_name}} Изменил(-а) статус паспорта спортивного объекта {{subj.facility_type.full_name}} "{{subj.name}}". ' \
                    'Новый статус: {{obj.name}}.'
    # Казахский
    template_html_kk = '{{initiator.full_name}}' \
                       '<a href="{{urls.frontend_url}}/sports-facilities/{{subj.id}}/info">{{subj.facility_type.full_name}} түріндегі "{{subj.name}}"</a> ' \
                       'спорттық нысан паспортының мәртебесін өзгертті. ' \
                       'Жаңа күй: <strong>{{obj.name}}</strong>.'
    template_text_kk = '{{initiator.full_name}} {{subj.facility_type.full_name}} түріндегі "{{subj.name}}" спорттық нысан паспортының мәртебесін өзгертті. ' \
                       'Жаңа күй: {{obj.name}}.'

    url = f"{{urls.notifications}}/sports-facilities/{{subj.id}}/gallery"

    def collect_data(self, initiator: ProfileModel = None, subj=None, obj=None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)


class SportFacilityRequestUpdate(BaseEventType):
    """
    Уведомление админам спортивных объектов организации о запросе на изменение.
    """
    code: str = 'sports_facility_request_update'
    verbose_name: str = 'Запрос на изменение спортивного объекта'
    verbose_name_kk: str = 'Спорттық нысанды өзгертуге сұрау'
    color: str = 'primary'
    icon: str = 'info'  # TODO поменять иконку
    category_code: str = 'sports-facilities'
    # TODO прописать ссылку
    template_html = '{{initiator.full_name}} отправил(-а) запрос на изменение паспорта спортивного объекта ' \
                    '<a href="{{urls.frontend_url}}/sports-facilities/{{subj.id}}/info">{{subj.facility_type.full_name}} "{{subj.name}}"</a>. ' \
                    'Чтобы разрешить изменение, смените статус объекта на "На доработку".'
    template_text = '{{initiator.full_name}} отправил(-а) запрос на изменение паспорта спортивного объекта {{subj.facility_type.full_name}} "{{subj.name}}". ' \
                    'Чтобы разрешить изменение, смените статус объекта на "На доработку".'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<a href="{{urls.frontend_url}}/sports-facilities/{{subj.id}}/info">{{subj.facility_type.full_name}} түріндегі "{{subj.name}}"</a> ' \
                    'спорттық нысан паспортына өзгеріс енгізу туралы сұрау жіберді. ' \
                    'Өзгеріске рұқсат беру үшін нысанның күйін "Пысықтауға" деп өзгертіңіз.'
    template_text_kk = '{{initiator.full_name}} {{subj.facility_type.full_name}} түріндегі "{{subj.name}}". ' \
                       'спорттық нысан паспортына өзгеріс енгізу туралы сұрау жіберді. ' \
                       'Өзгеріске рұқсат беру үшін нысанның күйін "Пысықтауға" деп өзгертіңіз.'
    url = f"{{urls.notifications}}/sports-facilities/{{subj.id}}/gallery"

    def collect_data(self, initiator: ProfileModel = None, subj=None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj)


class WorkgroupOrganizationMemberInvite(BaseEventType):
    """Уведомление о приглашении организации-участника в проект"""
    code: str = 'workgroup_organization_member_invite'
    verbose_name: str = 'Приглашение организации-участника в проект'
    verbose_name_kk: str = 'Жобаға қатысушы ұйымды шақыру'

    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'projects'
    subject_source = 'obj'

    template_html: str = 'Вас приглашают <span class="n_link" data-link-type="project_organization_member_invite" ' \
                    'data-link-query=\'{"project": "{{obj.id}}", "organization_member": "{{subj.id}}"}\' ' \
                    'data-link-open="false">вступить</span> в проект "{{obj.name}}" в роли "{{subj.role.name}}"'
    template_text: str = 'Вас приглашают вступить в проект "{{obj.name}}" в роли "{{subj.role.name}}"'
    # Казахский
    template_html_kk: str = 'Сізді "{{obj.name}}" жобасына "{{subj.role.name}}" рөлінде ' \
                    '<span class="n_link" data-link-type="project_organization_member_invite" ' \
                    'data-link-query=\'{"project": "{{obj.id}}", "organization_member": "{{subj.id}}"}\' ' \
                    'data-link-open="false">қатысуға шақырады</span>'
    template_text_kk: str = 'Сізді "{{obj.name}}" жобасына "{{subj.role.name}}" рөлінде қатысуға шақырады'

    def collect_data(self, obj=None, subj=None, collect_context: dict = None, **kwargs):
        return super().collect_data(obj=obj, subj=subj)


# НАПОМИНАНИЯ О ЦЕЛЯХ OKR
class UpdateObjectiveReminderWeekly(BaseEventType):
    """
    Напоминание о необходимости актуализировать цель и ее ключевые результаты.
    Еженедельное.
    """
    code: str = 'update_objective_reminder_weekly'
    verbose_name: str = 'Еженедельное напоминание о цели.'
    verbose_name_kk: str = 'Мақсат туралы апталық еске салу'
    color: str = 'primary'
    icon: str = 'schedule'
    category_code: str = 'okr'
    template_html = 'Пожалуйста, обновите статус по цели ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> в разделе "OKR".'
    template_text = 'Пожалуйста, обновите статус по цели "{{subj.objective}}" в разделе "OKR".'
    # Казахский
    template_html_kk = '"OKR" бөлімінде ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> мақсаты бойынша күйді жаңартыңыз.'
    template_text_kk = '"OKR" бөлімінде "{{subj.objective}}" мақсаты бойынша күйді жаңартыңыз.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class UpdateObjectiveReminderFortnightly(BaseEventType):
    """
    Напоминание о необходимости актуализировать цель и ее ключевые результаты.
    Раз в две недели.
    """
    code: str = 'update_objective_reminder_fortnightly'
    verbose_name: str = 'Напоминание о цели раз в две недели.'
    verbose_name_kk: str = 'Мақсат туралы әр екі апта сайын еске салу.'
    color: str = 'primary'
    icon: str = 'schedule'
    category_code: str = 'okr'

    template_html = 'Напоминание: требуется актуализировать ключевые результаты по цели ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span>. Обновление доступно в разделе "OKR".'
    template_text = 'Напоминание: требуется актуализировать ключевые результаты по цели "{{subj.objective}}". ' \
                    'Обновление доступно в разделе "OKR".'
    # Казахский
    template_html_kk = 'Еске салу: ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> мақсаты бойынша негізгі нәтижелерді жаңарту қажет. Жаңартуды «OKR» бөлімінде жасауға болады.'
    template_text_kk = 'Еске салу: "{{subj.objective}}" ' \
                    'мақсаты бойынша негізгі нәтижелерді жаңарту қажет. Жаңартуды «OKR» бөлімінде жасауға болады.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class UpdateObjectiveReminderMonthly(BaseEventType):
    """
    Напоминание о необходимости актуализировать цель и ее ключевые результаты.
    Раз в месяц.
    """
    code: str = 'update_objective_reminder_monthly'
    verbose_name: str = 'Напоминание о цели раз в месяц.'
    verbose_name_kk: str = 'Мақсат туралы ай сайынғы еске салу.'
    color: str = 'primary'
    icon: str = 'schedule'
    category_code: str = 'okr'

    template_html = 'Завершается месяц. Просим проверить и при необходимости обновить статус по цели ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> в разделе "OKR".'
    template_text = 'Завершается месяц. Просим проверить и при необходимости обновить статус по цели "{{subj.objective}}" ' \
                    'в разделе "OKR".'
    # Казахский
    template_html_kk = 'Ай аяқталады. ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> мақсаты бойынша мәртебені "OKR" бөлімінде тексеріп, қажет болса жаңартыңыз.'
    template_text_kk = 'Ай аяқталады. "{{subj.objective}}" ' \
                    'мақсаты бойынша мәртебені "OKR" бөлімінде тексеріп, қажет болса жаңартыңыз.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class UpdateObjectiveReminderQuarterly(BaseEventType):
    """
    Напоминание о необходимости актуализировать цель и ее ключевые результаты.
    Раз в квартал.
    """
    code: str = 'update_objective_reminder_quarterly'
    verbose_name: str = 'Напоминание о цели раз в квартал.'
    verbose_name_kk: str = 'Мақсат бойынша тоқсан сайынғы еске салу.'
    color: str = 'primary'
    icon: str = 'schedule'
    category_code: str = 'okr'

    template_html = 'Завершается квартал. Необходимо актуализировать ключевые результаты и общий статус по цели ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> в разделе "OKR".'
    template_text = 'Завершается квартал. Необходимо актуализировать ключевые результаты и общий статус по цели "{{subj.objective}}" ' \
                    'в разделе "OKR".'
    # Казахский
    template_html_kk = 'Тоқсан аяқталуда. ' \
                    '<span class="n_link" data-link-type="objectives" ' \
                    'data-link-query=\'{"objectives":"{{subj.id}}"}\' data-link-open="true" >' \
                    '"{{subj.objective}}"</span> мақсаты бойынша негізгі нәтижелер мен жалпы күйді "OKR" бөлімінде жаңарту қажет.'
    template_text_kk = 'Тоқсан аяқталуда. "{{subj.objective}}" ' \
                    'мақсаты бойынша негізгі нәтижелер мен жалпы күйді "OKR" бөлімінде жаңарту қажет.'
    url = '{{urls.notifications}}?event={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


# help_desk

class HelpDeskTicketNewComment(BaseEventType):
    code: str = 'ticket_new_comment'
    verbose_name: str = 'Новый комментарий к обращению'
    verbose_name_kk: str = 'Өтінішке жаңа пікір'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к <strong>обращению</strong> ' \
                    '<span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к обращению #{{subj.number}}:\n {{obj.text}}'
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span> өтінішке пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} #{{subj.number}} өтінішке пікір қалдырды: {{obj.text}}'
    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, initiator, subj, obj, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients=tuple(), initiator=None, subj=None, obj=None):
        recipients = list()
        specialist = subj.specialist
        if specialist:
            recipients.append(specialist.pk)
        customer_card = subj.contact_person.customer_card
        if not specialist:
            specialists = list(subj.contact_person.customer_card.actual_specialists.values_list('user', flat=True))
            recipients = recipients + specialists
        visors = list(subj.visors.all().values_list('pk', flat=True))
        if visors:
            recipients = recipients + visors
        admins = list(
            users_that_have_app_section_role_in_contractors((customer_card.org_admin_id,), 'help_desk', 'admin')
        )
        if admins:
            recipients = recipients + admins
        recipients = set(recipients)
        mentions = set(obj.mentions.all().values_list('pk', flat=True))
        recipients = recipients - mentions
        recipients.discard(initiator.pk)
        return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class HelpDeskTicketNewCommentMention(BaseEventType):
    code: str = 'ticket_new_comment_mention'
    verbose_name: str = 'Упоминание в комментарии к обращению'
    verbose_name_kk: str = 'Өтінішке қалдырылған пікірде атап өту'
    color: str = 'primary'
    icon: str = 'info'
    is_mention: bool = True

    category_code: str = 'help_desk'
    template_html = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к <strong>обращению</strong> ' \
                    '<span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к обращению #{{subj.number}}:\n ' \
                    '{{obj.text}}'
    template_html_kk = '{{initiator.full_name}} сізді ' \
                    '<span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}}</span> өтінішке қалдырылған пікірде атап өтті: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text_kk = '{{initiator.full_name}} сізді #{{subj.number}} ' \
                       'өтінішке қалдырылған пікірде атап өтті:\n {{obj.text}}'
    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, initiator, subj, obj, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients=tuple(), initiator=None, subj=None, obj=None):
        recipients = list(obj.mentions.all())
        if recipients:
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class HelpDeskTicketNewCommentClient(BaseEventType):
    code: str = 'ticket_new_comment_client'
    verbose_name: str = 'Новый комментарий к обращению (для клиентов)'
    verbose_name_kk: str = 'Өтінішке жаңа пікір (клиенттер үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к <strong>обращению</strong> ' \
                    '<span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                    '</blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) {% if obj.is_personal %} конфиденциальный {% endif %}' \
                    ' комментарий к обращению #{{subj.number}}:\n {{obj.text}}'
    template_html_kk = '{{initiator.full_name}} ' \
                       '<span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                       'data-link-open="true">№{{subj.number}} </span> өтінішке пікір қалдырды: ' \
                       '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}' \
                       '</blockquote>'
    template_text_kk = '{{initiator.full_name}} #{{subj.number}} өтінішке пікір қалдырды: {{obj.text}}'
    url = '{{urls.notifications}}?requestView={{subj.id}}'

    def collect_data(self, initiator, subj, obj, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients=tuple(), initiator=None, subj=None, obj=None):
        if obj.is_personal:
            return None
        else:
            recipients = list()
            contact_person = subj.contact_person
            if contact_person:
                contact_person_user = subj.contact_person.user
                if contact_person_user:
                    recipients.append(contact_person_user)
        if recipients:
            recipients = set(recipients)
            recipients.discard(initiator)
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)
        else:
            return None


class TicketStatusNew(BaseEventType):

    code: str = 'ticket_new_status'
    verbose_name: str = 'Новый статус обращения (для клиента)'
    verbose_name_kk: str = 'Өтініштің жаңа күйі (клиент үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Ваше обращение <span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>' \
                    'сменило статус на "{{obj.name}}"'
    template_text = 'Ваше обращение №{{subj.number}} сменило статус на "{{obj.name}}"'

    template_html_kk = 'Сіздің <span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>' \
                    'өтінішіңіздің күйі "{{obj.name}}" болып өзгерді'
    template_text_kk = 'Сіздің №{{subj.number}} өтінішіңіздің күйі "{{obj.name}}" болып өзгерді'

    url = '{{urls.notifications}}?requestView={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class TicketStatusNewSpecialist(BaseEventType):

    code: str = 'ticket_new_status_specialist'
    verbose_name: str = 'Новый статус обращения (для техподдержки)'
    verbose_name_kk: str = 'Өтініштің жаңа күйі (техникалық қолдау үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Обращение <span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span>' \
                    'сменило статус на "{{obj.name}}"'
    template_text = 'Обращение №{{subj.number}} сменило статус на: \n "{{obj.name}}"\n' \
                    'Ответственный: {{subj.specialist.full_name}}\n' \
                    '👤 Контактное лицо: \n' \
                    'Имя: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Категория: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Приоритет: {{subj.priority.name}}\n' \
                    '📅 Создано: {{subj.created_at}}\n' \
                    '⏰ Крайний срок: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Время реагирования: {{subj.sla.first_reaction_time_str}} ' \
                    '(взять в работу до {{subj.sla.in_work_to}})\n' \
                    '⌛ Время решения: {{subj.sla.solve_time_str}}'

    template_html_kk = '<span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}} </span> ' \
                    'өтініштің күйі "{{obj.name}}" болып өзгерді'
    template_text_kk = '№{{subj.number}} өтініштің күйі \n "{{obj.name}}" болып өзгерді\n' \
                    'Жауапты: {{subj.specialist.full_name}}\n' \
                    '👤 Байланыс тұлға: \n' \
                    'Аты: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Санат: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Маңыздылық: {{subj.priority.name}}\n' \
                    '📅 Құрылды: {{subj.created_at}}\n' \
                    '⏰ Соңғы мерзім: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Жауап беру уақыты: {{subj.sla.first_reaction_time_str}} ' \
                    '(жұмысқа кірісу мерзімі {{subj.sla.in_work_to}})\n' \
                    '⌛ Шешім уақыты: {{subj.sla.solve_time_str}}\n'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class TicketNewForContactPerson(BaseEventType):
    code: str = 'ticket_new_for_contact_person'
    verbose_name: str = 'Новое обращение (для клиента техподдержки)'
    verbose_name_kk: str = 'Жаңа өтініш (техқолдау клиенті үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Ваше обращение <span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}}</span> зарегистрировано в системе'
    template_text = 'Ваше обращение №{{subj.number}} зарегистрировано в системе'

    template_html_kk = 'Сіздің <span class="n_link" data-link-query=\'{"requestView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}}</span> өтінішіңіз жүйеге тіркелді'
    template_text_kk = 'Сіздің №{{subj.number}} өтінішіңіз жүйеге тіркелді'

    url = '{{urls.notifications}}?requestView={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class TicketNewForAdmins(BaseEventType):
    code: str = 'ticket_new_for_admins'
    verbose_name: str = 'Новое обращение (для администратора техподдержки)'
    verbose_name_kk: str = 'Жаңа өтініш (техқолдау әкімшісі үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Поступило новое обращение <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{obj.name}}'
    template_text = 'Поступило новое обращение №{{subj.number}} от {{obj.name}}  \n' \
                    'Ответственный: {{subj.specialist.full_name}}\n' \
                    '👤 Контактное лицо: \n' \
                    'Имя: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{obj.name}}\n' \
                    '📂 Категория: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Приоритет: {{subj.priority.name}}\n' \
                    '📅 Создано: {{subj.created_at}}\n' \
                    '⏰ Крайний срок: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Время реагирования: {{subj.sla.first_reaction_time_str}} ' \
                    '(взять в работу до {{subj.sla.in_work_to}})\n' \
                    '⌛ Время решения: {{subj.sla.solve_time_str}}\n'

    template_html_kk = '{{obj.name}} ұйымынан жаңа <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> нөмірлі өтініш келіп түсті'
    template_text_kk = '{{obj.name}} ұйымынан жаңа №{{subj.number}} нөмірлі өтініш келіп түсті \n' \
                    'Жауапты: {{subj.specialist.full_name}}\n' \
                    '👤 Байланыс тұлға: \n' \
                    'Аты: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{obj.name}}\n' \
                    '📂 Санат: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Маңыздылық: {{subj.priority.name}}\n' \
                    '📅 Құрылған күні: {{subj.created_at}}\n' \
                    '⏰ Соңғы мерзім: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Жауап беру уақыты: {{subj.sla.first_reaction_time_str}} ' \
                    '(жұмысқа кірісу мерзімі до {{subj.sla.in_work_to}})\n' \
                    '⌛ Шешім уақыты: {{subj.sla.solve_time_str}}\n'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class TicketNewForSpecialists(BaseEventType):
    code: str = 'ticket_new_for_specialists'
    verbose_name: str = 'Новое обращение (для специалиста техподдержки)'
    verbose_name_kk: str = 'Жаңа өтініш (техқолдау маманы үшін)'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Поступило новое обращение <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{obj.name}}'
    template_text = 'Поступило новое обращение №{{subj.number}} от {{obj.name}}  \n' \
                    'Ответственный: {{subj.specialist.full_name}}\n' \
                    '👤 Контактное лицо: \n' \
                    'Имя: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{obj.name}}\n' \
                    '📂 Категория: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Приоритет: {{subj.priority.name}}\n' \
                    '📅 Создано: {{subj.created_at}}\n' \
                    '⏰ Крайний срок: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Время реагирования: {{subj.sla.first_reaction_time_str}} ' \
                    '(взять в работу до {{subj.sla.in_work_to}})\n' \
                    '⌛ Время решения: {{subj.sla.solve_time_str}}\n'

    template_html_kk = '{{obj.name}} ұйымынан жаңа <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> нөмірлі өтініш келіп түсті'
    template_text_kk = '{{obj.name}} ұйымынан жаңа №{{subj.number}}  нөмірлі өтініш келіп түсті \n' \
                    'Жауапты: {{subj.specialist.full_name}}\n' \
                    '👤 Байланыс тұлға: \n' \
                    'Аты: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{obj.name}}\n' \
                    '📂 Санат: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Маңыздылық: {{subj.priority.name}}\n' \
                    '📅 Құрылған күні: {{subj.created_at}}\n' \
                    '⏰ Соңғы мерзім: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Жауап беру уақыты: {{subj.sla.first_reaction_time_str}} ' \
                    '(жұмысқа кірісу мерзімі {{subj.sla.in_work_to}})\n' \
                    '⌛ Шешім уақыты: {{subj.sla.solve_time_str}}\n'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class LeadNewForSpecialists(BaseEventType):
    code: str = 'lead_new_for_specialists'
    verbose_name: str = 'Новый лид'
    verbose_name_kk: str = 'Жаңа лид'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Поступил новый лид <span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}}</span> от {{obj.name}}'
    template_text = 'Поступил новый лид №{{subj.number}} от {{obj.name}}'

    template_html_kk = 'Жаңа лид <span class="n_link" data-link-query=\'{"ticketView":"{{subj.id}}"}\' ' \
                    'data-link-open="true">№{{subj.number}}</span> {{obj.name}} келіп түсті'
    template_text_kk = 'Жаңа лид №{{subj.number}} {{obj.name}} келіп түсті'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj)
        return data


class NewTicketClientMessageForSpecialist(BaseEventType):
    code: str = 'new_ticket_client_message_for_specialist'
    verbose_name: str = 'Новое сообщение клиента в обращении'
    verbose_name_kk: str = 'Өтініштегі клиенттің жаңа хабарламасы'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Поступило новое сообщение в обращении <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{initiator.name}}: '\
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.short_text}}' \
                    '</blockquote>'
    template_text = 'Поступило новое сообщение в обращении №{{subj.number}} от {{initiator.name}}: \n' \
                    '{{obj.short_text}}'

    template_html_kk = '<span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> өтінішіне {{initiator.name}} тарапынан жаңа хабарлама келіп түсті: '\
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.short_text}}' \
                    '</blockquote>'
    template_text_kk = '№{{subj.number}} өтінішіне {{initiator.name}} тарапынан жаңа хабарлама келіп түсті: {{obj.short_text}}'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, initiator, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        return data


class NewTicketSpecialistMessageForClient(BaseEventType):
    code: str = 'new_ticket_specialist_message_for_client'
    verbose_name: str = 'Новое сообщение специалиста в обращении'
    verbose_name_kk: str = 'Өтініште маманның жаңа хабарламасы'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Поступило новое сообщение в обращении <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"requestView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{initiator.full_name}}: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.short_text}}' \
                    '</blockquote>'
    template_text = 'Поступило новое сообщение в обращении №{{subj.number}} от {{initiator.full_name}}: \n' \
                    '{{obj.short_text}}'

    template_html_kk = '<span class="n_link" data-link-open="true" ' \
                       'data-link-query=\'{"requestView":"{{subj.id}}"}\'> №{{subj.number}} </span> өтінішіне ' \
                       '{{initiator.full_name}} тарапынан жаңа хабарлама келіп түсті: ' \
                       '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.short_text}}' \
                       '</blockquote>'
    template_text_kk = '№{{subj.number}} өтінішіне {{initiator.full_name}} тарапынан жаңа хабарлама келіп түсті: {{obj.short_text}}'

    url = '{{urls.notifications}}?requestView={{subj.id}}'

    def collect_data(self, initiator, subj, obj, collect_context: dict = None, **kwargs):
        data = super().collect_data(initiator=initiator, subj=subj, obj=obj)
        return data


class TicketSpecialistAssign(BaseEventType):
    code: str = 'ticket_specialist_assign'
    verbose_name: str = 'Назначение обращения'
    verbose_name_kk: str = 'Өтінішті тағайындау'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Вам назначено обращение <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{subj.customer_card.name}}'
    template_text = 'Вам назначено обращение №{{subj.number}} от {{subj.customer_card.name}}  \n' \
                    'Ответственный: {{subj.specialist.full_name}}\n' \
                    '👤 Контактное лицо: \n' \
                    'Имя: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Категория: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Приоритет: {{subj.priority.name}}\n' \
                    '📅 Создано: {{subj.created_at}}\n' \
                    '⏰ Крайний срок: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Время реагирования: {{subj.sla.first_reaction_time_str}} ' \
                    '(взять в работу до {{subj.sla.in_work_to}})\n' \
                    '⌛ Время решения: {{subj.sla.solve_time_str}}\n'

    template_html_kk = 'Сізге <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> өтініші {{subj.customer_card.name}} атынан тағайындалды'
    template_text_kk = 'Сізге №{{subj.number}} өтініші {{subj.customer_card.name}} атынан тағайындалды \n' \
                    'Жауапты: {{subj.specialist.full_name}}\n' \
                    '👤 Байланыс тұлға: \n' \
                    'Аты: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Санат: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Маңыздылық: {{subj.priority.name}}\n' \
                    '📅 Құрылды: {{subj.created_at}}\n' \
                    '⏰ Соңғы мерзім: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Жауап беру уақыты: {{subj.sla.first_reaction_time_str}} ' \
                    '(жұмысқа кірісу мерзімі {{subj.sla.in_work_to}})\n' \
                    '⌛ Шешім уақыты: {{subj.sla.solve_time_str}}\n'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class TicketMemberAssign(BaseEventType):
    code: str = 'ticket_member_assign'
    verbose_name: str = 'Назначение участником обращения'
    verbose_name_kk: str = 'Өтінішке қатысушы ретінде тағайындау'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'help_desk'
    template_html = 'Вас назначили участником обращения <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> от {{subj.customer_card.name}}'
    template_text = 'Вас назначили участником обращения №{{subj.number}} от {{subj.customer_card.name}}  \n' \
                    'Ответственный: {{subj.specialist.full_name}}\n' \
                    '👤 Контактное лицо: \n' \
                    'Имя: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Категория: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Приоритет: {{subj.priority.name}}\n' \
                    '📅 Создано: {{subj.created_at}}\n' \
                    '⏰ Крайний срок: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Время реагирования: {{subj.sla.first_reaction_time_str}} ' \
                    '(взять в работу до {{subj.sla.in_work_to}})\n' \
                    '⌛ Время решения: {{subj.sla.solve_time_str}}\n'

    template_html_kk = 'Сізді <span class="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"ticketView":"{{subj.id}}"}\'> №{{subj.number}} </span> тарапынан ' \
                       '{{subj.customer_card.name}} өтінішіне қатысушы ретінде тағайындады'
    template_text_kk = 'Сізді №{{subj.number}} тарапынан {{subj.customer_card.name}} өтінішіне қатысушы ретінде тағайындады \n' \
                    'Жауапты: {{subj.specialist.full_name}}\n' \
                    '👤 Байланыс тұлға: \n' \
                    'Аты: {{subj.contact_person.name}} \n' \
                    '🏢 Клиент: {{subj.customer_card.name}}\n' \
                    '📂 Санат: {{subj.category.name}}\n' \
                    '{{subj.priority_emoji}} Маңыздылық: {{subj.priority.name}}\n' \
                    '📅 Құрылды: {{subj.created_at}}\n' \
                    '⏰ Соңғы мерзім: {{subj.dead_line}}\n' \
                    '{{subj.sla.color_emoji}} SLA: {{subj.sla.name}}\n' \
                    '⏱ Жауап беру уақыты: {{subj.sla.first_reaction_time_str}} ' \
                    '(жұмысқа кірісу мерзімі {{subj.sla.in_work_to}})\n' \
                    '⌛ Шешім уақыты: {{subj.sla.solve_time_str}}\n'

    url = '{{urls.notifications}}?ticketView={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


# contractor_permissions
class NewAccessGroupForMember(BaseEventType):
    code: str = 'new_access_group_for_member'
    verbose_name: str = 'Новая группа доступа'
    verbose_name_kk: str = 'Жаңа қолжетімділік тобы'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'organization'
    subject_source = None
    template_html = 'Вас добавили в группу доступа "{{obj.name}}" в организации "{{subj.name}}". ' \
                    'Обновите страницу, чтобы увидеть новые возможности'
    template_text = 'Вас добавили в группу доступа "{{obj.name}}" в организации "{{subj.name}}". ' \
                    'Обновите страницу, чтобы увидеть новые возможности'

    template_html_kk = 'Сіз "{{subj.name}}" ұйымындағы «{{obj.name}}» қолжетімділік тобына қосылдыңыз. ' \
                       'Жаңа мүмкіндіктерді көру үшін бетті жаңартыңыз'
    template_text_kk = 'Сіз "{{subj.name}}" ұйымындағы «{{obj.name}}» қолжетімділік тобына қосылдыңыз. ' \
                       'Жаңа мүмкіндіктерді көру үшін бетті жаңартыңыз'

    url = ''

    def collect_data(self, obj, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(obj=obj, subj=subj)
        return data


# new user info:
class NewUserInfo(BaseEventType):
    code: str = 'new_user_info'
    verbose_name: str = 'Новый пользователь'
    verbose_name_kk: str = 'Новый пользователь'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'moderation'
    subject_source = None
    template_html = 'Зарегистрирован новый пользователь {{subj.user.full_name}}!'
    template_html_kk = 'Зарегистрирован новый пользователь {{subj.user.full_name}}!'
    template_text = 'Жаңа пайдаланушы {{subj.user.full_name}} тіркелді!'
    template_text_kk = 'Жаңа пайдаланушы {{subj.user.full_name}} тіркелді!'
    url = ''

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


# workflow_request

class WorkflowRequestComplete(BaseEventType):
    code: str = 'workflow_request_complete'
    verbose_name: str = 'Заявка завершена'
    verbose_name_kk: str = 'Өтінім аяқталды'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Ваша заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> завершена!'
    template_text = 'Ваша заявка №{{subj.number}} завершена!'

    template_html_kk = 'Сіздің <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> өтініміңіз аяқталды!!'
    template_text_kk = 'Сіздің №{{subj.number}} өтініміңіз аяқталды!'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class WorkflowRequestLPRApprove(BaseEventType):
    code: str = 'workflow_request_lpr_approve'
    verbose_name: str = 'Заявка одобрена ЛПР'
    verbose_name_kk: str = 'Заявка одобрена ЛПР'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> одобрена ЛПР'
    template_text = 'Заявка №{{subj.number}} одобрена ЛПР'

    template_html_kk = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> одобрена ЛПР'
    template_text_kk = 'Заявка №{{subj.number}} одобрена ЛПР'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj)
        return data


class WorkflowRequestFinanceServiceAdvanceReport(BaseEventType):
    code: str = 'workflow_request_fs_ar'
    verbose_name: str = 'Согласование авансового отчета'
    verbose_name_kk: str = 'Аванстық есепті келісу'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = '{{initiator.full_name}} отправил(а) <strong>авансовый отчет</strong> заявки <span class ="n_link" ' \
                    'data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'на согласование'
    template_text = '{{initiator.full_name}} отправил(а) авансовый отчет заявки №{{subj.number}} на согласование'

    template_html_kk = '{{initiator.full_name}} <span class ="n_link" data-link-open="true" ' \
                       'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span>  өтінімнің аванстық ' \
                       'есебін келісуге жіберді'
    template_text_kk = '{{initiator.full_name}} №{{subj.number}} өтінімнің аванстық есебін келісуге жіберді'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestNewComment(BaseEventType):
    code: str = 'workflow_request_comments_notification'
    verbose_name: str = 'Новый комментарий к заявке'
    verbose_name_kk: str = 'Өтінімге жаңа пікір'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'workflow_request'

    template_html = '{{initiator.full_name}} оставил(-а)  комментарий к <strong>заявке</strong> ' \
                    '<span class="n_link" data-link-query=\'{"approvals":"{{subj.id}}"}\'>№{{subj.number}}</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}} </blockquote>'
    template_text = '{{initiator.full_name}} оставил(-а) комментарий к заявке №{{subj.number}}:\n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} ' \
                    '<span class="n_link" data-link-query=\'{"approvals":"{{subj.id}}"}\'>№{{subj.number}}</span> ' \
                       'өтінімге пікір қалдырды: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}} </blockquote>'
    template_text_kk = '{{initiator.full_name}} №{{subj.number}} өтінімге пікір қалдырды:\n {{obj.text}}'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj=None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj=None,
                            obj: CommentModel = None):
        from bpms.processes.models import RequestRouteUserThrough
        routes = subj.request_routes.all().values_list('pk', flat=True)
        recipients = set(
            RequestRouteUserThrough.objects.filter(
                request_route_id__in=routes,
            ).values_list('user', flat=True)
        )
        recipients.add(subj.author.pk)
        mentions = set(obj.mentions.all().values_list('pk', flat=True))
        recipients = recipients - mentions
        recipients.discard(initiator.pk)
        recipients.discard(None)
        if recipients:
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class WorkflowRequestNewCommentMention(BaseEventType):
    code: str = 'workflow_request_new_comments_mention'
    verbose_name: str = 'Упоминание в комментарии к заявке'
    verbose_name_kk: str = 'Өтінімге қалдырылған пікірде атап өту'
    color: str = 'default'
    icon: str = 'ellipsis'
    category_code: str = 'workflow_request'
    is_mention: bool = True

    template_html = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к <strong>заявке</strong> ' \
                    '<span class="n_link" data-link-query=\'{"approvals":"{{subj.id}}"}\'>№{{subj.number}}</span>: ' \
                    '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text = '{{initiator.full_name}} упомянул(-а) Вас в комментарии к заявке №{{subj.number}} :\n {{obj.text}}'
    # Казахский
    template_html_kk = '{{initiator.full_name}} сізді ' \
                       '<span class="n_link" data-link-query=\'{"approvals":"{{subj.id}}"}\'>№{{subj.number}}</span> ' \
                       'өтінімге қалдырылған пікірде атап өтті: ' \
                       '<blockquote style="padding-left: 5px; border-left: 3px solid #cccccc; ">{{obj.text}}</blockquote>'
    template_text_kk = '{{initiator.full_name}} сізді №{{subj.number}} өтінімге қалдырылған пікірде атап өтті:\n ' \
                       '{{obj.text}}'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, initiator: ProfileModel = None, subj=None, obj: CommentModel = None, collect_context: dict = None, **kwargs):
        return super().collect_data(initiator=initiator, subj=subj, obj=obj)

    def create_notification(self, recipients: tuple = tuple(), initiator: ProfileModel = None, subj=None,
                            obj: CommentModel = None):
        recipients = set(list(obj.mentions.all()))
        if recipients:
            return super().create_notification(recipients=tuple(recipients), initiator=initiator, subj=subj, obj=obj)


class WorkflowRequestForHeadOfDepartment(BaseEventType):
    code: str = 'workflow_request_for_head_or_department'
    verbose_name: str = 'Заявка на согласование руководителю подразделения'
    verbose_name_kk: str = 'Бөлім басшысына келісуге өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = '{{initiator.full_name}} отправил(а) заявку <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> на согласование'
    template_text = '{{initiator.full_name}} отправил(а) заявку №{{subj.number}} на согласование'

    template_html_kk = '{{initiator.full_name}} <span class ="n_link" data-link-open="true" ' \
                       'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                       'өтінімді келісуге жіберді'
    template_text_kk = '{{initiator.full_name}} №{{subj.number}} өтінімді келісуге жіберді'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestForFinanceService(BaseEventType):
    code: str = 'workflow_request_for_finance_service'
    verbose_name: str = 'Заявка на согласование финслужбе'
    verbose_name_kk: str = 'Қаржы қызметіне келісуге өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'ожидает согласования финансовой службой'
    template_text = 'Заявка №{{subj.number}} ожидает согласования финансовой службой'

    template_html_kk = '<span class ="n_link" data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> ' \
                       '№{{subj.number}} </span> өтінім басшы тарапынан визаланып, қаржы қызметімен келісуді күтуде'
    template_text_kk = '№{{subj.number}} өтінім басшы тарапынан визаланып, қаржы қызметімен келісуді күтуде'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestForPersonnelService(BaseEventType):
    code: str = 'workflow_request_for_personnel_service'
    verbose_name: str = 'Заявка на согласование кадровой службе'
    verbose_name_kk: str = 'Кадр қызметіне келісуге өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'ожидает согласования кадровой службой'
    template_text = 'Заявка №{{subj.number}} визирована руководителем ожидает согласования кадровой службой'

    template_html_kk = '<span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'өтінім басшы тарапынан визаланды, кадр қызметімен келісуді күтуде'
    template_text_kk = '№{{subj.number}} өтінім басшы тарапынан визаланды, кадр қызметімен келісуді күтуде'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestForLPR(BaseEventType):
    code: str = 'workflow_request_for_LPR'
    verbose_name: str = 'Заявка на согласование ЛПР'
    verbose_name_kk: str = 'Шешім қабылдайтын тұлғаға келісуге өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'передана ЛПР для принятия решения'
    template_text = 'Заявка №{{subj.number}} передана ЛПР для принятия решения'

    template_html_kk = '<span class ="n_link" data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> ' \
                       '№{{subj.number}} </span> өтінім қаржы қызметімен келісіліп, шешім қабылдау үшін ' \
                       'Шешім қабылдайтын тұлғаға жіберілді'
    template_text_kk = '№{{subj.number}} өтінім қаржы қызметімен келісіліп, шешім қабылдау үшін Шешім қабылдайтын тұлғаға жіберілді'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestForPayMaster(BaseEventType):
    code: str = 'workflow_request_for_paymaster'
    verbose_name: str = 'Заявка на выдачу денежных средств казначею'
    verbose_name_kk: str = 'Қазынашыға ақша қаражатын беру жөніндегі өтінім'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'ожидает выдачи денежных средств'
    template_text = 'Заявка №{{subj.number}} ожидает выдачи денежных средств'

    template_html_kk = '<span class ="n_link" data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> ' \
                       '№{{subj.number}} </span> өтінім Шешім қабылдайтын тұлға тарапынан мақұлданып, ' \
                       'ақша қаражатын беруді күтуде'
    template_text_kk = '№{{subj.number}} өтінім Шешім қабылдайтын тұлға тарапынан мақұлданып, ақша қаражатын беруді күтуде'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


class WorkflowRequestChangeStatusForAuthor(BaseEventType):
    code: str = 'workflow_request_change_status_for_author'
    verbose_name: str = 'Смена статуса заявки'
    verbose_name_kk: str = 'Өтінім күйінің өзгеруі'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'Ваша заявка <span class ="n_link" data-link-open="true" ' \
                    'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                    'сменила статус на "{{obj.name}}"'
    template_text = 'Ваша заявка №{{subj.number}} сменила статус на "{{obj.name}}"'

    template_html_kk = 'Сіздің <span class ="n_link" data-link-open="true" ' \
                       'data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> ' \
                       'өтініміңіздің күйі «{{obj.name}}» болып өзгерді'
    template_text_kk = 'Сіздің №{{subj.number}} өтініміңіздің күйі «{{obj.name}}» болып өзгерді'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, obj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, obj=obj, initiator=initiator)
        return data


class WorkflowRequestPaidForAuthor(BaseEventType):
    code: str = 'workflow_request_paid_for_author'
    verbose_name: str = 'Денежные средства выданы'
    verbose_name_kk: str = 'Ақша қаражаты берілді'
    color: str = 'primary'
    icon: str = 'info'
    category_code: str = 'workflow_request'
    template_html = 'По заявке <span class ="n_link" data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> выданы денежные средства, требуется заполнить авансовый отчёт'  # TODO добавить ссылку
    template_text = 'По заявке №{{subj.number}} выданы денежные средства, требуется заполнить авансовый отчёт'

    template_html_kk = '<span class ="n_link" data-link-open="true" data-link-query=\'{"approvals":"{{subj.id}}"}\'> №{{subj.number}} </span> өтінім бойынша ақша қаражаты берілді, аванстық есепті толтыру қажет'  # TODO добавить ссылку
    template_text_kk = '№{{subj.number}} өтінім бойынша ақша қаражаты берілді, аванстық есепті толтыру қажет'

    url = '{{urls.notifications}}?approvals={{subj.id}}'

    def collect_data(self, subj, initiator, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, initiator=initiator)
        return data


# Чат:
class ChatMention(BaseEventType):
    code: str = 'chat_mention'
    verbose_name: str = 'Упоминание в чате'
    verbose_name_kk: str = 'Чатта атап өту'
    color: str = 'primary'
    is_mention: bool = True

    category_code: str = 'chat'
    template_html = '{{subj.message_author.full_name}} упомянул Вас в чате <span class="n_link" data-link-type="chat" ' \
                    'data-link-query=\'{"chat_id":"{{subj.chat.chat_uid}}", "message_id":"{{subj.message_uid}}"}\' ' \
                    'data-link-open="true">{{subj.chat.name}}</span>'
    template_text = '{{subj.message_author.full_name}} упомянул Вас в чате {{subj.chat.name}}'

    template_html_kk = '{{subj.message_author.full_name}} сізді <span class="n_link" data-link-type="chat" ' \
                    'data-link-query=\'{"chat_id":"{{subj.chat.chat_uid}}", "message_id":"{{subj.message_uid}}"}\' ' \
                    'data-link-open="true">{{subj.chat.name}}</span> чатында атап өтті'
    template_text_kk = '{{subj.message_author.full_name}} сізді {{subj.chat.name}} чатында атап өтті'

    url = '{{urls.chat}}?chat_id={{subj.chat.chat_uid}}&message_id={{subj.message_uid}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj,)
        return data

    def get_subject(self, **kwargs):
        subj = kwargs.get('subj')
        return getattr(subj, 'chat', None) if subj else None


class ChatSummaryReady(BaseEventType):
    code: str = 'chat_summary_ready'
    verbose_name: str = 'Саммари чата готово'
    verbose_name_kk: str = 'Чат саммари дайын'
    color: str = 'success'
    icon: str = 'file-text'
    category_code: str = 'chat'
    template_html = 'Саммари чата <span class="n_link" data-link-type="chat" ' \
                    'data-link-query=\'{"chat_id":"{{subj.chat.chat_uid}}", "ai_summary":"true"}\' ' \
                    'data-link-open="true">"{{subj.chat.name}}"</span> готово.'
    template_text = 'Саммари чата "{{subj.chat.name}}" готово.'
    template_html_kk = 'Чат саммари <span class="n_link" data-link-type="chat" ' \
                        'data-link-query=\'{"chat_id":"{{subj.chat.chat_uid}}", "ai_summary":"true"}\' ' \
                        'data-link-open="true">"{{subj.chat.name}}"</span> дайын.'
    template_text_kk = 'Чат саммари "{{subj.chat.name}}" дайын.'
    url = '{{urls.chat}}?chat_id={{subj.chat.chat_uid}}&ai_summary=true'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj,)
        return data

    def get_subject(self, **kwargs):
        subj = kwargs.get('subj')
        return getattr(subj, 'chat', None) if subj else None


class ActivitySummaryReady(BaseEventType):
    code: str = 'activity_summary_ready'
    verbose_name: str = 'Саммари активности готово'
    verbose_name_kk: str = 'Белсенділік саммари дайын'
    color: str = 'success'
    icon: str = 'file-text'
    category_code: str = 'system'
    subject_source = None
    template_html = 'Саммари активности за период <span class="n_link" data-link-type="workplan-ai-consolidation" ' \
                    'data-link-query=\'{"id":"{{subj.id}}", "related_object_id":"{{subj.related_object}}", "scope":"{{subj.scope}}", "start_date":"{{subj.start_date}}", "end_date":"{{subj.end_date}}"}\' ' \
                    'data-link-open="false">{{ subj.period_display }}</span> готово.'
    template_text = 'Саммари активности ({{ subj.scope }}) за период {{ subj.period_display }} готово.'
    template_html_kk = 'Белсенділік саммари ({{ subj.scope }}) <span class="n_link" data-link-type="workplan-ai-consolidation" ' \
                        'data-link-query=\'{"id":"{{subj.id}}", "related_object_id":"{{subj.related_object}}", "scope":"{{subj.scope}}", "start_date":"{{subj.start_date}}", "end_date":"{{subj.end_date}}"}\' ' \
                        'data-link-open="false">{{ subj.period_display }}</span> дайын.'
    template_text_kk = 'Белсенділік саммари ({{ subj.scope }}) {{ subj.period_display }} дайын.'
    url = '{{urls.notifications}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, **kwargs)
        data['subj']['period_display'] = (
            f'{subj.start_date.strftime("%d.%m.%Y")}-{subj.end_date.strftime("%d.%m.%Y")}'
        )
        return data


class DaySummaryReady(BaseEventType):
    code: str = 'day_summary_ready'
    verbose_name: str = 'Саммари за день готово'
    verbose_name_kk: str = 'Күннің саммари дайын'
    color: str = 'success'
    icon: str = 'file-text'
    category_code: str = 'system'
    subject_source = None
    template_html = 'Саммари за {{subj.date_display}} <span class="n_link" ' \
                    'data-link-query=\'{"my_plan":"true", "wtab":"pulse"}\' ' \
                    'data-link-open="true">готово</span>.'
    template_text = 'Саммари за {{subj.date_display}} готово.'
    template_html_kk = 'Күннің саммари {{subj.date_display}} <span class="n_link" ' \
                      'data-link-query=\'{"my_plan":"true", "wtab":"pulse"}\' ' \
                      'data-link-open="true">дайын</span>.'
    template_text_kk = 'Күннің саммари {{subj.date_display}} дайын.'
    url = '{{urls.notifications}}'

    def collect_data(self, subj, collect_context: dict = None, **kwargs):
        data = super().collect_data(subj=subj, **kwargs)
        data['subj']['date_display'] = subj.date.strftime('%d.%m.%Y')
        return data


