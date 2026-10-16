import json
import logging
from time import perf_counter

from django.db import connection
from django.db.utils import InterfaceError, OperationalError
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string


logger = logging.getLogger('perf.request')
health_logger = logging.getLogger('core.health')


class _QueryTimer:
    def __init__(self):
        self.db_queries = 0
        self.db_time_ms = 0.0

    def __call__(self, execute, sql, params, many, context):
        start = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.db_queries += 1
            self.db_time_ms += (perf_counter() - start) * 1000


class PerformanceMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = perf_counter()
        query_timer = _QueryTimer()
        request._server_timing = {}

        with connection.execute_wrapper(query_timer):
            response = self.get_response(request)

        total_ms = (perf_counter() - start) * 1000
        timing_parts = getattr(request, '_server_timing', {})
        db_fetch_ms = float(timing_parts.get('db_fetch_ms', query_timer.db_time_ms))
        inference_ms = float(timing_parts.get('inference_ms', 0.0))
        render_ms = float(timing_parts.get('render_ms', 0.0))

        response['Server-Timing'] = (
            f"dbfetch;dur={db_fetch_ms:.2f}, "
            f"inference;dur={inference_ms:.2f}, "
            f"render;dur={render_ms:.2f}"
        )

        logger.info(
            json.dumps(
                {
                    'path': request.path,
                    'status': response.status_code,
                    'duration_ms': round(total_ms, 2),
                    'db_queries': query_timer.db_queries,
                    'db_time_ms': round(query_timer.db_time_ms, 2),
                }
            )
        )
        return response


class DatabaseUnavailableMiddleware:
    """Turn a database outage into a clear 503 instead of an opaque 500.

    The page is rendered without a request context on purpose: the normal base template
    reads the session and user, which would need the very database that is down.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (OperationalError, InterfaceError)):
            return None

        health_logger.error('Database unavailable on %s: %s', request.path, exception)
        wants_json = request.path.endswith('/data/') or 'application/json' in request.headers.get('Accept', '')
        if wants_json:
            response = JsonResponse({'error': 'database_unavailable'}, status=503)
        else:
            response = HttpResponse(render_to_string('503.html'), status=503)
        response['Retry-After'] = '30'
        response['Cache-Control'] = 'no-store'
        return response
