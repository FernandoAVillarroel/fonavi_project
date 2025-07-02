from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse

@csrf_protect
def login_view(request):
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login exitoso. ¡Bienvenido!')
            
            # Redirigir al dashboard o a la URL especificada en 'next'
            if next_url:
                return redirect(next_url)
            else:
                return redirect('templates\dashboard.html')  # Reemplaza con el nombre de tu vista de dashboard
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Intenta nuevamente.')
    
    return render(request, 'registration/login.html')

@login_required
def dashboard_view(request):
    """Vista del dashboard - requiere autenticación"""
    context = {
        'user': request.user,
        'title': 'Dashboard - Sistema de Liquidación de Sueldos'
    }
    return render(request, 'dashboard/dashboard.html', context)

def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')