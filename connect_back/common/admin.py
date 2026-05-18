from django.contrib import admin
from django.db.models import JSONField
from django.contrib.contenttypes.models import ContentType

from prettyjson.widgets import PrettyJSONWidget

from . import models


class ViewerInline(admin.TabularInline):
    model = models.ObjectViewerRelationModel
    fields = (
        'profile',
    )
    autocomplete_fields = ('profile',)
    extra = 0
    fk_name = 'obj'


class FileBaseModelInline(admin.TabularInline):
    fields = ('file', 'folder', 'is_active')
    model = models.FileBaseModel
    extra = 0
    autocomplete_fields = ('file',)


class MentionInline(admin.TabularInline):
    model = models.MentionModel
    fields = ('user',)
    extra = 0
    fk_name = 'related_object'
    autocomplete_fields = ('user',)


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ('app_label', 'model',)


@admin.register(models.BaseModel)
class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)
    search_fields = ('id',)
    list_display = (
        'id',
        'is_active',
        'ct',
        'created_at',
        'updated_at',
        'deleted_at',
    )


@admin.register(models.FileBaseModel)
class FileBaseModelAdmin(admin.ModelAdmin):
    list_display = (
        'file',
        'related_object',
    )
    autocomplete_fields = ('file', 'related_object',)


@admin.register(models.FolderModel)
class FolderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name'
    )
    autocomplete_fields = (
        'related_object',
    )


@admin.register(models.BaseCatalog)
class BaseCatalogAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)
    search_fields = ('name',)


@admin.register(models.File)
class FileAdmin(admin.ModelAdmin):
    autocomplete_fields = ('author',)
    list_display = (
        'id',
        'name',
        'extension',
        'created_at',
        'mime_type',
        'upload',
        'author',
        'is_orphaned',
        'is_image',
        'is_confined',)
    readonly_fields = ('author', 'size', 'extension', 'created_at',)
    search_fields = ('name', 'id',)
    list_filter = (
        'extension',
        'mime_type',
        'is_orphaned',
        'is_confined',
    )
    ordering = ('-created_at',)


class MimeTypeModelInline(admin.TabularInline):
    model = models.MimeType
    fk_name = 'file_type'
    extra = 0


@admin.register(models.FileType)
class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sort')
    inlines = (MimeTypeModelInline,)


@admin.register(models.MimeType)
class MimeTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'file_type', 'sort')


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    readonly_fields = ('author',)
    search_fields = ['name']


@admin.register(models.BaseDocument)
class BaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'author')
    readonly_fields = ('author',)


@admin.register(models.Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    readonly_fields = ('author',)


@admin.register(models.FiltersStore)
class FilterStoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at', 'page_name', 'author')
    list_filter = ('model',)
    search_fields = (
        'author__id',
        'author__user__last_name',
        'author__user__first_name',
        'author__user__middle_name',
        'author__user__email',
    )
    readonly_fields = ('author',)
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


@admin.register(models.RecentlySelectedUsersModel)
class RecentlySelectedUsersModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'updated_at')
    search_fields = (
        'author__user__last_name',
        'author__user__first_name',
        'author__user__email',
    )
    readonly_fields = ('author',)
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


@admin.register(models.AssetInWarehouse)
class AssetInWarehouseAdmin(admin.ModelAdmin):
    list_display = ('asset',
                    'asset_owner',
                    'warehouse',
                    'quantity',
                    'amount',
                    'type_of_accumulation'
                    )


@admin.register(models.PlanOfCharacteristic)
class PlanOfCharacteristicAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)
    list_display = (
        "name",
        "entity_type",
        "field_code",
        "subfield_code",
        "repetitive",
        "required",
    )
    list_filter = (
        'block',
        'entity_type',
        'field_type',
        'appointment',
    )
    autocomplete_fields = ('block',)


@admin.register(models.PlanOfCharacteristicValue)
class PlanOfCharacteristicValueAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner_object',
        'field_type',
        'field_value_to_repr',
        'field_index',
        'subfield_index',
    )

    readonly_fields = ('author',)


@admin.register(models.TechnicalIsolatedCallsControlModel)
class TechnicalIsolatedCallsControlAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_started'
    )


@admin.register(models.CKEditorFileModel)
class CKEditorFileModelAdmin(admin.ModelAdmin):
    list_display = (
        'related_object',
        'file',
        'is_active',
    )

    readonly_fields = ('author',)
    autocomplete_fields = ('related_object', 'file',)


@admin.register(models.PlanOfCharacteristicBlock)
class PlanOfCharacteristicBlockAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
    )
    readonly_fields = ('author',)
    search_fields = ('code', 'name',)


@admin.register(models.PlanOfCharacteristicLookup)
class PlanOfCharacteristicLookupAdmin(admin.ModelAdmin):
    list_display = (
        'target_model',
        'key',
        'value',
    )

    list_filter = ('target_model',)
    search_fields = ('target_model', 'key')


@admin.register(models.InterfaceModel)
class InterfaceModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'role',
        'role_id'
    )
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


@admin.register(models.CustomThemeModel)
class CustomThemeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )


@admin.register(models.CustomJSModel)
class CustomJSModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )



@admin.register(models.DesktopApplicationVersionModel)
class DesktopApplicationVersionModelAdmin(admin.ModelAdmin):
    list_display = (
      'id', 'version', 'created_at', 'target_url', 'release_file'
    )
    readonly_fields = ('author', 'created_at', 'updated_at')
    ordering = ('-created_at',)




@admin.register(models.TableSettingsModel)
class TableSettingsModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'profile',
        'field1',
        'field2',
        'field3',
    )
    autocomplete_fields = ('profile',)
    ordering = ('profile__user__last_name', 'profile__user__first_name')
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'field1', 'field1', 'field3')


@admin.register(models.MentionModel)
class MentionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'related_object',
        'author',
        'created_at',
    )
    autocomplete_fields = ('user', 'related_object',)
    search_fields = (
        'author__user__first_name',
        'author__user__last_name',
        'user__user__last_name',
        'user__user__first_name'
    )
    ordering = ('-created_at',)


from collections import defaultdict

from django import forms
from django.apps import apps
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q, CharField, TextField
from django.http import JsonResponse, HttpResponseBadRequest,HttpResponseForbidden
from django.shortcuts import render
from django.urls import path

# ------------------- Форма -------------------

class ReplaceRefsForm(forms.Form):
    source_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label="Тип источника",
        required=True,
    )
    source_object_id = forms.CharField(
        label="ID источника (UUID)",
        required=True,
        widget=forms.HiddenInput,
    )

    target_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label="Тип приёмника",
        required=True,
    )
    target_object_id = forms.CharField(
        label="ID приёмника (UUID)",
        required=True,
        widget=forms.HiddenInput,
    )

# ------------------- Логика поиска ссылок -------------------

def find_references(source_model, source_pk):
    hits = []

    for model in apps.get_models():
        meta = model._meta
        app_label = meta.app_label
        model_name = meta.model_name

        for field in meta.get_fields():
            # ForeignKey, прямое поле, не обратная связь
            if not (field.is_relation and field.many_to_one and not field.auto_created):
                continue

            if field.related_model is not source_model:
                continue

            qs = model.objects.filter(**{field.name: source_pk})
            for obj in qs:
                hit_id = f"{app_label}.{model_name}:{field.name}:{obj.pk}"
                hits.append(
                    {
                        "id": hit_id,
                        "app_label": app_label,
                        "model_name": model_name,
                        "field_name": field.name,
                        "field_verbose": getattr(field, "verbose_name", field.name),
                        "pk": str(obj.pk),
                        "repr": str(obj),
                    }
                )

    return hits


def apply_replacements(selected_hit_ids, target_pk):
    grouped = defaultdict(list)

    for hit_id in selected_hit_ids:
        try:
            model_part, field_name, pk_str = hit_id.split(":")
            app_label, model_name = model_part.split(".")
        except ValueError:
            continue
        grouped[(app_label, model_name, field_name)].append(pk_str)

    total = 0

    for (app_label, model_name, field_name), pk_list in grouped.items():
        model = apps.get_model(app_label, model_name)
        if model is None:
            continue
        updated = 0

        for pk_str in pk_list:
            try:
                obj = model.objects.get(pk=pk_str)
                setattr(obj, field_name, target_pk)
                obj.save()
                updated += 1
            except:
                pass
        total += updated

    return total

# ------------------- Admin view -------------------
def replace_refs_view(request):


    if not request.user.is_superuser:
        return HttpResponseForbidden('Only superusers are allowed')

    hits = []
    action = request.POST.get("action")
    form = ReplaceRefsForm(request.POST or None)

    # подписи для выбранных объектов (будут видны в селектах)
    source_object_label = ""
    target_object_label = ""

    if request.method == "POST" and form.is_valid():
        source_ct = form.cleaned_data["source_content_type"]
        source_object_id = form.cleaned_data["source_object_id"]
        target_ct = form.cleaned_data["target_content_type"]
        target_object_id = form.cleaned_data["target_object_id"]

        source_model = source_ct.model_class()
        target_model = target_ct.model_class()

        # пробуем вытащить объекты и сохранить человекочитаемые имена
        if source_model is not None and source_object_id:
            try:
                source_obj = source_model.objects.get(pk=source_object_id)
                source_object_label = str(source_obj)
            except source_model.DoesNotExist:
                pass

        if target_model is not None and target_object_id:
            try:
                target_obj = target_model.objects.get(pk=target_object_id)
                target_object_label = str(target_obj)
            except target_model.DoesNotExist:
                pass

        if source_model is None or target_model is None:
            messages.error(request, "Не удалось получить модель по content_type.")
        else:
            source_pk = source_object_id
            target_pk = target_object_id

            if action == "fill":
                hits = find_references(source_model, source_pk)
                if not hits:
                    messages.info(
                        request,
                        "Ссылок на указанный источник не найдено.",
                    )

            elif action == "replace":
                selected_ids = request.POST.getlist("selected")
                if not selected_ids:
                    messages.warning(
                        request,
                        "Не выбрано ни одной строки для замены.",
                    )
                else:
                    count = apply_replacements(selected_ids, target_pk)
                    messages.success(
                        request,
                        f"Заменено ссылок: {count}.",
                    )
                    hits = find_references(source_model, source_pk)

    context = {
        "title": "Массовая замена ссылок",
        "form": form,
        "hits": hits,
        "source_object_label": source_object_label,
        "target_object_label": target_object_label,
    }
    return render(request, "admin/replace_refs.html", context)


# ------------------- Автокомплит источник/приёмник -------------------

def load_objects_view(request):
    """
    AJAX: вернуть список объектов для выбранного content_type
    в формате, удобном для select2 (id/text).
    Параметры:
        ct_id  - id ContentType
        q      - строка поиска (опционально)
    """

    if not request.user.is_superuser:
        return HttpResponseForbidden('Only superusers are allowed')

    ct_id = request.GET.get("ct_id")
    if not ct_id:
        return HttpResponseBadRequest("ct_id is required")

    try:
        ct = ContentType.objects.get(pk=ct_id)
    except ContentType.DoesNotExist:
        return HttpResponseBadRequest("Invalid content type")

    model = ct.model_class()
    if model is None:
        return JsonResponse({"results": []})

    term = (request.GET.get("q") or "").strip()
    qs = model.objects.all()

    if term:
        q_obj = Q()

        # --- поиск по PK ---
        pk_field = model._meta.pk

        # текстовый / UUID PK → можно icontains
        if isinstance(pk_field, (models.UUIDField, models.CharField, models.TextField)):
            q_obj |= Q(pk__icontains=term)
        else:
            # пробуем привести к типу PK (int, FK и т.п.)
            try:
                cast_val = pk_field.to_python(term)
            except (ValueError, TypeError, ValidationError):
                cast_val = None
            if cast_val is not None:
                q_obj |= Q(pk=cast_val)

        # --- поиск по "разумным" текстовым полям ---
        preferred_names = ["name", "title", "code"]
        used_fields = set()

        for fname in preferred_names:
            try:
                f = model._meta.get_field(fname)
            except FieldDoesNotExist:
                continue
            if isinstance(f, (CharField, TextField)):
                q_obj |= Q(**{f"{fname}__icontains": term})
                used_fields.add(fname)

        # остальные Char/Text поля
        for f in model._meta.get_fields():
            if f.name in used_fields:
                continue
            if not isinstance(f, (CharField, TextField)):
                continue
            if getattr(f, "many_to_many", False) or getattr(f, "one_to_many", False):
                continue
            q_obj |= Q(**{f"{f.name}__icontains": term})

        if q_obj:
            qs = qs.filter(q_obj)

    qs = qs.order_by("pk")[:50]

    data = [
        {
            "id": str(obj.pk),
            "text": f"{obj} - {obj.pk}",
        }
        for obj in qs
    ]

    return JsonResponse({"results": data})

# ------------------- Подключение к admin.site -------------------

def get_admin_urls(urls):
    def wrapper():
        custom_urls = [
            path(
                "replace-refs/",
                admin.site.admin_view(replace_refs_view),
                name="replace_refs",
            ),
            path(
                "replace-refs/load-objects/",
                admin.site.admin_view(load_objects_view),
                name="replace_refs_load_objects",
            ),
        ]
        return custom_urls + urls()

    return wrapper









admin.site.get_urls = get_admin_urls(admin.site.get_urls)
