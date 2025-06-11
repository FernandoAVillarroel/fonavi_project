from django.contrib.auth.views import LoginView
from django.shortcuts import render
from .models import Usuarios
from .models import Empleados
from .models import Oficinas

def lista_oficinas(request):
    oficinas = Oficinas.objects.all()
    return render(request, 'autenticacion/lista_oficinas.html', {'oficinas': oficinas})

def lista_empleados(request):
    empleados = Empleados.objects.all()
    return render(request, 'autenticacion/lista_empleados.html', {'empleados': empleados})

class MyLoginView(LoginView):
    template_name = 'registration/login.html'

def menu_admin(request):
    usuario = Usuarios.objects.filter(nombre=request.user.username).first()
    if usuario and usuario.tipo == 1:
        return render(request, 'autenticacion/menu_admin.html')
    else:
        return render(request, 'no_autorizado.html')

def menu_listados(request):
    return render(request, 'autenticacion/menu_listados.html')