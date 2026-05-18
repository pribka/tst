from django.contrib import admin

from . import models


class AppSectionRoleThroughInline(admin.TabularInline):
    model = models.WidgetAppSectionRoleThrough
    fields = (
        'app_section_role',
    )
    extra = 0
    fk_name = 'widget'
    ordering = ('app_section_role__app_section__name',)


class AccessGroupDesktopTemplateThroughInline(admin.TabularInline):
    model = models.DesktopTemplateAccessGroupThrough
    fields = (
        'access_group',
    )
    extra = 0
    fk_name = 'desktop_template'
    ordering = ('access_group__name',)
    autocomplete_fields = ('access_group',)


@admin.register(models.WidgetCatalog)
class WidgetAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ['name']


@admin.register(models.UserWidgetModel)
class UserWidgetAdmin(admin.ModelAdmin):
    autocomplete_fields = ('user', 'widget',)

    list_display = ['user', 'widget', 'column']

    class Meta:
        model = models.UserWidgetModel
        fields = '__all__'


class WidgetCategoryModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_filter = ['name']
    search_fields = ['name']


class WidgetModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'icon', 'widget_component', 'is_mobile', 'is_desktop', 'static',]
    list_editable = ['is_mobile', 'is_desktop']
    list_filter = ['category', 'static']
    search_fields = ['icon', 'widget_component']
    inlines = (AppSectionRoleThroughInline,)


class DesktopTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'default', 'name', 'draggable', 'resizable', 'margin_x', 'margin_y', 'vertical_compact',
                    'use_css_transforms']
    list_filter = ['draggable', 'resizable', 'vertical_compact', 'use_css_transforms']
    inlines = (AccessGroupDesktopTemplateThroughInline,)


class UserDesktopModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'author', 'created_at', 'is_active', 'desktop_template', 'draggable', 'resizable', 'margin_x', 'margin_y',
                    'vertical_compact', 'use_css_transforms']
    list_filter = ['draggable', 'resizable', 'vertical_compact', 'use_css_transforms']
    search_fields = ['id', 'name', 'author__username', 'author__first_name', 'author__last_name']
    readonly_fields = ('author', 'created_at', 'updated_at',)


class UserWidgetOnDesktopModelAdmin(admin.ModelAdmin):
    list_display = [
        'widget',
        'desktop',
        'desktop_author',
        'created_at',
        'x',
        'y',
        'w',
        'h',
        'i',
        'mobile_index',
        'is_mobile',
        'is_desktop',
        'is_active'
    ]
    list_filter = ['is_active',]
    search_fields = ['desktop__id', 'name', 'widget__name']
    autocomplete_fields = ['desktop']
    readonly_fields = ('created_at', 'updated_at', 'author')

    def desktop_author(self, obj):
        if obj.desktop and obj.desktop.author:
            return str(obj.desktop.author)
        return '-'
    desktop_author.short_description = 'Desktop Author'


class DesktopTemplateWidgetOnDesktopModelAdmin(admin.ModelAdmin):
    list_display = ['widget', 'desktop', 'x', 'y', 'w', 'h', 'i', 'mobile_index', 'is_mobile', 'is_desktop',]
    list_filter = ['widget', 'desktop']
    search_fields = ['widget__name']


admin.site.register(models.DesktopTemplateWidgetOnDesktopModel, DesktopTemplateWidgetOnDesktopModelAdmin)

admin.site.register(models.WidgetCategoryModel, WidgetCategoryModelAdmin)
admin.site.register(models.WidgetModel, WidgetModelAdmin)
admin.site.register(models.DesktopTemplateModel, DesktopTemplateAdmin)
admin.site.register(models.UserDesktopModel, UserDesktopModelAdmin)
admin.site.register(models.UserWidgetOnDesktopModel, UserWidgetOnDesktopModelAdmin)
