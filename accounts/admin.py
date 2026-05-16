from django.contrib import admin

from accounts.forms import UserChangeFormCustom, UserCreationFormCustom
from accounts.models import User

# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = UserCreationFormCustom
    form = UserChangeFormCustom
    model = User

    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "joined_at")}),
    )
    add_fieldsets = (
        None,
        {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
        },
    )
    readonly_fields = ("last_login", "joined_at")
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
