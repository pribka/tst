import json

from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django_q.tasks import async_task

from bkz3.settings import (FRONTEND_URL,
                           SOCKETIO_SYSTEM_CHANNEL,
                           GLOBAL_FRONT_SETTINGS)
from bpms.bpms_common.models import NewsModel, NewsCategoryModel
from bpms.workgroups.models import WorkgroupModel

from common.redis import socketio_redis
from notifications.models import (EmailNotificationModel,
                                  EmailNotificationRecipientModel)
from notifications.utils import send_email
from users.models import ProfileModel

from . import models, serializers


def get_news_short_content(content):
    short_content = ''
    if content:
        soup = BeautifulSoup(content)
        short_content = soup.get_text(' ', strip=True)[:500]
        if not short_content.__len__() < 500:
            short_content = '{}...'.format(short_content)
    return short_content


def send_socketio_about_new_news(news):
    from .serializers import NewsListSerializer
    s_data = NewsListSerializer(instance=news).data
    data = json.dumps({
        'event': 'news_create',
        'data': s_data,
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    return 'message sent'


def send_dealers_email_news_notification(news):
    '''
    Рассылко по email для диллеров о появлении новости на рабочем столе.
    '''

    from .serializers import NewsListSerializer

    news_data = NewsListSerializer(instance=news).data
    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    context['url'] = f'{FRONTEND_URL}/'
    context['title'] = news_data['title']
    context['content'] = news_data['content']

    notification = EmailNotificationModel.objects.create(template='email_news_notification',
                                                         subject='Свежая новость!',
                                                         context=context)
    all_recepients = ProfileModel.objects.filter(is_active=True,
                                                 temporary_blocked=False,
                                                 profile_type__code='dealer').distinct()
    
    list_objects = [EmailNotificationRecipientModel(
        email_notification=notification,
        recipient=recepient.user.email) for recepient in all_recepients]
    
    EmailNotificationRecipientModel.objects.bulk_create(list_objects)
    
    send_email(notification.id)


def get_news_filters(request):
    try:
        checked_objects = models.CheckedNewsCategoryModel.objects.get(user=request.user.profile)
    except models.CheckedNewsCategoryModel.DoesNotExist:
        checked_categories = []
        checked_workgroups = []
    else:
        checked_categories_data = checked_objects.data
        if checked_categories_data:
            checked_categories = checked_categories_data.get('categories', [])
            checked_workgroups = checked_categories_data.get('workgroups', [])
        else:
            checked_categories = []
            checked_workgroups = []
    categories = NewsCategoryModel.objects.filter(is_active=True).order_by('sort', 'name')
    categories_list = serializers.NewsFilterCategoryModelSerializer(
        categories, many=True, context={"checked_categories": checked_categories}
    ).data
    my_workgroups = get_my_workgroups(request)
    workgroups_list = serializers.NewsCategoryWorkgroupSerializer(
        my_workgroups, many=True, context={"checked_workgroups": checked_workgroups}
    ).data
    return categories_list + workgroups_list


def get_my_workgroups(request):
    return WorkgroupModel.prepare_queryset(request).filter(
        is_user__gt=0).order_by('is_finished', 'name', '-created_at')
