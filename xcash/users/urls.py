from django.urls import path
from django_smart_ratelimit import rate_limit

from .views import LoginView
from .views import SignupDisabledView

app_name = "users"

urlpatterns = [
    # 注册入口保留为显式 404，避免未命中 users.urls 后继续被 admin 默认路由兜底。
    path("signup", SignupDisabledView.as_view(), name="signup_disabled"),
    path(
        "login",
        rate_limit(
            key="ip",
            rate="100/h",
            skip_if=lambda req: req.method != "POST",
        )(LoginView.as_view()),
        name="login",
    ),
]
