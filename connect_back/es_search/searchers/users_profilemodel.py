from elasticsearch_dsl import Q
from ..documents import ProfileDocument


def search_users_profilemodel(search: str):
    """Поиск по профилям в ES. Возвращает список словарей {'id','score'} без учета видимости."""
    query_string = (search or "").strip()

    s = ProfileDocument.search()

    if query_string:
        # Поиск только по ФИО (отдельные поля) по анализируемым полям без стемминга
        # с приоритетом: last_name > first_name > middle_name.
        # Основной поиск - точный match по токенам, дополнительный - ngram и fuzzy.
        field_boosts = {
            "last_name": {
                "exact": 8,
                "ngram": 6,
                "fuzzy": 4,
            },
            "first_name": {
                "exact": 7,
                "ngram": 5,
                "fuzzy": 3,
            },
            "middle_name": {
                "exact": 6,
                "ngram": 4,
                "fuzzy": 2,
            },
        }

        should_clauses = []
        for field_name, boosts in field_boosts.items():
            exact_boost = boosts["exact"]
            ngram_boost = boosts["ngram"]
            fuzzy_boost = boosts["fuzzy"]

            should_clauses.extend(
                [
                    # Точный матч по токенам без стемминга
                    Q(
                        "match",
                        **{
                            field_name: {
                                "query": query_string,
                                "operator": "and",
                                "boost": exact_boost,
                            }
                        },
                    ),
                    # Частичный поиск через edge_ngram-подполе
                    Q(
                        "match",
                        **{
                            f"{field_name}.ngram": {
                                "query": query_string,
                                "boost": ngram_boost,
                            }
                        },
                    ),
                    # Нечеткий поиск для учета опечаток
                    Q(
                        "match",
                        **{
                            field_name: {
                                "query": query_string,
                                "fuzziness": 1,
                                "prefix_length": 1,
                                "max_expansions": 50,
                                "operator": "and",
                                "boost": fuzzy_boost,
                            }
                        },
                    ),
                ]
            )

        s = s.query(
            Q(
                "bool",
                should=should_clauses,
                minimum_should_match=1,
            )
        )

    # Увеличиваем окно результатов до 300 документов
    s = s[0:300]
    # Источники не используются, отключаем для экономии
    s = s.source(False)
    resp = s.execute()

    results = []
    
    if resp.hits:
        max_score = resp.hits[0].meta.score if resp.hits else 0
        score_threshold = max_score * 0.2 if max_score >= 2 else 0
        
        for hit in resp.hits:
            if hit.meta.score >= score_threshold:
            # if True:
                results.append({
                    'id': hit.meta.id,
                    'score': hit.meta.score,
                })
    
    return results
