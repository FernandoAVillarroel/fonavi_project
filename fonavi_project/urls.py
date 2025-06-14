# fonavi_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from autenticacion.views import MyLoginView

urlpatterns = [
    # Redirige la raíz al login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # Admin de Django
    path('administracion/', admin.site.urls),

    # Autenticación
    path('accounts/login/',  MyLoginView.as_view(),  name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    # URLs de la app empleados
    path('', include('empleados.urls')),
]