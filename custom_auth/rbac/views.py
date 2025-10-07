# rbac/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Resource, Action, Permission, Role
from .serializers import ResourceSerializer, ActionSerializer, PermissionSerializer, RoleSerializer


class IsAdminPermission(IsAuthenticated):
    """Кастомное разрешение: Только пользователи с ролью Admin или superuser."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        return (user.is_superuser or 
                user.has_permission('permissions', 'manage'))


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAdminPermission]


class ActionViewSet(viewsets.ModelViewSet):
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = [IsAdminPermission]


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminPermission]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminPermission]

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Дополнительный endpoint: Пользователи с этой ролью."""
        role = self.get_object()
        users = role.users.all()
        serializer = RoleSerializer(role)
        return Response({'role': serializer.data, 'users_count': users.count()})
