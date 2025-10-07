from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResourceViewSet, ActionViewSet, PermissionViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'resources', ResourceViewSet)
router.register(r'actions', ActionViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'roles', RoleViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
