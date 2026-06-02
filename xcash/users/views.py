from django.contrib import admin
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.http import Http404
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic import View

from .forms import LoginForm
from .models import AdminAccessLog
from .models import User


def _safe_next_path(request) -> str:
    """从请求中提取 next 参数，仅允许同站相对路径，防止 Open Redirect。"""
    next_path = request.POST.get("next") or request.GET.get("next") or "/"
    if url_has_allowed_host_and_scheme(next_path, allowed_hosts=None):
        return next_path
    return "/"


def record_admin_access(
    *,
    request,
    action: str,
    result: str,
    user=None,
    reason: str = "",
    username_snapshot: str | None = None,
) -> None:
    username = (
        username_snapshot or getattr(user, "username", "") or "anonymous"
    ).strip() or "anonymous"
    AdminAccessLog.objects.create(
        user=user,
        username_snapshot=username[:150],
        ip=request.META.get("REMOTE_ADDR") or None,
        user_agent=request.headers.get("user-agent", "")[:1024],
        action=action,
        result=result,
        reason=reason[:1024],
    )


class AdminContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)  # noqa
        ctx.update(admin.site.each_context(self.request))  # noqa
        ctx["app_path"] = self.request.get_full_path()
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.is_staff
            and request.path != "/logout/"
        ):
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)


class LoginView(AdminContextMixin, FormView):
    form_class = LoginForm
    template_name = "auth/login.html"
    success_url = "/"

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user: User | None = authenticate(
            self.request, username=username, password=password
        )
        if user is None:
            record_admin_access(
                request=self.request,
                action=AdminAccessLog.Action.PASSWORD_LOGIN,
                result=AdminAccessLog.Result.FAILED,
                username_snapshot=username,
                reason="invalid_credentials",
            )
            self._password_login_failure_recorded = True
            form.add_error(None, _("用户名或密码错误。"))
            return self.form_invalid(form)

        auth_login(self.request, user)
        record_admin_access(
            request=self.request,
            action=AdminAccessLog.Action.PASSWORD_LOGIN,
            result=AdminAccessLog.Result.SUCCEEDED,
            user=user,
            reason="password_ok",
        )
        return redirect(_safe_next_path(self.request))

    def form_invalid(self, form):
        username = self.request.POST.get("username", "")
        if username and not getattr(self, "_password_login_failure_recorded", False):
            record_admin_access(
                request=self.request,
                action=AdminAccessLog.Action.PASSWORD_LOGIN,
                result=AdminAccessLog.Result.FAILED,
                username_snapshot=username,
                reason="invalid_credentials",
            )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("登录")
        context["next"] = _safe_next_path(self.request)
        return context


class SignupDisabledView(View):
    def dispatch(self, request, *args, **kwargs):
        # 注册能力已下线，显式返回 404 可避免请求继续落到 admin 默认路由。
        raise Http404(_("注册页面不存在。"))
