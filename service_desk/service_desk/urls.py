from django.contrib import admin
from django.urls import path, include
from core.views import login_view, logout_view, home_redirect

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home_redirect, name="home"),
    path("auth/login/", login_view, name="login"),
    path("auth/logout/", logout_view, name="logout"),

    path("", include("core.urls")),
]

