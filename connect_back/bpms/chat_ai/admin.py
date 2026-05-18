from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from django.contrib.admin import SimpleListFilter
import json

from .models import (
    IntentTypeModel, IntentStatusModel, AIChatModel, AIMessageModel, IntentModel,
    AIMessageStatusModel, AIChatRoleModel, AIProvider, TokenUsage)


class AIProviderForm(forms.ModelForm):
    api_key = forms.CharField(
        label="API-ключ",
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text="Оставьте пустым, если не хотите менять ключ"
    )

    class Meta:
        model = AIProvider
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        stored_instance = instance  # Сохраняем оригинальный instance
        
        # Для существующего объекта создаём форму без instance,
        # затем вручную заполняем начальные значения
        if instance and instance.pk:
            # Убираем instance чтобы избежать model_to_dict
            kwargs.pop('instance', None)
            super().__init__(*args, **kwargs)
            
            # Вручную заполняем initial для всех полей кроме api_key
            for field_name in self.fields.keys():
                if field_name != 'api_key':
                    try:
                        value = getattr(stored_instance, field_name)
                        self.initial[field_name] = value
                        # Также устанавливаем в data для корректного отображения
                        if field_name in self.fields:
                            self.fields[field_name].initial = value
                    except Exception:
                        pass
            
            # Для api_key всегда показываем placeholder для существующих объектов
            # Это позволяет видеть, что ключ может быть установлен, но не показывает его значение
            self.initial['api_key'] = '********'
            self.fields['api_key'].widget.attrs['placeholder'] = '********'
            
            # Восстанавливаем instance для save()
            self.instance = stored_instance
            self.fields['api_key'].required = False
        else:
            super().__init__(*args, **kwargs)
            # api_key необязателен даже для новых объектов
            self.fields['api_key'].required = False
            self.fields['api_key'].help_text = "Оставьте пустым, если ключ не требуется"

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Если api_key заполнен, устанавливаем его в instance
        api_key_value = self.cleaned_data.get("api_key")
        if api_key_value:
            instance.api_key = api_key_value
        
        # Сохраняем если нужно (но admin использует commit=False и потом вызывает save_model)
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    form = AIProviderForm
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    
    def get_queryset(self, request):
        """Откладываем загрузку зашифрованного api_key, чтобы избежать BadSignature при другом SECRET_KEY."""
        queryset = super().get_queryset(request)
        return queryset.defer('api_key')
    
    def get_object(self, request, object_id, from_field=None):
        """Откладываем загрузку api_key при открытии формы редактирования."""
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            obj = queryset.defer('api_key').get(**{field.name: object_id})
            return obj
        except (model.DoesNotExist, ValueError):
            return None
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для правильной обработки api_key."""
        api_key_value = form.cleaned_data.get('api_key')
        
        # Проверяем, является ли значение placeholder-ом (звездочки)
        is_placeholder = api_key_value == '********' or not api_key_value
        
        if api_key_value and not is_placeholder:
            # api_key заполнен реальным значением - обновляем его и сохраняем всё
            obj.api_key = api_key_value
            obj.save()
        elif change:
            # Редактирование без api_key или с placeholder - сохраняем без этого поля (старое значение сохранится)
            # Исключаем ptr-поля (указатели на родительские модели) и другие неконкретные поля
            excluded_fields = {'api_key', 'id'}
            # Исключаем все поля, которые заканчиваются на _ptr (указатели на родительские модели)
            update_fields = [
                f.name for f in obj._meta.fields 
                if f.name not in excluded_fields 
                and not f.name.endswith('_ptr')
                and f.concrete
            ]
            obj.save(update_fields=update_fields)
        else:
            # Новый объект - устанавливаем api_key (пустое значение, если не указано)
            obj.api_key = api_key_value if api_key_value and api_key_value != '********' else ''
            obj.save()


class AIProviderFilter(SimpleListFilter):
    """Кастомный фильтр для provider, который не загружает зашифрованное поле api_key."""
    title = 'Провайдер LLM'
    parameter_name = 'provider'

    def lookups(self, request, model_admin):
        """Возвращает список вариантов для фильтра, используя queryset без api_key."""
        try:
            providers = AIProvider.objects.defer('api_key').filter(is_active=True).order_by('name')
            return [(provider.code, provider.name) for provider in providers]
        except Exception:
            # Если не удается расшифровать данные, возвращаем пустой список
            return []

    def queryset(self, request, queryset):
        """Фильтрует queryset по выбранному provider."""
        if self.value():
            return queryset.filter(provider__code=self.value())
        return queryset


class AIChatRoleModelForm(forms.ModelForm):
    """Форма для AIChatRoleModel, которая не загружает api_key из связанной модели AIProvider."""
    
    class Meta:
        model = AIChatRoleModel
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настраиваем queryset для поля provider, чтобы не загружать api_key
        if 'provider' in self.fields:
            try:
                self.fields['provider'].queryset = AIProvider.objects.defer('api_key').all()
            except Exception:
                # Если не удается загрузить, используем пустой queryset
                self.fields['provider'].queryset = AIProvider.objects.none()


@admin.register(AIChatRoleModel)
class AIChatRoleModelAdmin(admin.ModelAdmin):
    form = AIChatRoleModelForm
    list_display = ('code', 'sort', 'provider', 'model_name', 'temperature', 'top_p', 'max_output_tokens', 'num_ctx',)
    list_filter = (AIProviderFilter, 'model_name', 'is_active',)
    list_editable = ('sort',)
    ordering = ('-sort',)
    
    def get_queryset(self, request):
        """Откладываем загрузку зашифрованного api_key из связанной модели AIProvider."""
        queryset = super().get_queryset(request)
        return queryset.select_related('provider').defer('provider__api_key')
    
    def get_object(self, request, object_id, from_field=None):
        """Откладываем загрузку api_key при открытии формы редактирования."""
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            obj = queryset.get(**{field.name: object_id})
            return obj
        except (model.DoesNotExist, ValueError):
            return None


@admin.register(IntentTypeModel)
class IntentTypeModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sort', 'btn_title_create', 'is_active',)
    list_editable = ('sort',)
    list_filter = ('is_active',)
    ordering = ('-sort',)
    search_fields = ('code', 'name')


@admin.register(AIMessageStatusModel)
class AIMessageStatusModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'sort')
    list_filter = ('is_active',)
    ordering = ('sort',)
    search_fields = ('code', 'name')


@admin.register(IntentStatusModel)
class IntentStatusModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active',)
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(AIChatModel)
class AIChatModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'last_sent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('id', 'name', 'chat_author__user__username', 'chat_author__user__email')
    autocomplete_fields = ('chat_author',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('chat_author__user')


class IntentInline(admin.TabularInline):
    model = IntentModel
    fk_name = 'source_object'
    extra = 0
    readonly_fields = ('intent_type', 'status', 'created_at')
    fields = ('intent_type', 'status', 'created_at')


@admin.register(AIMessageModel)
class AIMessageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_bot', 'is_intent',)
    list_filter = ('is_bot', 'is_intent', 'created_at', 'updated_at')
    search_fields = ('text', 'message_author__user__username', 'chat__name')
    autocomplete_fields = ('chat', 'message_author', 'reply_to', 'status')
    list_select_related = ('chat', 'message_author__user', 'status')
    inlines = [IntentInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('chat', 'message_author__user')


@admin.register(IntentModel)
class IntentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'intent_type', 'status', 'created_at')
    list_filter = ('intent_type', 'status')
    search_fields = ('intent_type__name', 'status__name')
    autocomplete_fields = ('intent_type', 'status', 'source_object', 'related_object')


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'author', 'model_name', 'prompt_tokens', 'completion_tokens', 'created_at')
    search_fields = ('model_name', 'consumer__id', 'author__user__username', 'author__user__email')
    list_filter = ('model_name', 'created_at')
    readonly_fields = ('consumer', 'author', 'model_name', 'prompt_tokens', 'completion_tokens', 'created_at')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author__user')