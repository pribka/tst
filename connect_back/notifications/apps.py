from django.apps import AppConfig
from django.db.utils import ProgrammingError
import sys


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        # Во время schema-команд (migrate и т.п.) Django тоже вызывает ready().
        # Здесь делаем обход: пропускаем стартовую синхронизацию уведомлений,
        # чтобы не дергать cache/redis до завершения миграций.
        management_commands = {'migrate', 'makemigrations', 'showmigrations', 'sqlmigrate'}
        if any(arg in management_commands for arg in sys.argv[1:]):
            return

        from notifications.models import EventTypeModel, NotificationCategoryModel
        from notifications.event_types import BaseEventType
        from notifications.category_registry import NOTIFICATION_CATEGORIES
        try:
            # Синхронизируем категории из реестра
            current_category_codes = set()
            for category_code, category_data in NOTIFICATION_CATEGORIES.items():
                current_category_codes.add(category_code)
                NotificationCategoryModel.objects.update_or_create(
                    code=category_code,
                    defaults={
                        'name_ru': category_data['name_ru'],
                        'name_kk': category_data['name_kk'],
                        'sort': category_data['sort'],
                        'is_active': True,
                    }
                )

            # Удаляем категории, которых больше нет в реестре
            NotificationCategoryModel.objects.exclude(
                code__in=current_category_codes
            ).update(is_active=False)

            # Синхронизируем event types
            current_event_type_codes = set()
            for each in BaseEventType.__subclasses__():
                current_event_type_codes.add(each.code)
                category = None
                if each.category_code:
                    category = NotificationCategoryModel.objects.get(code=each.category_code)
                is_mention = getattr(each, 'is_mention', False)
                defaults = {
                    'color': each.color,
                    'icon': each.icon,
                    'template_html': each.template_html,
                    'template_text': each.template_text,
                    'template_html_ru': each.template_html,
                    'template_text_ru': each.template_text,
                    'template_html_kk': each.template_html_kk,
                    'template_text_kk': each.template_text_kk,
                    'name_ru': each.verbose_name,
                    'name_kk': each.verbose_name_kk,
                    'url': each.url,
                    'category': category,
                    'show_in_settings': each.show_in_settings,
                    'default_enabled': each.default_enabled,
                    'is_active': True,
                    'is_mention': is_mention
                }

                EventTypeModel.objects.update_or_create(
                    code=each.code,
                    defaults=defaults
                )

            # Удаляем event types, которых больше нет в коде
            EventTypeModel.objects.exclude(
                code__in=current_event_type_codes
            ).update(is_active=False)
        except ProgrammingError:
            pass



