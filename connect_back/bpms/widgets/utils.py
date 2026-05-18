from django.core import serializers
from django.db.models import Q

from common.utils import get_available_app_section_roles_through

from .models import WidgetCategoryModel, WidgetModel, DesktopTemplateModel, DesktopTemplateWidgetOnDesktopModel, \
    UserDesktopModel, UserWidgetOnDesktopModel
from common.models import BaseCatalog, BaseModel


def go():
    # Assuming you have querysets for each model, e.g., QuerysetCategory, QuerysetWidget, etc.
    # Create querysets for each model
    category_queryset = WidgetCategoryModel.objects.all()
    widget_queryset = WidgetModel.objects.all()
    template_queryset = DesktopTemplateModel.objects.all()
    desktop_widget_queryset = DesktopTemplateWidgetOnDesktopModel.objects.all()

    # Serialize the models into JSON
    category_json = serializers.serialize('json', category_queryset)
    widget_json = serializers.serialize('json', widget_queryset)
    template_json = serializers.serialize('json', template_queryset)
    desktop_widget_json = serializers.serialize('json', desktop_widget_queryset)

    # Combine all querysets into one list
    all_lists = list(category_queryset) + list(widget_queryset) + list(template_queryset) + list(
        desktop_widget_queryset)

    # Extract primary key (pk) values from the models
    pk_values = [item.pk for item in all_lists]

    basecatalog_json = serializers.serialize('json', BaseCatalog.objects.filter(pk__in=pk_values))
    basemodel_json = serializers.serialize('json', BaseModel.objects.filter(pk__in=pk_values))

    # Concatenate the JSON strings
    all_data = f'{basemodel_json}\n{basecatalog_json}\n{category_json}\n{widget_json}\n{template_json}\n{desktop_widget_json}'

    # Define the filename for the single file
    output_filename = 'all_data.json'

    # Write the concatenated JSON data to the single file
    with open(output_filename, 'w') as output_file:
        output_file.write(all_data)


def get_default_desktop_template():
    template = DesktopTemplateModel.objects.filter(default=True).order_by('-created_at').first()
    return template


def create_desktop_from_template(profile_id, template_id, widget_ids=None, name=None):
    from bpms.widgets.models import DesktopTemplateModel, UserDesktopModel, UserWidgetOnDesktopModel
    from django.db import transaction
    
    try:
        template = DesktopTemplateModel.objects.get(pk=template_id)
    except DesktopTemplateModel.DoesNotExist:
        raise ValueError('Template not found')

    if name is None:
        name = template.name
    
    with transaction.atomic():
        # Создаем новый рабочий стол
        new_desktop = UserDesktopModel(
            desktop_template=template,
            name=name,
            draggable=template.draggable,
            resizable=template.resizable,
            margin_x=template.margin_x,
            margin_y=template.margin_y,
            vertical_compact=template.vertical_compact,
            use_css_transforms=template.use_css_transforms,
            author_id=profile_id
        )
        new_desktop.save()
        
        # Копируем виджеты
        widgets = template.default_widgets.all()
        if widget_ids:
            widgets = widgets.filter(widget_id__in=widget_ids)
            
        for widget in widgets:
            new_widget = UserWidgetOnDesktopModel(
                name=widget.widget.name,
                name_ru=widget.widget.name_ru,
                name_kk=widget.widget.name_kk,
                widget=widget.widget,
                desktop=new_desktop,
                x=widget.x,
                y=widget.y,
                w=widget.w,
                h=widget.h,
                i=widget.i,
                mobile_index=2,
                is_mobile=widget.is_mobile,
                is_desktop=widget.is_desktop,
                random_settings=widget.random_settings,
            )
            new_widget.save()
    
    return new_desktop


def filter_permission_widgets(profile, queryset, show_in_list=None):
    """Фильтрует список виджетов по правам пользователя"""
    available_section_roles = get_available_app_section_roles_through(profile)
    if show_in_list:
        lookup = Q(
            app_section_roles_through__in=available_section_roles,
            show_in_list=True,
        )
    else:
        lookup = Q(
            app_section_roles_through__in=available_section_roles,
        )
    if profile.is_support:
        lookup = lookup | Q(for_support=True)
    queryset = queryset.filter(lookup)
    return queryset
