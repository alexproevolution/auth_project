from django.db import models


class Resource(models.Model):
    """Ресурсы системы (e.g., user_profile)."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название ресурса")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Ресурс"
        verbose_name_plural = "Ресурсы"

    def __str__(self):
        return self.name


class Action(models.Model):
    """Действия над ресурсами (e.g., update)."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название действия")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Действие"
        verbose_name_plural = "Действия"

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Разрешение: ресурс + действие."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name="Ресурс")
    action = models.ForeignKey(Action, on_delete=models.CASCADE, verbose_name="Действие")
    description = models.TextField(blank=True, verbose_name="Описание разрешения")

    class Meta:
        unique_together = ('resource', 'action')  # Уникальная пара
        verbose_name = "Разрешение"
        verbose_name_plural = "Разрешения"

    def __str__(self):
        return f"{self.resource.name}_{self.action.name}"


class Role(models.Model):
    """Роль: набор разрешений."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    description = models.TextField(blank=True, verbose_name="Описание")
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name="Разрешения")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name

    def has_permission(self, resource_name, action_name):
        """Утилита: Проверяет, есть ли у роли конкретное разрешение."""
        return self.permissions.filter(
            resource__name=resource_name,
            action__name=action_name
        ).exists()
