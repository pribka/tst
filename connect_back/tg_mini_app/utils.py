import hmac
import json
from urllib.parse import parse_qsl
from hashlib import sha256

from django.core import exceptions as django_exceptions

from bkz3.local_settings import TG_BOT_TOKEN


def get_telegram_id(init_data):
    parsed_data = dict(parse_qsl(init_data))
    received_hash = parsed_data.pop('hash', None)

    if not received_hash:
        raise django_exceptions.ValidationError('Hash missing',)

    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hmac.new(b'WebAppData', TG_BOT_TOKEN.encode(), sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()

    if computed_hash != received_hash:
        raise django_exceptions.PermissionDenied('Invalid hash', )
    try:
        user_json = json.loads(parsed_data.get('user', '{}'))
    except json.JSONDecodeError:
        raise django_exceptions.ValidationError('Invalid user JSON')

    telegram_id = user_json.get('id')
    if not telegram_id:
        raise django_exceptions.ValidationError('No Telegram ID')
    return telegram_id


