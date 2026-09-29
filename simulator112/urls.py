from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import include, path


def logout_view(request):
    logout(request)
    return redirect("login")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", logout_view, name="logout"),
    path("", include("training.urls")),
]
