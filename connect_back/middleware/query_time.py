import time
import logging
from django.db import connections
from django.utils.deprecation import MiddlewareMixin
from app_info.models import AppInfo

logger = logging.getLogger('request_timing')


class QueryTimeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        # Генерируем уникальный ID для запроса
        request._request_id = int(time.time() * 1000000) % 1000000  # последние 6 цифр микросекунд

        # включаем сбор SQL-запросов даже если DEBUG=False
        for conn in connections.all():
            conn.force_debug_cursor = True
            conn.queries_log.clear()

    def _get_logging_settings(self):
        """Получаем настройки логирования из AppInfo"""
        try:
            app_info = AppInfo.objects.get(code='request_timing')
            return app_info.metadata
        except AppInfo.DoesNotExist:
            return {'total': False, 'sql': False}

    def process_response(self, request, response):
        settings = self._get_logging_settings()
        
        if not settings.get('total', False) and not settings.get('sql', False):
            return response

        # Логируем только API запросы
        path = request.get_full_path()
        if not path.startswith('/api/v1/'):
            return response

        total_time = time.time() - getattr(request, '_start_time', time.time())
        status = getattr(response, 'status_code', '???')
        method = request.method
        request_id = getattr(request, '_request_id', 0)

        # Логируем общее время запроса
        if settings.get('total', False):
            sql_time = 0.0
            sql_count = 0
            for conn in connections.all():
                queries = getattr(conn, 'queries', [])
                sql_count += len(queries)
                for q in queries:
                    try:
                        sql_time += float(q.get('time', 0))
                    except (TypeError, ValueError):
                        pass
            
            logger.info(
                f"ID:{request_id:06d} | total={total_time:7.3f}s | sql={sql_time:7.3f}s ({sql_count:3d}) | {status:3d} {method:<6} user={request.user} {path}"
            )

        # Логируем каждый SQL-запрос
        if settings.get('sql', False):
            sql_time = 0.0
            sql_count = 0
            
            for conn in connections.all():
                queries = getattr(conn, 'queries', [])
                sql_count += len(queries)
                
                for query in queries:
                    try:
                        query_time = float(query.get('time', 0))
                        sql_time += query_time
                        
                        # Получаем полный SQL-запрос
                        sql_text = query.get('sql', '')
                        
                        logger.info(
                            f"ID:{request_id:06d} | SQL: {query_time:7.3f}s | {sql_text}"
                        )
                    except (TypeError, ValueError):
                        pass

        return response
