import logging
import random
from celery import shared_task
from django.core.cache import cache
from .models import UserProfile
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def sync_user_with_auth_service(user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
        # Запрос к auth-service
        # Обновление данных пользователя
    except UserProfile.DoesNotExist:
        logger.error(f"User {user_id} not found")


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_verification_task(self, user_profile_id: str):
    try:
        profile = UserProfile.objects.get(id=user_profile_id, deleted_at=None)
    except UserProfile.DoesNotExist:
        logger.warning("UserProfile not found for email verification", extra={"user_profile_id": user_profile_id})
        return

    if profile.is_email_verified:
        logger.info("Email already verified, skipping send_email_verification", extra={"user_profile_id": user_profile_id})
        return

    code = profile.generate_email_verification_code(length=6, ttl_minutes=10)

    subject = "Email verification"
    message = (
        f"Здравствуйте!\n\n"
        f"Ваш код подтверждения email: {code}\n"
        f"Срок действия кода: 10 минут.\n\n"
        f"Если вы не запрашивали этот код, просто игнорируйте письмо."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@user-service.local")
    recipient_list = [profile.email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as exc:
        logger.exception(
            "Failed to send verification email",
            extra={"user_profile_id": user_profile_id, "email": profile.email},
        )
        raise self.retry(exc=exc)

    logger.info(
        "Verification email sent",
        extra={"user_profile_id": str(profile.id), "email": profile.email},
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_booking_confirmation_email_task(self, auth_id, event_data):
    """Send booking confirmation email to customer."""
    try:
        profile = UserProfile.objects.get(auth_id=auth_id, deleted_at=None)
    except UserProfile.DoesNotExist:
        logger.warning(f"UserProfile not found for auth_id {auth_id} during booking confirmation")
        return

    reservation_id = event_data.get("reservation_id")
    seat_count = len(event_data.get("seat_ids", []))

    subject = "Booking Confirmed!"
    message = (
        f"Здравствуйте, {profile.first_name or profile.username}!\n\n"
        f"Ваше бронирование #{reservation_id} успешно подтверждено.\n"
        f"Количество мест: {seat_count}\n\n"
        f"Ваши билеты доступны в личном кабинете.\n"
        f"Спасибо, что выбрали нас!"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@user-service.local")
    recipient_list = [profile.email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"Booking confirmation email sent to {profile.email}")
    except Exception as exc:
        logger.exception(f"Failed to send booking confirmation email to {profile.email}")
        raise self.retry(exc=exc)