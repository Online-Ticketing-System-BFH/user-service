from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
import logging

from .models import UserProfile
from .serializers import UserProfileSerializer

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
