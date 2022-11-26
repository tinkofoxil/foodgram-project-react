from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(UserAdmin):
    """Модель администрирование пользователей."""

    list_display = (
            'email',
            'username',
            'first_name',
            'last_name',
    )
    list_filter = ('email', 'username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Модель администрирование подписок."""

    list_display = ('user', 'author')
