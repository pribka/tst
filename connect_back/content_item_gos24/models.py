from django.db import models
from django.utils import timezone
import datetime

# предполагаю, что эти импорты у вас уже есть
from django.contrib.auth import get_user_model

User = get_user_model()

from common import models as common_models
from common import fields as common_fields
from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE
from users.models import CustomUser
from users.models import ProfileModel


class OfficialClarificationOrgan(common_models.BaseModel):
    title = models.CharField(
        max_length=400,
        verbose_name='Названия органа',
    )
    sent_gos = models.BooleanField(
        default=False,
        verbose_name='Отправлен в GOS24',
    )
    id_gos24 = models.IntegerField(
        default=0,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Официальные органы'
        verbose_name_plural = 'Официальные органы'


class Partition(common_models.BaseCatalog):
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    sent_gos = models.BooleanField(
        default=False,
        verbose_name='Отправлен в GOS24',
    )
    id_gos24 = models.IntegerField(
        default=0,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Раздел'


class Tag(common_models.BaseCatalog):
    main = models.BooleanField(
        default=False,
        verbose_name='Главный тег',
    )
    sent_gos = models.BooleanField(
        default=False,
        verbose_name='Отправлен в GOS24',
    )
    id_gos24 = models.IntegerField(
        default=0,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class ContentItem(common_models.BaseModel):
    # --- Константы типов ---
    KIND_ARTICLE = "article"
    KIND_OFFICIAL = "official"
    KIND_QA = "qa"
    KIND_KNOWLEDGEBASE = "knowledgebase"
    KIND_WEBINAR = "webinar"
    KIND_MASTER_CLASS = "master_class"
    KIND_COURSE = "course"
    KIND_NEWS_PUBLICATIONS_GOS24 = "news_publications_gos24"
    KIND_NEWS_FINANCE = "news_finance"
    KIND_CALENDAR = "calendar"
    KIND_CALENDAR_FINANCE = "calendar_finance"

    # Публичные choices (включая мастер-класс и курс)
    KIND_CHOICES = (
        (KIND_ARTICLE, "Статья"),
        (KIND_OFFICIAL, "Офиц. разъяснение"),
        (KIND_QA, "Вопрос-Ответ"),
        (KIND_WEBINAR, "Вебинар"),
        (KIND_MASTER_CLASS, "Мастер‑класс"),
        (KIND_COURSE, "Курс"),
        (KIND_KNOWLEDGEBASE, "База знаний"),
        (KIND_NEWS_PUBLICATIONS_GOS24, "Новости и публикации Гос24"),
        (KIND_CALENDAR, "Календарь"),
        (KIND_NEWS_FINANCE, "Публикации GOS24.Finance"),
        (KIND_CALENDAR_FINANCE, "Календарь GOS24.Finance"),
    )
    common_date = models.DateField(
        null=True, blank=True, verbose_name="Дата"
    )

    kind = models.CharField(max_length=32, choices=KIND_CHOICES, db_index=True, verbose_name="Тип контента")

    title = models.TextField(blank=True, default="", verbose_name="Заголовок")
    slug = models.CharField(blank=True, max_length=300, db_index=True, verbose_name="Слаг")
    partition = common_fields.CustomForeignKey(
        Partition,
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        verbose_name='Раздел',
    )
    category = common_fields.CustomForeignKey(
        Partition,
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        verbose_name='Категория',
        related_name='categorycontentitem',
    )
    draft = models.BooleanField(
        default=False,
        verbose_name="Черновик (для статей)"
    )
    publish = models.BooleanField(
        default=False,
        verbose_name="Публиковать (для official/qa/webinar)"
    )
    publication_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата публикации"
    )
    only_subscribed = models.BooleanField(
        default=False,
        verbose_name="Доступ только по подписке"
    )
    organ = models.ForeignKey(
        OfficialClarificationOrgan,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="content_items_as_organ",
        verbose_name="Наименование органа (для official)"
    )
    lecturer = common_fields.CustomForeignKey(
        ProfileModel,
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        verbose_name='Лектор',
    )
    lecturer_full_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    content_type = models.CharField(
        max_length=200,
        verbose_name='Тип контента',
        null=True,
        blank=True,
    )

    main_in_week = models.BooleanField(
        default=False,
        verbose_name="Главное за неделю"
    )
    anchor_links = models.BooleanField(
        default=False,
        verbose_name="Показать якорные ссылки"
    )
    image = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Обложка/Картинка"
    )
    summary = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="Резюме/краткое описание"
    )
    body = models.TextField(
        blank=True,
        default="",
        verbose_name="Тело (plain)"
    )
    body_clean = models.TextField(
        blank=True,
        default="",
        verbose_name="Тело (без HTML)"
    )
    body_amp = models.TextField(
        blank=True,
        default="",
        verbose_name="Тело AMP"
    )
    body_html = models.TextField(
        blank=True,
        default="",
        verbose_name="Тело/Содержание (HTML)"
    )
    body_html_amp = models.TextField(
        blank=True,
        default="",
        verbose_name="Тело/Содержание AMP (HTML->AMP)"
    )

    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание",
    )
    description_clean = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание (без HTML)"
    )
    description_amp = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание AMP"
    )
    tutorial_id = models.CharField(
        blank=True,
        null=True,
        max_length=200
    )
    section_id = models.CharField(
        blank=True,
        null=True,
        max_length=200
    )
    # --- QA ---
    question = models.TextField(
        blank=True,
        default="",
        verbose_name="Вопрос (plain)"
    )
    question_html = models.TextField(
        blank=True,
        default="",
        verbose_name="Вопрос (HTML)"
    )
    answer = models.TextField(
        blank=True,
        default="",
        verbose_name="Ответ (plain)"
    )
    answer_html = models.TextField(
        blank=True,
        default="",
        verbose_name="Ответ (HTML)"
    )
    small_title = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание для главной страницы (QA)"
    )

    # --- Education ---
    content_edu_type = models.IntegerField(
        default=0,
        blank=True,
        verbose_name="Тип образовательного контента (0-вебинар,1-МК,2-курс)"
    )
    webinar_date = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Дата вебинара (как есть)"
    )
    planned_date = models.DateField(
        default=datetime.date(1, 1, 1),
        verbose_name="Планируемая дата проведения"
    )
    start_live_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время начала"
    )
    end_live_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время окончания"
    )
    youtube_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        default="",
        verbose_name="YouTube URL"
    )
    broadcast = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        default="",
        verbose_name="Ссылка для трансляции"
    )
    next = models.BooleanField(
        default=False,
        verbose_name="Ближайший (education)"
    )
    spend = models.BooleanField(
        default=False,
        verbose_name="Проведен (education)"
    )
    free = models.BooleanField(
        default=False,
        verbose_name="Бесплатный (education)"
    )
    sent_gos = models.BooleanField(
        default=False,
        verbose_name='Отправлен в GOS24',
    )
    webinar_active = models.BooleanField(
        default=False,
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name='Тэги',
    )
    id_gos24 = models.IntegerField(
        default=0,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.lecturer_full_name:
            if self.lecturer and self.lecturer.user:
                self.lecturer_full_name = self.lecturer.user.full_name
            else:
                self.lecturer_full_name = None
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = "Контент"
        indexes = [
            models.Index(fields=["kind", "publish", "draft"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["publication_date"]),
        ]


import importlib
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import models

from common import models as common_models  # замени на свой базовый класс при необходимости

# где лежат функции import_connect_*
# если оставил их во views.py, укажи "your_app.views"
IMPORT_FUNCS_MODULE = "content_item_gos24.import_gos24.views2"


class SettingsGos(common_models.BaseModel):
    # --- типы операций ---
    TYPE_TAGS            = "tags"
    TYPE_PARTITIONS      = "partitions"
    TYPE_NEWS            = "news"
    TYPE_ARTICLES        = "articles"
    TYPE_OFFICIAL_ORGANS = "official_organs"
    TYPE_OFFICIAL        = "official"
    TYPE_QA              = "qa"
    TYPE_WEBINARS        = "webinars"
    TYPE_KNOWLEDGEBASE   = "knowledgebase"
    TYPE_DELETE_ALL      = "delete_all"

    TYPE_CHOICES = [
        (TYPE_TAGS, "Импорт тегов"),
        (TYPE_PARTITIONS, "Импорт разделов"),
        (TYPE_NEWS, "Импорт новостей"),
        (TYPE_ARTICLES, "Импорт статей"),
        (TYPE_OFFICIAL_ORGANS, "Импорт органов"),
        (TYPE_OFFICIAL, "Импорт оф. разъяснений"),
        (TYPE_QA, "Импорт Вопрос-Ответ"),
        (TYPE_WEBINARS, "Импорт вебинаров"),
        (TYPE_KNOWLEDGEBASE, "Импорт базы знаний"),
        (TYPE_DELETE_ALL, "Удалить весь контент"),
    ]

    op_type = models.CharField("Тип операции", max_length=32, choices=TYPE_CHOICES, blank=True, null=True)
    payload = models.JSONField(
        "Данные (список объектов)",
        default=list,  # теперь список, без ключа "items"
        blank=True,
        help_text="Передавай сюда сразу list[dict] для импорта. Для delete_all можно оставить пусто.",
    )
    atomic  = models.BooleanField(
        "Per-item atomic",
        default=True,
        help_text="Каждый элемент импортируется в своей atomic-транзакции",
    )
    url_send_gos = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    send_gos = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = "Настройка импорта/операций"
        verbose_name_plural = "Настройки импорта/операций"

    # Ручной запуск из кода
    def run_now(self):
        typ = self.op_type

        if typ == self.TYPE_DELETE_ALL:
            return self._delete_all_content()

        func = self._resolve_import_func(typ)
        if func is None:
            raise ValidationError(f"Не найдена функция для type='{typ}'")

        items = self.payload or []
        if not isinstance(items, list):
            raise ValidationError("payload должен быть списком объектов (list[dict])")

        return func(items, atomic=self.atomic)

    # Автовыполнение после сохранения
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            if self.op_type:
                self.run_now()

    # Резолв импорт-функции по типу
    def _resolve_import_func(self, typ):
        name_map = {
            self.TYPE_TAGS:            "import_connect_tags",
            self.TYPE_PARTITIONS:      "import_connect_partitions",
            self.TYPE_NEWS:            "import_connect_news",
            self.TYPE_ARTICLES:        "import_connect_articles",
            self.TYPE_OFFICIAL_ORGANS: "import_connect_official_organs",
            self.TYPE_OFFICIAL:        "import_connect_official_clarifications",
            self.TYPE_QA:              "import_connect_questions",
            self.TYPE_WEBINARS:        "import_connect_webinars",
            self.TYPE_KNOWLEDGEBASE:   "import_connect_knowledgebase",
        }
        func_name = name_map.get(typ)
        if not func_name:
            return None
        module = importlib.import_module(IMPORT_FUNCS_MODULE)
        return getattr(module, func_name, None)

    # Спец-операция: удалить всё
    def _delete_all_content(self):
        qs = ContentItem.objects.all()
        for item in qs:
            item.delete()

