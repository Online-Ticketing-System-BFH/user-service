import json
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

logger = logging.getLogger(__name__)

class GatewayUser:
    def __init__(self, auth_id, roles):
        self.auth_id = auth_id
        self.roles = roles
        self.is_authenticated = True
        self.is_staff = 'admin' in [r.lower() for r in roles]

    @property
    def id(self):
        return self.auth_id

    def __str__(self):
        return f"GatewayUser(auth_id={self.auth_id}, roles={self.roles})"

class GatewayHeaderMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_id = request.META.get('HTTP_X_USER_ID')
        roles_str = request.META.get('HTTP_X_USER_ROLES', '')
        
        if auth_id:
            roles = [r.strip() for r in roles_str.split(',') if r.strip()]
            request.user = GatewayUser(auth_id=int(auth_id), roles=roles)
        # We don't need to do anything for else, Django's default user is already unauthenticated

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