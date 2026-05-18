from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from rest_framework import status
from rest_framework import exceptions as drf_exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from common.paginators import CustomPagination
from common.utils import get_my_access_groups

from users.models import ProfileModel
from users.serializers import ProfileDetailSerializer

from bpms.bpms_common.permissions import IsSuperUserOrReadOnly

from . import models, serializers, utils

from ..tasks.models import TaskModel
from ..workgroups.models import WorkgroupMembersModel
from ..workgroups.serializers import WorkgroupMembersSerializer


class UserWidgetView(ModelViewSet):

    def get_queryset(self):
        category = self.request.query_params.get("category")
        if category is not None:
            query = models.WidgetCatalog.objects.raw(
                'SELECT widgets_widgetcatalog.basecatalog_ptr_id,'
                'widgets_userwidgetmodel.basemodel_ptr_id as "user_widget_id",'
                'widgets_widgetcatalog.component_name, common_basemodel.sort as '
                'widget_catalog_sort, widgets_userwidgetmodel.category as "user_widget_category", '
                'widgets_widgetcatalog.code,widgets_widgetcatalog.icon_name,'
                'common_basecatalog.name as "widget_name", COALESCE(common_basemodel.sort,0)'
                ' as user_widget_sort,COALESCE( widgets_userwidgetmodel.column,1)'
                'as user_widget_column FROM widgets_widgetcatalog LEFT '
                ' JOIN widgets_userwidgetmodel '
                'ON (widgets_widgetcatalog.basecatalog_ptr_id=widgets_userwidgetmodel.widget_id) '
                'and widgets_userwidgetmodel.user_id=%s LEFT JOIN common_basemodel'
                ' ON common_basemodel.id = widgets_userwidgetmodel.basemodel_ptr_id'
                ' LEFT JOIN common_basecatalog on common_basemodel.id = common_basecatalog.basemodel_ptr_id '
                ' WHERE widgets_userwidgetmodel.category=%s',
                [self.request.user.profile.id, category])
            return query
        else:
            query = models.WidgetCatalog.objects.raw(
                'SELECT widgets_widgetcatalog.basecatalog_ptr_id,widgets_userwidgetmodel.basemodel_ptr_id '
                'as "user_widget_id",widgets_widgetcatalog.component_name, common_basemodel.sort as '
                'widget_catalog_sort,widgets_userwidgetmodel.category as "user_widget_category", '
                'widgets_widgetcatalog.code,widgets_widgetcatalog.icon_name,'
                'common_basecatalog.name as "widget_name",'
                'COALESCE(common_basemodel.sort,0) as user_widget_sort,COALESCE( '
                'widgets_userwidgetmodel.column,1) as user_widget_column FROM widgets_widgetcatalog LEFT '
                'JOIN widgets_userwidgetmodel ON  ('
                'widgets_widgetcatalog.basecatalog_ptr_id=widgets_userwidgetmodel.widget_id) '
                'AND widgets_userwidgetmodel.user_id=%s'
                ' LEFT JOIN common_basemodel on common_basemodel.id = widgets_userwidgetmodel.basemodel_ptr_id '
                ' LEFT JOIN common_basecatalog on common_basemodel.id = common_basecatalog.basemodel_ptr_id '
                , [self.request.user.profile.id])
            return query

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'GET':
            return serializers.WidgetSerializer
        return serializers.UserWidgetSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.get("items") if 'items' in request.data else request.data
        arr = []
        for item in data:
            serializer = self.get_serializer_class()
            serializer = serializer(data=item)
            serializer.is_valid(raise_exception=True)
            serializer.save(is_active=True, user=request.user.profile)
            arr.append(serializer.data)
        return Response(arr, status=status.HTTP_201_CREATED)

    @action(methods=["put"], detail=False, url_path="put",
            url_name="put_widgets")
    def put_widgets(self, request):
        """Изменение  пользовательских виджетов меняем column,sort,widget"""
        widgets = []
        for item in request.data:
            widget = models.UserWidgetModel.objects.get(id=item['id'], user=request.user.profile, is_active=True)
            widget.column = item['column']
            widget.sort = item['sort']
            widget.user = request.user.profile
            widget.widget = models.WidgetCatalog.objects.get(id=item['widget'], is_active=True)
            widget.category = item['category']
            serializer = self.get_serializer_class()
            widget_serializer = serializer(widget, data=item, partial=True)
            if widget_serializer.is_valid():
                widget.save()
                widgets.append(widget_serializer.data)
        return Response(data=widgets, status=status.HTTP_200_OK)

    # TODO добавить к профилю ДР
    @action(methods=["get", ], detail=False, url_path="birthdays",
            url_name="get_birthdays")
    def get_birthdays(self, request):
        """Вывод 5 ближайших дней рождений """
        queryset = ProfileModel.objects.filter(is_active=True, birth_date__gte=timezone.now())[:5]
        serializer = ProfileDetailSerializer(queryset, many=True).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=False, url_path="work_groups",
            url_name="get_workgroups")
    def get_workgroups(self, request):
        """Вывод 6 моих рабочих групп"""
        queryset = WorkgroupMembersModel.objects.filter(is_active=True, student=request.user.profile).order_by(
            "-created")[:6]
        serializer = WorkgroupMembersSerializer(queryset, many=True).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=False, url_path="my_tasks",
            url_name="get_my_tasks")
    def get_my_tasks(self, request):
        """Вывод моих задач"""
        queryset = TaskModel.objects.all()[:1]
        serializer = serializers.MyTasksWidgetSerializer(queryset, many=True, context={'request': request}).data
        return Response(data=serializer, status=status.HTTP_200_OK)


class WidgetCategoryViewSet(ModelViewSet):
    queryset = models.WidgetCategoryModel.objects.filter(is_active=True)
    serializer_class = serializers.WidgetCategorySerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user.profile
        available_categories = utils.filter_permission_widgets(
            user,
            models.WidgetModel.objects.filter(is_active=True),
            show_in_list=True
        ).values('category').distinct('category')
        qs = qs.filter(pk__in=available_categories)
        return qs

    @action(detail=True, methods=['get'])
    def widgets(self, request, pk=None):
        category = self.get_object()
        widgets = category.widgets.filter(is_active=True)
        widgets = utils.filter_permission_widgets(request.user.profile, widgets, show_in_list=True)
        serializer = serializers.WidgetModelReadSerializer(widgets, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Получите виджеты в данной категории
        widgets = instance.widgets.filter(is_active=True)
        widgets = utils.filter_permission_widgets(request.user.profile, widgets, show_in_list=True)
        widget_serializer = serializers.WidgetModelReadSerializer(widgets, many=True)

        data = serializer.data
        data['widgets'] = widget_serializer.data

        return Response(data)


class WidgetViewSet(ModelViewSet):
    queryset = models.WidgetModel.objects.filter(is_active=True).order_by('sort')
    pagination_class = CustomPagination
    permission_classes = [IsSuperUserOrReadOnly]

    def get_queryset(self):

        queryset = utils.filter_permission_widgets(self.request.user.profile, self.queryset, show_in_list=True)
        # Получите параметры запроса для фильтрации
        category_id = self.request.query_params.get('category')
        name = self.request.query_params.get('name')

        is_mobile = self.request.query_params.get('is_mobile')
        is_desktop = self.request.query_params.get('is_desktop')

        if is_desktop:
            queryset = queryset.filter(is_desktop=True)

        if is_mobile:
            queryset = queryset.filter(is_mobile=True)

        # Примените фильтры на основе параметров запроса
        if category_id:
            # Фильтрация по полю 'category'
            queryset = queryset.filter(category_id=category_id)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return serializers.WidgetModelReadSerializer

        return serializers.WidgetModelWriteSerializer


class DesktopTemplateViewSet(ModelViewSet):
    queryset = models.DesktopTemplateModel.objects.filter(is_active=True).order_by('sort', 'name',)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user.profile
        access_groups = set(get_my_access_groups(user).values_list('pk', flat=True))
        queryset = queryset.filter(access_groups__in=access_groups,).distinct()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return serializers.DesktopTemplateReadSerializer
        return serializers.DesktopTemplateWriteSerializer

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Получите виджеты, связанные с данным шаблоном рабочего стола
        widgets = instance.default_widgets.all()
        widget_serializer = serializers.WidgetModelReadSerializer(widgets, many=True)

        data = serializer.data
        data['widgets'] = widget_serializer.data

        return Response(data)

    @action(detail=False, methods=['post'], url_path='copy-from-desktop', url_name='copy_from_desktop')
    def copy_from_desktop(self, request):
        """
        Копирует виджеты с рабочего стола пользователя в шаблон для новых пользователей.
        Только для администраторов.
        desktop - id пользовательского рабочего стола
        desktop_template - id шаблона рабочего стола, который будет изменен. Если desktop_template отсутствует, будет
        создан новый шаблон.
        """
        # Проверка на администратора
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only administrators can perform this action'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        desktop_id = request.data.get('desktop')
        if not desktop_id:
            return Response(
                {'detail': 'desktop_template field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Получаем экземпляр рабочего стола пользователя
            user_desktop = models.UserDesktopModel.objects.get(id=desktop_id)
        except models.UserDesktopModel.DoesNotExist:
            return Response(
                {'detail': 'Desktop not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Получаем шаблон рабочего стола
        desktop_template_id = request.data.get('desktop_template')
        if desktop_template_id:
            try:
                template = models.DesktopTemplateModel.objects.get(pk=desktop_template_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError(f'Desktop_template "{desktop_template_id}" not found.')
        else:
            template = None

        with transaction.atomic():
            if template:
                # Полностью очищаем данные в DesktopTemplateWidgetOnDesktopModel
                models.DesktopTemplateWidgetOnDesktopModel.objects.filter(desktop=template).delete()
            else:
                template = models.DesktopTemplateModel()
            template.name_ru = user_desktop.name_ru
            template.name_kk = user_desktop.name_kk
            template.save()
            # Получаем связанные виджеты с рабочего стола пользователя
            user_widgets = models.UserWidgetOnDesktopModel.objects.filter(
                desktop=user_desktop, 
                is_active=True
            ).order_by('sort')

            # Копируем виджеты в шаблон
            copied_widgets = []
            for user_widget in user_widgets:
                template_widget = models.DesktopTemplateWidgetOnDesktopModel(
                    name=user_widget.name,
                    sort=user_widget.sort,
                    x=user_widget.x,
                    y=user_widget.y,
                    w=user_widget.w,
                    h=user_widget.h,
                    i=user_widget.i,
                    static=user_widget.static,
                    widget=user_widget.widget,
                    desktop=template,
                    mobile_index=user_widget.mobile_index,
                    is_mobile=user_widget.is_mobile,
                    is_desktop=user_widget.is_desktop,
                    random_settings=user_widget.random_settings,
                )
                template_widget.save()
                copied_widgets.append(template_widget)

        return Response(
            {
                'message': f'Successfully copied {len(copied_widgets)} widgets from desktop {user_desktop.name} to template {template.name}',
                'copied_widgets_count': len(copied_widgets),
                'template_id': str(template.id),
                'source_desktop_id': str(user_desktop.id)
            },
            status=status.HTTP_200_OK
        )


class UserWidgetOnDesktopViewSet(ModelViewSet):
    queryset = models.UserWidgetOnDesktopModel.objects.all()
    serializer_class = serializers.UserWidgetOnDesktopSerializer

    def get_queryset(self):
        user = self.request.user

        desktop_id = self.request.query_params.get('desktop')
        queryset = models.UserWidgetOnDesktopModel.objects.filter(
            desktop__author=user.profile,
            is_active=True
        ).order_by('sort')

        if desktop_id:
            queryset = queryset.filter(desktop=desktop_id)

        return queryset

    @action(detail=True, methods=['get'])
    def actions(self, request, *args, **kwargs):
        instance = self.get_object()
        widget = instance.widget
        # Создайте пустой словарь
        data = {
            'actions': {
                'config': {'availability': widget.may_config},
                'pin': {'availability': widget.may_pin},
                'delete': {'availability': widget.may_delete},
            }
        }
        return Response(data)


class UserDesktopViewSet(ModelViewSet):
    queryset = models.UserDesktopModel.objects.all()
    serializer_class = serializers.UserDesktopSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def get_queryset(self):
        user = self.request.user.profile

        access_groups = set(get_my_access_groups(user).values_list('pk', flat=True))
        if access_groups:
            desktop_templates = set(models.DesktopTemplateAccessGroupThrough.objects.filter(
                access_group_id__in=access_groups,
            ).values_list('desktop_template', flat=True))
            if desktop_templates:
                exclude_desktop_templates = set(
                    models.DesktopTemplateAccessGroupThrough.objects.exclude(
                        desktop_template_id__in=desktop_templates
                    ).values_list(
                        'desktop_template',
                        flat=True
                    )
                )
                have_desktop_templates = set(
                    models.UserDesktopModel.objects.filter(
                        author=user,
                        desktop_template__in=desktop_templates
                    ).exclude(
                        desktop_template__in=exclude_desktop_templates
                    ).values_list(
                        'desktop_template',
                        flat=True
                    )
                )
                missing_desktop_templates = desktop_templates - have_desktop_templates
                for each in missing_desktop_templates:
                    utils.create_desktop_from_template(user.pk, each)
                return models.UserDesktopModel.objects.filter(
                    author=user,
                    is_active=True,
                ).exclude(desktop_template_id__in=exclude_desktop_templates).order_by('sort', 'created_at',)
        return models.UserDesktopModel.objects.filter(
            author=user,
            is_active=True
        ).order_by('sort', 'created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if queryset.count() > 0:
            return super().list(request, *args, **kwargs)
        else:
            template = utils.get_default_desktop_template()
            
            if template:
                # Проверяем, есть ли уже рабочий стол с данным шаблоном
                existing_desktop = models.UserDesktopModel.objects.filter(
                    author=request.user.profile,
                    desktop_template=template,
                    is_active=True
                ).first()
                
                if not existing_desktop:
                    desktop = utils.create_desktop_from_template(
                        request.user.profile.pk, 
                        str(template.id)
                    )

        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def widgets(self, request, pk=None):
        desktop = self.get_object()
        available_widgets = utils.filter_permission_widgets(
            self.request.user.profile,
            models.WidgetModel.objects.filter(is_active=True),
        ).values_list('pk', flat=True).distinct()
        widgets = models.UserWidgetOnDesktopModel.objects.filter(
            desktop=desktop,
            is_active=True,
            widget_id__in=available_widgets,
        ).order_by('sort')
        serializer = serializers.UserWidgetOnDesktopSerializer(widgets, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.serialize_object(instance)

        return Response(data)

    def serialize_object(self, instance):
        serializer = self.get_serializer(instance)

        # Получите виджеты для рабочего стола
        available_widgets = utils.filter_permission_widgets(
            self.request.user.profile,
            models.WidgetModel.objects.filter(is_active=True)
        ).values_list('pk', flat=True).distinct()
        widgets = models.UserWidgetOnDesktopModel.objects.filter(
            desktop=instance,
            is_active=True,
            widget_id__in=available_widgets,
        ).order_by('sort')

        is_mobile = self.request.query_params.get('is_mobile')
        is_desktop = self.request.query_params.get('is_desktop')

        if is_desktop:
            widgets = widgets.filter(is_desktop=True)

        if is_mobile:
            widgets = widgets.filter(is_mobile=True)

        widget_serializer = serializers.UserWidgetOnDesktopSerializer(widgets, many=True)
        data = serializer.data
        data['widgets'] = widget_serializer.data

        return data

    def create(self, request, *args, **kwargs):

        desktop_template = request.data.get('desktop_template')

        if desktop_template and len(request.data['desktop_template']) == 36:
            # Вызовите метод create_from_template
            return self.create_from_template(request)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def create_from_template(self, request):
        template_id = request.data.get('desktop_template')
        widget_ids = request.data.get('widgets')
        
        try:
            new_desktop = utils.create_desktop_from_template(
                request.user.profile.pk,
                template_id, 
                widget_ids,
                name=request.data.get('name')
            )
            data = self.serialize_object(new_desktop)
            return Response(data, status=201)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

    @action(detail=False, methods=['put'])
    def sort_list(self, request):

        data = request.data.get('desktops', [])
        sch = 1

        with transaction.atomic():
            for item in data:
                desktop = models.UserDesktopModel.objects.filter(author=request.user.profile, id=item).first()

                if desktop is None:
                    return Response({'detail': f'Not your desktop'}, status=status.HTTP_403_FORBIDDEN)

                desktop.sort = sch
                desktop.save()
                sch += 1

        return Response(request.data)

    @action(detail=True, methods=['put'])
    def location(self, request, pk=None):
        desktop = self.get_object()
        if desktop.author != request.user.profile:
            return Response({'detail': f'Not your desktop'}, status=status.HTTP_403_FORBIDDEN)

        widget_data = request.data.get('widgets', [])
        widgets = desktop.widgets.filter(is_active=True)

        with transaction.atomic():
            for item in widgets:
                item.is_active = False
                item.save()
            for widget_info in widget_data:
                widget_id = widget_info.get('id')
                if widget_id is not None:
                    try:
                        widget = models.UserWidgetOnDesktopModel.objects.get(id=widget_id, desktop=desktop)
                        widget.x = widget_info.get('x', widget.x)
                        widget.y = widget_info.get('y', widget.y)
                        widget.is_desktop = widget_info.get('is_desktop', widget.is_desktop)
                        widget.is_mobile = widget_info.get('is_mobile', widget.is_mobile)
                        widget.w = widget_info.get('w', widget.w)
                        widget.h = widget_info.get('h', widget.h)
                        widget.i = widget_info.get('i', widget.i)
                        widget.mobile_index = widget_info.get('mobile_index', widget.mobile_index)
                        widget.static = widget_info.get('static', widget.static)
                        widget.is_active = True
                        widget.save()
                    except models.UserWidgetOnDesktopModel.DoesNotExist:
                        return Response({'detail': f'Widget with id {widget_id} not found on this desktop'},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    widget = models.UserWidgetOnDesktopModel()
                    widget.desktop = desktop
                    widget.widget_id = widget_info.get('widget_catalog_id')
                    widget.x = widget_info.get('x', widget.x)
                    widget.y = widget_info.get('y', widget.y)
                    widget.w = widget_info.get('w', widget.w)
                    widget.h = widget_info.get('h', widget.h)
                    widget.i = widget_info.get('i', widget.i)
                    widget.is_desktop = widget_info.get('is_desktop', widget.is_desktop)
                    widget.mobile_index = widget_info.get('mobile_index', widget.mobile_index)
                    widget.is_mobile = widget_info.get('is_mobile', widget.is_mobile)
                    widget.static = widget_info.get('static', widget.static)
                    widget.is_active = True
                    widget.save()

        # return Response(widget_data)
        data = self.serialize_object(desktop)
        # widgets = UserWidgetOnDesktopModel.objects.filter(desktop=desktop, is_active=True)
        # serializer = UserWidgetOnDesktopSerializer(widgets, many=True)

        return Response(data)
