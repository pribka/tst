DEFAULT = {
    "mappings": {
        "properties": {
            "chat_id": {
                "type": "keyword"
            },
            "chat_is_active": {
                "type": "boolean"
            },
            "chat_is_public": {
                "type": "boolean"
            },
            "chat_members": {
                "type": "keyword"
            },
            "counter": {
                "type": "long"
            },
            "created_at": {
                "type": "date"
            },
            "dead_line": {
                "type": "date"
            },
            "django_ct": {
                "type": "keyword"
            },
            "django_id": {
                "type": "keyword"
            },
            "full_name_auto": {
                "type": "text",
                "analyzer": "edgengram_analyzer"
            },
            "id": {
                "type": "keyword"
            },
            "is_active": {
                "type": "boolean"
            },
            "name": {
                "type": "text",
                "analyzer": "custom_russian"
            },
            "operator": {
                "type": "text",
                "analyzer": "custom_russian"
            },
            "owner": {
                "type": "text",
                "analyzer": "custom_russian"
            },
            "popularity": {
                "type": "float"
            },
            "price_by_catalog": {
                "type": "long"
            },
            "profile_id": {
                "type": "keyword"
            },
            "status": {
                "type": "integer"
            },
            "text": {
                "type": "text",
                "analyzer": "edgengram_analyzer",
                "fields": {
                    "exact": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "text_exact": {
                        "type": "keyword"
                    }
                }
            }
        }
    },
    "settings": {
        "index": {
            "max_ngram_diff": "2",
            "routing": {
                "allocation": {
                    "include": {
                        "_tier_preference": "data_content"
                    }
                }
            },
            "analysis": {
                "filter": {
                    "haystack_ngram": {
                        "type": "ngram",
                        "min_gram": "3",
                        "max_gram": "4"
                    },
                    "haystack_edgengram": {
                        "type": "edge_ngram",
                        "min_gram": "3",
                        "max_gram": "10"
                    },

                    "ru_stop": {
                        "type": "stop",
                        "stopwords": "_russian_"
                    },
                    "ru_stemmer": {
                        "type": "stemmer",
                        "language": "russian"
                    }
                },
                "analyzer": {
                    "custom_russian": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "ru_stop",
                            "ru_stemmer"
                        ]
                    },
                    "edgengram_analyzer": {
                        "filter": [
                            "haystack_edgengram",
                            "lowercase"
                        ],
                        "tokenizer": "standard"
                    },
                    "ngram_analyzer": {
                        "filter": [
                            "haystack_ngram",
                            "lowercase"
                        ],
                        "tokenizer": "standard"
                    }
                }
            }
        }
    }
}
