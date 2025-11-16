import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
import random

PHONE_CLEAN_RE = re.compile(r'[ \-()\u00A0]')

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_id = models.IntegerField(unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)
    
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    address = models.JSONField(null=True, blank=True)

    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    email_verification_expires_at = models.DateTimeField(null=True, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['auth_id']),
            models.Index(fields=['email']),
        ]
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.email} (Auth ID: {self.auth_id})"

    def clean_phone_value(self, value: str | None) -> str | None:
        if not value:
            return value
        v = PHONE_CLEAN_RE.sub('', str(value)).strip()
        return v or None

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        self.phone = self.clean_phone_value(self.phone)
        super().save(*args, **kwargs)

    def generate_email_verification_code(self, length: int = 6, ttl_minutes: int = 10) -> str:
        code = "".join(random.choices("0123456789", k=length))
        now = timezone.now()
        self.email_verification_code = code
        self.email_verification_sent_at = now
        self.email_verification_expires_at = now + timedelta(minutes=ttl_minutes)
        self.is_email_verified = False
        self.save(update_fields=[
            "email_verification_code",
            "email_verification_expires_at",
            "email_verification_sent_at",
            "is_email_verified",
            "updated_at",
        ])
        return code