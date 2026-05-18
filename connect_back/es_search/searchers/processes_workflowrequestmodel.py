from elasticsearch_dsl import Q
from ..documents import WorkflowRequestDocument


def search_processes_workflowrequestmodel(search: str):
    """Поиск по заявкам (WorkflowRequestModel): суффикс по номеру + полнотекст по описанию.
    Возвращает список словарей {'id', 'score'} без учета видимости.
    """
    query_string = (search or "").strip()
    s = WorkflowRequestDocument.search()

    if query_string:
        should_clauses = []
        # Суффикс по номеру только когда ищут одним числом (077, 0077, 00077).
        # Запрос делаем через match: search_analyzer (reverse) развернёт строку,
        # а термы в индексе уже развёрнуты и нарезаны edge_ngram.
        if query_string.isdigit() and len(query_string) >= 3:
            should_clauses.append(
                Q("match", number_suffix={"query": query_string, "boost": 4})
            )
        should_clauses.append(
            Q(
                "match",
                description={
                    "query": query_string,
                    "operator": "or",
                    "boost": 2,
                },
            )
        )
        s = s.query(
            Q(
                "bool",
                should=should_clauses,
                minimum_should_match=1,
            )
        )

    s = s[0:300]
    s = s.source(False)
    resp = s.execute()

    results = []
    if resp.hits:
        max_score = resp.hits[0].meta.score if resp.hits else 0
        score_threshold = max_score * 0.2 if max_score >= 2 else 0
        for hit in resp.hits:
            if hit.meta.score >= score_threshold:
                results.append({
                    "id": hit.meta.id,
                    "score": hit.meta.score,
                })
    return results
