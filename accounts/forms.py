from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from accounts.models import User


class UserCreationFormCustom(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserChangeFormCustom(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "is_superuser",
            "groups",
            "user_permissions",
        )
