from django.contrib import admin
from django.urls import path, re_path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings

schema_perms = (permissions.AllowAny,) if getattr(settings, 'SWAGGER_PUBLIC', True) else (permissions.IsAdminUser,)

schema_view = get_schema_view(
    openapi.Info(
        title="User Service API",
        default_version='v1',
        description="User profile management service for ticket booking system",
    ),
    public=getattr(settings, 'SWAGGER_PUBLIC', True),
    permission_classes=schema_perms,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('users.urls')),
    path('', include('django_prometheus.urls')),

    re_path(r'^openapi(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
