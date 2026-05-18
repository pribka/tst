from django.contrib import admin
from django import forms
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
import os
import shutil

from . import models


class ReportSettingsModelAdminForm(forms.ModelForm):
    """Форма с загрузкой файла шаблона в report_templates."""
    template_file = forms.FileField(
        label='Шаблон Excel',
        required=False,
        help_text='Загрузите .xlsx — файл сохранится в общую папку report_templates и не будет зависеть от ваших файлов.',
    )
    clear_template = forms.BooleanField(
        label='Очистить шаблон',
        required=False,
        help_text='Отметьте и сохраните — путь к шаблону будет очищен, отчёт будет без своего Excel-шаблона.',
    )

    class Meta:
        model = models.ReportSettingsModel
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.template_path:
            self.fields['template_file'].help_text = (
                f'Текущий шаблон: {self.instance.template_path}. Загрузите новый файл, чтобы заменить.'
            )
        else:
            self.fields['clear_template'].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        want_clear = self.cleaned_data.get('clear_template') or self.data.get('clear_template') in ('on', 'true', '1', True)
        if want_clear and instance.pk:
            if instance.template_path:
                full_path = os.path.join(settings.MEDIA_ROOT, instance.template_path)
                if os.path.isfile(full_path):
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass
            instance.template_path = None
            if commit:
                instance.save(update_fields=['template_path'])
        return instance


@admin.register(models.ReportCategoryModel)
class ReportCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sort', 'is_active',)
    search_fields = ('code', 'name',)
    ordering = ('sort',)


@admin.register(models.ReportSettingsModel)
class ReportSettingsModelAdmin(admin.ModelAdmin):
    form = ReportSettingsModelAdminForm
    readonly_fields = ('template_path', 'download_template_link',)

    list_filter = (
        'app_section_code',
        'category',
        'usage_scope',
        'is_active',
    )

    list_display = (
        'code',
        'name',
        'category',
        'app_section_code',
        'usage_scope',
    )
    # list_editable = ('app_section_code', 'category',)

    search_fields = ('id', 'name',)
    ordering = ('usage_scope', 'category', 'app_section_code', 'name',)
    autocomplete_fields = ('category',)

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                '<uuid:object_id>/download_template/',
                self.admin_site.admin_view(self.download_template_view),
                name='reports_reportsettingsmodel_download_template',
            ),
        ]
        return extra + urls

    def download_template_view(self, request, object_id):
        from django.shortcuts import get_object_or_404
        obj = get_object_or_404(models.ReportSettingsModel, pk=object_id)
        if not self.has_change_permission(request, obj):
            raise Http404
        if not obj.template_path:
            raise Http404
        full_path = os.path.join(settings.MEDIA_ROOT, obj.template_path)
        if not os.path.isfile(full_path):
            raise Http404
        filename = os.path.basename(obj.template_path)
        with open(full_path, 'rb') as fh:
            response = HttpResponse(
                fh.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @admin.display(description='Скачать шаблон')
    def download_template_link(self, obj):
        if not obj or not obj.pk or not obj.template_path:
            return '—'
        url = reverse(
            'admin:reports_reportsettingsmodel_download_template',
            args=[obj.pk],
        )
        return format_html('<a href="{}">Скачать файл шаблона</a>', url)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.cleaned_data.get('clear_template'):
            return
        uploaded = form.files.get('template_file')
        if not uploaded:
            return
        report_templates_root = getattr(settings, 'REPORT_TEMPLATES_ROOT', None)
        if not report_templates_root:
            return
        os.makedirs(report_templates_root, exist_ok=True)
        ext = os.path.splitext(getattr(uploaded, 'name', '') or '')[1] or 'xlsx'
        if ext.lower() != '.xlsx':
            ext = 'xlsx'
        else:
            ext = ext.lstrip('.')
        rel_path = f"report_templates/template_{obj.pk}.{ext}"
        dest_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        with open(dest_path, 'wb') as dest:
            shutil.copyfileobj(uploaded, dest)
        obj.template_path = rel_path
        obj.save(update_fields=['template_path'])


@admin.register(models.UserReportSettingsModel)
class UserReportSettingsModelAdmin(admin.ModelAdmin):
    list_filter = (
        'app_section_code',
        'base_report__category',
        'is_active',
    )

    list_display = (
        'id',
        'name',
        'author',
        'base_report_id',
        'base_report_category',
    )

    search_fields = (
        'id',
        'name',
        'author__id',
        'author__user__last_name',
        'author__user__first_name',
        'author__user__email',
    )
    ordering = ('-created_at',)
    autocomplete_fields = ('author', 'base_report',)

    @admin.display(description='Категория', ordering='base_report__category__name')
    def base_report_category(self, obj):
        if not obj.base_report_id:
            return None
        return obj.base_report.category