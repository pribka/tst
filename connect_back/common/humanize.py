import datetime

import pytz

from bkz3.settings import TIME_ZONE
from django.utils.translation import gettext as _


def get_humanized_timezone(timezone_code: str = TIME_ZONE, value: datetime.datetime = None) -> str:
    timezone_code = timezone_code or TIME_ZONE
    try:
        timezone_value = pytz.timezone(timezone_code)
    except pytz.UnknownTimeZoneError:
        return f'UTC ({timezone_code})'

    if value is None:
        reference_datetime = datetime.datetime.now(datetime.timezone.utc)
    elif value.tzinfo is None:
        reference_datetime = pytz.utc.localize(value)
    else:
        reference_datetime = value
    local_datetime = reference_datetime.astimezone(timezone_value)
    offset_value = local_datetime.strftime('%z')
    offset_humanized = f'{offset_value[:3]}:{offset_value[3:]}' if offset_value else '+00:00'
    return _('по времени UTC%(offset)s (%(timezone)s)') % {
        'offset': offset_humanized,
        'timezone': timezone_code,
    }


HUMANIZED_MONTHS = {
    1: _('январь'),
    2: _('февраль'),
    3: _('март'),
    4: _('апрель'),
    5: _('май'),
    6: _('июнь'),
    7: _('июль'),
    8: _('август'),
    9: _('сентябрь'),
    10: _('октябрь'),
    11: _('ноябрь'),
    12: _('декабрь'),
}


def get_humanized_month(month: int) -> str:
    result = HUMANIZED_MONTHS.get(month)
    return result


def get_humanized_month_year(date: datetime.date):
    month = date.month
    return f"{get_humanized_month(month)} {date.year} г"




