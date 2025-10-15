import logging
from celery import shared_task
from django.core.cache import cache
from .models import UserProfile

logger = logging.getLogger(__name__)


@shared_task
def sync_user_with_auth_service(user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
        # Запрос к auth-service
        # Обновление данных пользователя
    except UserProfile.DoesNotExist:
        logger.error(f"User {user_id} not found")