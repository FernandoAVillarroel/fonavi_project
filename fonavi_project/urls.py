from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from autenticacion.views import MyLoginView, menu_admin, menu_listados, lista_empleados, lista_oficinas  # Importa la vista del menú

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(), name='home'),  # Mostrar login en la raíz
    path('menu/', menu_admin, name='menu_admin'),   # Ruta para el menú de admin
    path('listados/', menu_listados, name='menu_listados'),  # Ruta para el menú de listados
    path('empleados/', lista_empleados, name='lista_empleados'),   # Ruta para la lista de empleados
    path('oficinas/', lista_oficinas, name='lista_oficinas'),   # Ruta para la lista de oficina
    path('accounts/login/', MyLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]