 # urls.py de tu app
from django.contrib import admin
from django.urls import path, include
from autenticacion import views


urlpatterns = [
    path('', views.login_view, name='login'),  # Página principal será login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('', include('empleados.urls')),
]

# Si estás usando el urls.py principal del proyecto, también agrega:
# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('tu_app.urls')),  # Reemplaza 'tu_app' con el nombre real
# ]