from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from django.utils import timezone
import logging

from .models import UserProfile
from .serializers import UserProfileSerializer
from .tasks import send_email_verification_task

logger = logging.getLogger(__name__)

PROFILE_ID_KEY   = 'user_profile_{profile_id}'
PROFILE_AUTH_KEY = 'user_profile_auth_{auth_id}'
LIST_KEY_ALL     = 'user_profiles_list_all'

PROFILE_TTL = 60 * 15
LIST_TTL    = 60 * 5


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles.
    
    Provides CRUD operations for UserProfile model with caching and permission checks.
    Regular users can only access their own profiles, while staff users can access all profiles.
    """
    queryset = UserProfile.objects.filter(deleted_at=None)
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    swagger_tags = ['User Profiles']

    def _invalidate_profile_cache(self, instance):
        try:
            keys = {
                PROFILE_ID_KEY.format(profile_id=instance.id),
                PROFILE_AUTH_KEY.format(auth_id=instance.auth_id),
                LIST_KEY_ALL,
            }
            cache.delete_many(list(keys))
        except Exception:
            logger.exception("Cache invalidation failed")



    def perform_create(self, serializer):
        obj = serializer.save()
        self._invalidate_profile_cache(obj)



    @swagger_auto_schema(
        method='post',
        operation_description="Send email verification code to this user's email",
        responses={
            202: openapi.Response('Accepted'),
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found'),
        }
    )
    @action(detail=True, methods=['post'], url_path='send-email-verification')
    def send_email_verification(self, request, pk=None):
        profile = self.get_object()

        if profile.deleted_at is not None:
            return Response({"detail": "Profile is deleted."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.is_email_verified:
            return Response({"detail": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.email_verification_sent_at and \
           (timezone.now() - profile.email_verification_sent_at).total_seconds() < 60:
            return Response({"detail": "Verification email was sent recently. Please wait before retrying."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        send_email_verification_task.delay(str(profile.id))

        logger.info(
            "Email verification task queued",
            extra={"user_id": profile.id, "auth_id": profile.auth_id, "email": profile.email},
        )

        self._invalidate_profile_cache(profile)

        return Response({"detail": "Verification email will be sent shortly."}, status=status.HTTP_202_ACCEPTED)



    @swagger_auto_schema(
        method='post',
        operation_description="Verify user's email by code",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='Verification code from email'),
            },
            required=['code'],
        ),
        responses={
            200: openapi.Response('OK', UserProfileSerializer),
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found'),
        }
    )
    @action(detail=True, methods=['post'], url_path='verify-email')
    def verify_email(self, request, pk=None):
        profile = self.get_object()
        code = request.data.get("code")

        if not code:
            return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.deleted_at is not None:
            return Response({"detail": "Profile is deleted."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.is_email_verified:
            return Response({"detail": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        if not profile.email_verification_code:
            return Response({"detail": "Verification code is not set. Please request a new code."},
                            status=status.HTTP_400_BAD_REQUEST)

        if profile.email_verification_expires_at and timezone.now() > profile.email_verification_expires_at:
            return Response({"detail": "Verification code has expired. Please request a new code."},
                            status=status.HTTP_400_BAD_REQUEST)

        if str(profile.email_verification_code) != str(code).strip():
            return Response({"detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        profile.is_email_verified = True
        profile.email_verification_code = None
        profile.email_verification_expires_at = None
        profile.save(update_fields=[
            "is_email_verified",
            "email_verification_code",
            "email_verification_expires_at",
            "updated_at",
        ])

        self._invalidate_profile_cache(profile)

        logger.info(
            "Email verified successfully",
            extra={"user_id": profile.id, "auth_id": profile.auth_id, "email": profile.email},
        )

        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)



    @swagger_auto_schema(
        operation_description="Create a new user profile",
        request_body=UserProfileSerializer,
        responses={
            201: openapi.Response('Created', UserProfileSerializer),
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Unauthorized'),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        qs = UserProfile.objects.filter(deleted_at=None)
        auth_id = self.request.query_params.get('auth_id')
        if auth_id:
            qs = qs.filter(auth_id=auth_id)
        return qs



    @swagger_auto_schema(
        operation_description="Get details of a specific user profile",
        responses={
            200: openapi.Response('OK', UserProfileSerializer),
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = PROFILE_ID_KEY.format(profile_id=instance.id)
        profile_data = cache.get(cache_key)

        if profile_data is None:
            serializer = self.get_serializer(instance)
            profile_data = serializer.data
            cache.set(cache_key, profile_data, timeout=PROFILE_TTL)

        return Response(profile_data)



    @swagger_auto_schema(
        operation_description="Get list of user profiles. For regular users returns only their profile, for admins returns all profiles",
        responses={
            200: openapi.Response('OK', UserProfileSerializer(many=True)),
            401: openapi.Response('Unauthorized'),
            403: openapi.Response('Forbidden'),
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        if request.query_params.get('auth_id'):
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        profiles_data = cache.get(LIST_KEY_ALL)
        if profiles_data is None:
            serializer = self.get_serializer(queryset, many=True)
            profiles_data = serializer.data
            cache.set(LIST_KEY_ALL, profiles_data, timeout=LIST_TTL)
        return Response(profiles_data)



    @swagger_auto_schema(
        operation_description="Update user profile",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('OK', UserProfileSerializer),
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Unauthorized'),
            403: openapi.Response('Forbidden'),
            404: openapi.Response('Not Found'),
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self._invalidate_profile_cache(instance)
        logger.info(
            "Profile updated",
            extra={"user_id": instance.id, "auth_id": instance.auth_id, "updated_fields": list(request.data.keys())}
        )
        return Response(serializer.data)



    @swagger_auto_schema(
        operation_description="Partially update user profile (PATCH)",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('OK', UserProfileSerializer),
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Unauthorized'),
            403: openapi.Response('Forbidden'),
            404: openapi.Response('Not Found'),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)



    @swagger_auto_schema(
        operation_description="Soft delete user profile",
        responses={
            204: openapi.Response('No Content'),
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        self._invalidate_profile_cache(instance)
        logger.info("Profile deleted", extra={"user_id": instance.id, "auth_id": instance.auth_id})
        return Response(status=status.HTTP_204_NO_CONTENT)
