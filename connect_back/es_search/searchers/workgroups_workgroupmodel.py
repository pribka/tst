from elasticsearch_dsl import Q
from ..documents import WorkgroupDocument


def search_workgroups_workgroupmodel(search: str):
    """Поиск по рабочим группам в ES. Возвращает [{'id','score'}] без учета видимости."""
    q = (search or "").strip()

    # Собираем ES-запрос без ограничений по видимости
    s = WorkgroupDocument.search()

    if q:
        # Комбинированный поиск: точное совпадение + частичное совпадение
        s = s.query(
            Q("bool",
              should=[
                  # Точный поиск по основному полю
                  Q("multi_match",
                    query=q,
                    fields=["name^5"],
                    type="phrase_prefix"),
                  # Частичный поиск по ngram полю
                  Q("multi_match",
                    query=q,
                    fields=["name.ngram^3"],
                    type="best_fields",
                    operator="or"),
                  # Wildcard поиск для максимальной гибкости
                  Q("wildcard", name=f"*{q.lower()}*")
              ])
        )

    s = s.source(includes=["name"])
    resp = s.execute()

    # Получаем ID найденных рабочих групп с релевантностью
    found_results = []
    for hit in resp.hits:
        found_results.append({
            'id': hit.meta.id,
            'score': hit.meta.score
        })

    return found_results
