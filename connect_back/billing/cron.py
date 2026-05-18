from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Prefetch
from django_q.tasks import async_task

from notifications.models import EmailNotificationModel, EmailNotificationRecipientModel
from notifications.utils import send_email
from common.catalogs.models import ContractorProfileModel
from .models import ContractorTariffModel, ContractorTariffNotificationLog

# Соответствие между template и subject
TEMPLATE_SUBJECTS = {
    'demo_started': 'Добро пожаловать! Ваш демо-период уже активирован',
    'demo_ending_3days': 'До окончания демо осталось 3 дня',
    'demo_ended': 'Сегодня заканчивается ваш демо-период',
}

def send_tariff_started_notifications(instance_count=100):
    """Отправка уведомлений о начале тарифа."""
    now = timezone.now()
    demo_started_tariffs = _get_demo_started_tariffs(now, instance_count)
    tasks_count = 0
    for contractor_tariff in demo_started_tariffs:
        async_task(_send_notification, contractor_tariff, 'demo_started')
        tasks_count += 1
    return tasks_count


def send_tariff_ending_notifications(instance_count=100):
    """Отправка уведомлений об окончании срока действия тарифов (пока только для демо-тарифа)."""
    now = timezone.now()
    
    # Запросы для каждого типа уведомления
    demo_ending_3days_tariffs = _get_demo_ending_3days_tariffs(now, instance_count)
    demo_ended_tariffs = _get_demo_ended_tariffs(now, instance_count)
    
    # Считаем количество задач
    tasks_count = 0
    
    # Отправляем уведомления за 3 дня до окончания
    for contractor_tariff in demo_ending_3days_tariffs:
        async_task(_send_notification, contractor_tariff, 'demo_ending_3days')
        tasks_count += 1
    
    # Отправляем уведомления об окончании
    for contractor_tariff in demo_ended_tariffs:
        async_task(_send_notification, contractor_tariff, 'demo_ended')
        tasks_count += 1
    
    return tasks_count


def _get_demo_started_tariffs(now, limit):
    """Тарифы, по которым сегодня началось демо"""
    return ContractorTariffModel.objects.filter(
        is_active=True,
        tariff__code='demo',
        date_start__date=now.date(),
    ).exclude(
        notification_logs__notification_type='demo_started'
    ).select_related('tariff').prefetch_related(
        Prefetch(
            'contractor__contractor_profile',
            queryset=ContractorProfileModel.objects.filter(director=True).select_related('user')
        )
    )[:limit]

def _get_demo_ending_3days_tariffs(now, limit):
    """Тарифы, по которым через 3 дня заканчивается демо"""
    target_date = now.date() + timedelta(days=3)
    return ContractorTariffModel.objects.filter(
        is_active=True,
        tariff__code='demo',
        date_end__date=target_date,
    ).exclude(
        notification_logs__notification_type='demo_ending_3days'
    ).select_related('tariff').prefetch_related(
        Prefetch(
            'contractor__contractor_profile',
            queryset=ContractorProfileModel.objects.filter(director=True).select_related('user')
        )
    )[:limit]


def _get_demo_ended_tariffs(now, limit):
    """Тарифы, по которым сегодня заканчивается демо"""
    return ContractorTariffModel.objects.filter(
        is_active=True,
        tariff__code='demo',
        date_end__date=now.date(),
    ).exclude(
        notification_logs__notification_type='demo_ended'
    ).select_related('tariff').prefetch_related(
        Prefetch(
            'contractor__contractor_profile',
            queryset=ContractorProfileModel.objects.filter(director=True).select_related('user')
        )
    )[:limit]


def _send_notification(contractor_tariff, notification_type):
    """Отправляет одно уведомление"""
    print("_send_notification", contractor_tariff, notification_type)
    try:
        director_profile = contractor_tariff.contractor.contractor_profile.filter(director=True).first()
        if not director_profile or not director_profile.user.user.email:
            return False
        director_email = director_profile.user.user.email
    except:
        return False

    try:
        from bkz3.settings import COMPANY_NAME
    except ImportError:
        COMPANY_NAME = 'GOS24.CONNECT'

    try:
        from bkz3.settings import TARIFFS_URL
    except ImportError:
        TARIFFS_URL = 'https://gos24.kz/tariffplans'

    with transaction.atomic():
        # Создаем email уведомление
        email_notification = EmailNotificationModel.objects.create(
            template=notification_type,
            subject=TEMPLATE_SUBJECTS[notification_type],
            context={
                'company_name': COMPANY_NAME,
                'tariffs_url': TARIFFS_URL,
                'director_name': director_profile.user.full_name,
                'contractor_name': contractor_tariff.contractor.name,
                'tariff_name': contractor_tariff.tariff.name,
                'date_start': contractor_tariff.date_start.strftime('%d.%m.%Y') if contractor_tariff.date_start else None,
                'date_end': contractor_tariff.date_end.strftime('%d.%m.%Y') if contractor_tariff.date_end else None,
                'days_left': (contractor_tariff.date_end - timezone.now()).days if contractor_tariff.date_end > timezone.now() else 0,
            }
        )

        # Добавляем получателя
        EmailNotificationRecipientModel.objects.create(
            email_notification=email_notification,
            recipient=director_email
        )

        # Создаем лог
        ContractorTariffNotificationLog.objects.create(
            contractor_tariff=contractor_tariff,
            notification_type=notification_type
        )

        # Отправляем
        send_email(email_notification.pk)
