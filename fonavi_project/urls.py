# fonavi_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from autenticacion.views import MyLoginView
from empleados.views_periodo import seleccionar_periodo
from empleados.views_liquidacion import (
    periodo_panel, crear_liquidacion, cerrar_liquidacion,
    reabrir_liquidacion, confirmar_liquidacion,
    ver_liquidacion_periodo, 
)

urlpatterns = [
    # Raíz → login
    path("", RedirectView.as_view(pattern_name="login", permanent=False), name="root"),

    # Admin de Django
    path("admin/", admin.site.urls),

    # Autenticación
    path("accounts/login/", MyLoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login", http_method_names=["get", "post"]),
        name="logout",
    ),
    path("accounts/", include("django.contrib.auth.urls")),

    # Presidencia (usa empleados/presidencia_urls.py)
    path("presidencia/", include("empleados.presidencia_urls")),

    # App empleados (CRUDs y demás)
    path("empleados/", include(("empleados.urls", "empleados"), namespace="empleados")),

    # Selector de período (desde el sidebar)
    path("seleccionar-periodo/", seleccionar_periodo, name="seleccionar_periodo"),

    # Panel del período y acciones de estado
    path("periodo/", periodo_panel, name="periodo_panel"),
    path("periodo/crear/", crear_liquidacion, name="crear_liquidacion"),
    path("periodo/cerrar/", cerrar_liquidacion, name="cerrar_liquidacion"),
    path("periodo/reabrir/", reabrir_liquidacion, name="reabrir_liquidacion"),
    path("periodo/confirmar/", confirmar_liquidacion, name="confirmar_liquidacion"),
    path("periodo/ver/", ver_liquidacion_periodo, name="ver_liquidacion_periodo"),
]
