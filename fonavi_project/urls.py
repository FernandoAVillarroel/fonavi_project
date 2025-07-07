# fonavi_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from autenticacion.views import MyLoginView
from empleados.views import (
    presidencia_dashboard,
    generar_preliquidacion,
    confirmar_liquidacion,
)

urlpatterns = [
    # 1) Redirige la raíz al login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # 2) Panel de administración de Django
    path('administracion/', admin.site.urls),

    # 3) Autenticación (login / logout / demás)
    path('accounts/login/',  MyLoginView.as_view(),               name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
                                 next_page='login'),
                                 name='logout'),
    path('accounts/',        include('django.contrib.auth.urls')),

    # 4) Área Presidencia
    path('presidencia/',         presidencia_dashboard,    name='presidencia_dashboard'),
    path('presidencia/generar/', generar_preliquidacion,   name='preliquidacion-generar'),
    path('presidencia/confirmar/', confirmar_liquidacion,  name='liquidacion-confirmar'),

    # 5) Resto de URLs de tu app empleados (listas, formularios ABM, etc)
    path('', include('empleados.urls')),
]
