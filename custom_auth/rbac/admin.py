from django.contrib import admin
from .models import Resource, Action, Permission, Role

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['resource', 'action', 'description']
    list_filter = ['resource', 'action']
    search_fields = ['resource__name', 'action__name']
    ordering = ['resource__name', 'action__name']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'permissions_count']
    list_filter = ['permissions__resource__name']
    filter_horizontal = ['permissions']
    search_fields = ['name']
    ordering = ['name']

    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Количество разрешений'
