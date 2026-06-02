from django import forms
from django.contrib.auth import forms as admin_forms
from django.utils.translation import gettext_lazy as _
from unfold.widgets import UnfoldAdminPasswordWidget
from unfold.widgets import UnfoldAdminTextInputWidget

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = "__all__"


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("username",)
        error_messages = {"username": {"unique": _("此用户名已被使用.")}}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = UnfoldAdminTextInputWidget()
        self.fields["password1"].widget = UnfoldAdminPasswordWidget(
            attrs={"autocomplete": "new-password"}
        )
        self.fields["password2"].widget = UnfoldAdminPasswordWidget(
            attrs={"autocomplete": "new-password"}
        )


class LoginForm(forms.Form):
    """
    Form used by the public admin login entrance.
    """

    username = forms.CharField(
        required=True,
        label=_("用户名"),
        widget=UnfoldAdminTextInputWidget(),
    )
    password = forms.CharField(
        required=True,
        label=_("密码"),
        widget=UnfoldAdminPasswordWidget(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                raise forms.ValidationError(_("此账户已被禁用，如有疑问请联系管理员。"))
        except User.DoesNotExist as exc:
            raise forms.ValidationError("此用户名未注册。") from exc

        return cleaned_data
