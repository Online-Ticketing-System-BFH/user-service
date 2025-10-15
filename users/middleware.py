import json
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            try:
                duration = time.time() - request.start_time
                log_data = {
                    'timestamp': timezone.now().isoformat(),
                    'method': request.method,
                    'path': request.path,
                    'status': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'user_id': str(request.user.id) if request.user.is_authenticated else None,
                    'ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                }
                if 400 <= response.status_code < 600:
                    log_data['error'] = response.data if hasattr(response, 'data') else str(response.content)
                    logger.error('API Error', extra=log_data)
                else:
                    logger.info('API Request', extra=log_data)
            except Exception as e:
                logger.error(f"Logging error: {str(e)}")
        return response