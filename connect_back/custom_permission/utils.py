from django.core.exceptions import PermissionDenied
from common.current_profile.middleware import get_current_user
from django.contrib.contenttypes.models import ContentType
from .models import UserAccessProfileModel, SessionParameterModel


def check_custom_permission(viewset, access_type, request=None):
    ct = ContentType.objects.get_for_model(viewset.model)
    user = get_current_user()

    # Вытащим заготовку таблицы прав для пользователя с вычислением шаблона доступа по параметру access_type

    access = UserAccessProfileModel.objects.filter(user=user,
                                                   access_profile__roles__access__ct=ct,
                                                   )

    # Определим целевой тип доступа
    target_field = 'access_profile__roles__access__' + access_type
    access = access.filter(**{target_field: True})

    # Вытащим все указанные шаблоны ограничений
    access = access.values(
        target_field + '_template__target_field',
        target_field + '_template', ).distinct()

    # Так как поля М2М, то сгруппируем повторы одних и тех же шаблонов
    access = access.distinct(target_field + '_template__target_field',
                             target_field + '_template', )

    # Отсортируем так, чтобы вероятное NULL-значение шаблона оказалось сверху,
    # тогда не будем обрабатывать дофильтровку по шаблону,
    # так как отсутствие шаблона снимает ограничение на уровне записей
    access = access.order_by('-' + target_field + '_template')

    # TODO отключаю контроль для суперюзера, чтобы сюрприза не произошло на тестовом серваке.
    if access.exists() or getattr(user, 'is_superuser', False):
        # Если  есть хоть одна запись True

        # получим заводской кверисет
        queryset = viewset.model.get_queryset(request)

        # Определим параметры сессии для текущего пользователя, если нет, то создадим
        session_params, created = SessionParameterModel.objects.get_or_create(user=user)
        for each in access:
            # TODO суперюзеру пока ничего не режем
            if getattr(user, 'is_superuser', False):
                continue

            # Фильтруем только если есть шаблон ограничения
            if each[target_field + '_template'] is not None:
                # Получаем поле, по которому фильтруем кверисет
                filtering_field = each[target_field + '_template__target_field']

                # Получаем значение фильтра из параметра сессии
                filtering_value = getattr(session_params, each[target_field + '_template__target_field'])

                # Режем кверисет
                queryset = queryset.filter(
                    **{filtering_field + '__in': filtering_value.all()}
                )

        return queryset  # Готово

    else:
        # Если  нет ролей с целевым типом прав, деликатно вызываем 403
        raise PermissionDenied()
