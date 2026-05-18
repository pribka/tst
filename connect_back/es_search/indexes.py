from django_elasticsearch_dsl import Index
from elasticsearch_dsl import analyzer, token_filter

from bkz3.settings import DEFAULT_DSL_NAMESPACE

# Явные настройки индекса (django-elasticsearch-dsl не всегда корректно собирает analysis из всех Documents)
CONNECT_INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "filter": {
            "ru_stop": {"type": "stop", "stopwords": "_russian_"},
            "ru_stemmer": {"type": "stemmer", "language": "russian"},
            "edge_ngram_filter": {"type": "edge_ngram", "min_gram": 3, "max_gram": 10},
            "reverse_filter": {"type": "reverse"},
            "edge_ngram_suffix": {"type": "edge_ngram", "min_gram": 3, "max_gram": 6},
        },
        "analyzer": {
            "text_ru": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "ru_stop", "ru_stemmer"],
            },
            "text_fio": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase"],
            },
            "text_ru_ngram": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "edge_ngram_filter"],
            },
            "number_suffix": {
                "type": "custom",
                "tokenizer": "keyword",
                "filter": ["reverse_filter", "edge_ngram_suffix"],
            },
            "number_suffix_search": {
                "type": "custom",
                "tokenizer": "keyword",
                "filter": ["reverse_filter"],
            },
        },
    },
}

# Общий индекс для всех моделей проекта
connect = Index(DEFAULT_DSL_NAMESPACE)
connect.settings(**CONNECT_INDEX_SETTINGS)

# Русские стоп-слова и стемминг (для казахского оставим lowercase)
ru_stop    = token_filter("ru_stop", type="stop", stopwords="_russian_")
ru_stemmer = token_filter("ru_stemmer", type="stemmer", language="russian")

# Edge ngram фильтр для частичного поиска
edge_ngram_filter = token_filter(
    "edge_ngram_filter",
    type="edge_ngram",
    min_gram=3,
    max_gram=10
)

# Универсальный анализатор для RU (+KK как lowercase)
text_ru = analyzer(
    "text_ru",
    tokenizer="standard",
    filter=["lowercase", ru_stop, ru_stemmer],
)

# Анализатор ФИО без стемминга: просто токенизация + приведение к нижнему регистру.
text_fio = analyzer(
    "text_fio",
    tokenizer="standard",
    filter=["lowercase"],
)

# Анализатор с edge_ngram для частичного поиска
text_ru_ngram = analyzer(
    "text_ru_ngram",
    tokenizer="standard",
    filter=["lowercase", edge_ngram_filter],
)

# Суффиксный поиск по номеру заявки: reverse + edge_ngram (поиск от 3 символов)
reverse_filter = token_filter("reverse_filter", type="reverse")
edge_ngram_suffix = token_filter(
    "edge_ngram_suffix",
    type="edge_ngram",
    min_gram=3,
    max_gram=6,
)
number_suffix = analyzer(
    "number_suffix",
    tokenizer="keyword",
    filter=[reverse_filter, edge_ngram_suffix],
)
number_suffix_search = analyzer(
    "number_suffix_search",
    tokenizer="keyword",
    filter=[reverse_filter],
)
