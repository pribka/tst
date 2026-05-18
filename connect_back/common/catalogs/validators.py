from django.core.exceptions import ValidationError


def inn_validator(value):
    if not ((len(value) == 12 and value.isdigit()) or
            value == ''):
        raise ValidationError('ИНН юридического лица должен быть '
                              'последовательностью из 12 цифр.')


def kpp_validator(value):
    if not ((len(value) == 9 and value.isdigit()) or
            value == ''):
        raise ValidationError('КПП юридического лица должен быть '
                              'последовательностью из 9 арабских цифр.')


def ogrn_validator(value):
    if not ((len(value) == 13 and
             value.isdigit() and
             (value.startswith('1') or value.startswith('5'))) or
            value == ''):
        raise ValidationError('ОГРН юридического лица должен быть '
                              'последовательностью из 13 арабских цифр. '
                              'Первая цифра 1 или 5.')


def ogrnip_validator(value):
    if not ((len(value) == 15 and
             value.isdigit() and
             value.startswith('3')) or
            value == ''):
        raise ValidationError('ОГРНИП индивидуального предпринимателя '
                              'должен быть последовательностью из 15 '
                              'арабских цифр. Первая цифра 3.')


def okpo_validator(value):
    if not (((len(value) == 8 or len(value) == 10) and
             value.isdigit()) or
            value == ''):
        raise ValidationError('ОКПО должен быть последовательностью из '
                              '8 арабских цифр для организаций и из 10 '
                              'арабских цифр для индивидуальных '
                              'предпринимателей.')


def bank_account_validator(value):
    if not ((len(value) == 20 and
            value.isdigit() and
            (value.startswith('405') or
             value.startswith('406') or
             value.startswith('407'))) or
            value == ''):
        raise ValidationError('Расчетный счет юридического лица должен '
                              'быть последовательностью из 20 арабских '
                              'цифр, первая цифра 405, 406 или 407.')


def correspondent_account_validator(value):
    if not ((len(value) == 20 and
             value.isdigit() and
             value.startswith('301')) or
            value == ''):
        raise ValidationError('Корреспондентский счет юридического лица '
                              'должен быть последовательностью из 20 '
                              'арабских цифр, первая цифра 301.')


def bik_validator(value):
    if not ((len(value) == 9 and
             value.isdigit() and
             value.startswith('04')) or
            value == ''):
        raise ValidationError('Банковский идентификационный код должен '
                              'быть последовательностью из 9 арабских '
                              'цифр, первые цифры 04.')
