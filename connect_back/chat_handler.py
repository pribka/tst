#!/usr/bin/env python
import os
import django
import json
from time import sleep
import redis
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from common.redis import socketio_redis
from bpms.chat.utils import ChatHandler


def _handle_chat_data():
    while True:
        key, data = socketio_redis.blpop('events', 0)
        data_dict = json.loads(data)
        print(data_dict)
        try:
            ChatHandler().select_handler(name=data_dict.get('event'), data=data_dict.get('data'))
        except Exception as ex:
            print(str(ex))


_handle_chat_data()
