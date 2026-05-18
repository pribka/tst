import time
import logging
from typing import List, Tuple
from django.utils.deprecation import MiddlewareMixin
from django.db import connections

logger = logging.getLogger("request_timing")


class _SQLTimer:
    """Колбэк-обёртка для connection.execute_wrapper; суммирует время выполнения SQL."""
    def __init__(self):
        self.total_seconds = 0.0

    def __call__(self, execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.total_seconds += (time.perf_counter() - start)


class RequestTimingMiddleware(MiddlewareMixin):
    """
    Логирует:
      - client ip (первым полем)
      - total_duration_ms
      - sql_duration_ms (сумма по всем БД)
      - bytes (объём ответа)
      - method
      - user
      - status
      - url (path?query)
    Без включения DEBUG/connection.queries.
    """

    def process_request(self, request):
        request._rt_start = time.perf_counter()
        request._rt_sql_contexts: List[Tuple[str, _SQLTimer, object]] = []

        for alias in connections.databases.keys():
            timer = _SQLTimer()
            cm = connections[alias].execute_wrapper(timer)
            cm.__enter__()
            request._rt_sql_contexts.append((alias, timer, cm))

    def process_exception(self, request, exception):
        # важно: снять wrapper'ы при любой ошибке
        self._close_sql_wrappers(request)

    def _close_sql_wrappers(self, request) -> float:
        sql_total = 0.0
        contexts = getattr(request, "_rt_sql_contexts", [])
        for _alias, timer, cm in contexts:
            try:
                cm.__exit__(None, None, None)
            finally:
                sql_total += timer.total_seconds
        request._rt_sql_contexts = []
        return sql_total

    def _get_client_ip(self, request) -> str:
        """
        Берём IP из X-Forwarded-For / X-Real-IP (если есть прокси),
        иначе REMOTE_ADDR.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            # первый в списке — исходный клиент
            ip = xff.split(",")[0].strip()
            if ip:
                return ip

        xri = request.META.get("HTTP_X_REAL_IP")
        if xri:
            return xri.strip()

        return request.META.get("REMOTE_ADDR", "-")

    def _build_url(self, request) -> str:
        path = getattr(request, "path", "-")
        query = request.META.get("QUERY_STRING")
        return f"{path}?{query}" if query else path

    def _get_username(self, request) -> str:
        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            return getattr(request.user, "username", None) or str(request.user)
        return "anonymous"

    def process_response(self, request, response):
        client_ip = self._get_client_ip(request)
        method = getattr(request, "method", "-")
        url = self._build_url(request)
        status = getattr(response, "status_code", 0)
        username = self._get_username(request)

        # STREAMING: логируем после полного стрима + там же закрываем SQL wrappers
        if getattr(response, "streaming", False) and hasattr(response, "streaming_content"):
            start = getattr(request, "_rt_start", time.perf_counter())
            original = response.streaming_content

            def wrapped(gen):
                total = 0
                try:
                    for chunk in gen:
                        if isinstance(chunk, str):
                            total += len(chunk.encode("utf-8"))
                            yield chunk
                        else:
                            total += len(chunk)
                            yield chunk
                finally:
                    sql_total = self._close_sql_wrappers(request)
                    total_duration = (time.perf_counter() - start)

                    logger.info(
                        "ip=%-15s  "
                        "dur_ms=%8.1f  "
                        "sql_ms=%8.1f  "
                        "bytes=%8d  "
                        "method=%-6s  "
                        "user=%-20s  "
                        "status=%3d  "
                        "url=\"%s\"",
                        client_ip,
                        total_duration * 1000.0,
                        sql_total * 1000.0,
                        total,
                        method,
                        username,
                        status,
                        url,
                    )

            response.streaming_content = wrapped(original)
            return response

        # НЕ streaming: можно сразу узнать bytes и закрыть wrappers
        sql_total = self._close_sql_wrappers(request)

        size_bytes = 0
        if response.has_header("Content-Length"):
            try:
                size_bytes = int(response["Content-Length"])
            except Exception:
                size_bytes = 0
        elif hasattr(response, "content"):
            size_bytes = len(response.content)

        total_duration = (time.perf_counter() - getattr(request, "_rt_start", time.perf_counter()))

        logger.info(
            "ip=%-15s  "
            "dur_ms=%8.1f  "
            "sql_ms=%8.1f  "
            "bytes=%8d  "
            "method=%-6s  "
            "user=%-20s  "
            "status=%3d  "
            "url=\"%s\"",
            client_ip,
            total_duration * 1000.0,
            sql_total * 1000.0,
            int(size_bytes),
            method,
            username,
            status,
            url,
        )

        return response
