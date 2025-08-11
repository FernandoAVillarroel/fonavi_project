# fonavi_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from autenticacion.views import MyLoginView

urlpatterns = [
    # 1) Raíz → login
    path("", RedirectView.as_view(pattern_name="login", permanent=False), name="root"),

    # 2) Admin de Django
    path("admin/", admin.site.urls),

    # 3) Autenticación
    path("accounts/login/", MyLoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(
            next_page="login",
            http_method_names=["get", "post"],
        ),
        name="logout",
    ),
    path("accounts/", include("django.contrib.auth.urls")),

    # 4) Área Presidencia (se incluyen las rutas desde el app, sin importar views aquí)
    path("presidencia/", include("empleados.presidencia_urls")),

    # 5) App empleados (CRUDs y demás)
    path("empleados/", include(("empleados.urls", "empleados"), namespace="empleados")),
]
