# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import MyUser   
from .forms import MyUserCreationForm, MyUserChangeForm
from django.utils import timezone


class MyUserAdmin(BaseUserAdmin):
    """Кастомная админка для MyUser."""

    form = MyUserChangeForm
    add_form = MyUserCreationForm

    list_display = (
        'email',
        'first_name',
        'last_name',
        'middle_name',
        'is_staff',
        'is_active',
        'deleted_at',
        'date_joined'
    )

    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'date_joined',
        'deleted_at',
    )

    search_fields = ('email', 'first_name', 'last_name', 'middle_name')
    ordering = ('last_name', 'first_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'middle_name')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {'fields': ('date_joined', 'deleted_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'middle_name',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )

    readonly_fields = ('date_joined', 'deleted_at')


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(deleted_at__isnull=True, is_active=True)

    def delete_model(self, request, obj):
        """Мягкое удаление одного пользователя."""
        obj.is_active = False
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['is_active', 'deleted_at'])

    def delete_queryset(self, request, queryset):
        """Мягкое удаление нескольких пользователей."""
        queryset.update(is_active=False, deleted_at=timezone.now())

    def undelete_users(self, request, queryset):
        """Восстановить выбранных удалённых пользователей."""
        count = 0
        for user in queryset:
            if not user.is_active and user.deleted_at:
                user.is_active = True
                user.deleted_at = None
                user.save(update_fields=['is_active', 'deleted_at'])
                count += 1
        self.message_user(request, f'Восстановлено {count} пользователей.')
    undelete_users.short_description = 'Восстановить выбранных пользователей'

    actions = ['delete_queryset', 'undelete_users']


admin.site.register(MyUser, MyUserAdmin)
