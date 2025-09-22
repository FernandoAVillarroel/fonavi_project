# empleados/views_dashboard.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from .models import Empleado, LiquidacionPeriodo
from .utils import get_periodo_from_session, q_activo_en_periodo

@login_required(login_url='login')
def dashboard_empleados(request):
    anio, mes, per = get_periodo_from_session(request)
    
    # Obtener estado del período
    try:
        lp = LiquidacionPeriodo.objects.filter(periodo=per).first()
        estado = lp.estado if lp else 'SIN CREAR'
    except:
        estado = 'SIN CREAR'
    
    # Empleados activos en el período
    qs = Empleado.objects.filter(q_activo_en_periodo(anio, mes, prefix=""))
    
    total = qs.count()
    if total == 0:
        messages.info(request, f"No hay empleados para el período {per}.")
    
    # Calcular métricas de situación laboral
    permanentes = qs.filter(situacion='P').count()
    contratados = qs.filter(situacion='C').count()
    
    # Obtener novedades (aquí debes implementar la lógica según tu modelo de novedades)
    novedades = []  # Reemplazar con tu lógica para obtener novedades
    tipos_novedad = []  # Reemplazar con los tipos de novedad disponibles
    
    # Variables para el template
    from .utils import MONTH_NAMES
    mes_nombre = MONTH_NAMES.get(mes, str(mes)).upper()
    
    context = {
        "empleados": qs.order_by("apellido", "nombre"),
        "total_empleados": total,
        "total_activos": total,  # Todos los empleados filtrados están activos
        "total_inactivos": 0,    # Este valor deberías calcularlo según tu lógica
        
        # Nuevos campos añadidos
        "estado": estado,
        "PERIODO_MES_NOMBRE": mes_nombre,
        "PERIODO_ANIO": anio,
        "PERIODO_ELEGIDO": per != "Ninguno",  # Asumiendo que "Ninguno" significa no seleccionado
        
        # Métricas de situación laboral
        "permanentes": permanentes,
        "contratados": contratados,
        
        # Novedades
        "novedades": novedades,
        "tipos_novedad": tipos_novedad,
    }
    
    return render(request, "empleados/dashboard.html", context)