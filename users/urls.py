from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet
from django.http import JsonResponse

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet)

def healthz(_): return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('', include(router.urls)),
    path('healthz/', healthz)
]
