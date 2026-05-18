import os
import django
from django.apps import apps
from telegram_bot.base import base_bot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()


@base_bot.message_handler(regexp=r'^/start\s+')
def handle_message(message):
    chat_id = message.chat.id
    token = message.text.split(' ')[-1]
    profile_model = apps.get_model('users', 'ProfileModel')

    profile = profile_model.objects.get(telegram_connect_token=token)
    if not profile.telegram_id:
        profile.telegram_id = chat_id
        profile.save()
        welcome_message = 'Добро пожаловать!\nПрофиль успешно подтвержден'
    else:
        welcome_message = 'Ваш аккаунт уже привязан!'
    base_bot.send_message(chat_id=chat_id,
                          text=welcome_message)


if __name__ == '__main__':
    base_bot.polling(none_stop=True)
