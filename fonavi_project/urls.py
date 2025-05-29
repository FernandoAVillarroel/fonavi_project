from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from autenticacion.views import MyLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/',  MyLoginView.as_view(),  name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Rutas de login/logout y recuperación de contraseña
    path('accounts/', include('django.contrib.auth.urls')),
]
