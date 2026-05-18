import json
import re

from django.core import validators, exceptions
from django.core.exceptions import ValidationError
from django.core.validators import _lazy_re_compile
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

iin_validator = validators.RegexValidator(
    _lazy_re_compile(r'^-?\d{12}\Z'),
    message=_('Enter a valid iin.'),
    code='invalid', )


def validate_text_to_json(value):
    try:
        json.loads(value)
    except json.JSONDecodeError:
        raise exceptions.ValidationError(
            _('Value must be valid JSON.'),
            code='invalid',
            params={'value': value},
        )


class MaxCurrentYearValidator(validators.MaxValueValidator):
    message = _('Дата постройки не может быть больше текущего года.')
    code = 'max_current_year'

    def compare(self, a, b):
        b = timezone.localdate().year
        return a > b


class MinValueOrNoneValidator(validators.MinValueValidator):
    code = 'min_value_or_none'

    def compare(self, a, b):
        if a is not None:
            return super().compare(a, b)
        else:
            return False


class MaxValueOrNoneValidator(validators.MaxValueValidator):
    code = 'max_value_or_none'

    def compare(self, a, b):
        if a is not None:
            return super().compare(a, b)
        else:
            return False


def normalize_kz_bin(value):
    return re.sub(r'\D', '', str(value or '').strip())


def _calc_kz_bin_checksum(first_11_digits: str, second_cycle: bool = False) -> int:
    if second_cycle:
        weights = (3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2)
    else:
        weights = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    return sum(int(digit) * weight for digit, weight in zip(first_11_digits, weights)) % 11


def kz_bin_validator(value):
    normalized = normalize_kz_bin(value)

    if not normalized:
        return

    if len(normalized) != 12:
        raise ValidationError(_('БИН должен содержать 12 цифр'))

    if not normalized.isdigit():
        raise ValidationError(_('БИН должен содержать только цифры'))

    first_11 = normalized[:11]
    fact_checksum = int(normalized[11])

    expected_checksum = _calc_kz_bin_checksum(first_11)

    if expected_checksum == 10:
        expected_checksum = _calc_kz_bin_checksum(first_11, second_cycle=True)

    if expected_checksum == 10 or fact_checksum != expected_checksum:
        raise ValidationError(_('Некорректный БИН'))
