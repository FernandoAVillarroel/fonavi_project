# empleados/views_novedades.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Q
from datetime import date

from .models import NovedadMensual
from .utils import get_periodo_from_session, MONTH_NAMES


def is_presidencia(user):
    return user.is_superuser or user.is_staff or user.groups.filter(name__iexact='PRESIDENCIA').exists()


@login_required(login_url="login")
@user_passes_test(is_presidencia)
def novedades_mensuales_list(request):
    """
    Lista de novedades del período que el usuario tiene en la sesión.
    Permite filtrar por 'tipo' (?tipo=...) y por texto (?q=...).
    """
    anio, mes, periodo_str = get_periodo_from_session(request)  # 'YYYY-MM'
    
    # Verificar estado del período
    hoy = date.today()
    es_periodo_actual = (anio == hoy.year and mes == hoy.month)
    
    # Obtener estado de la base de datos
    try:
        from .models import LiquidacionPeriodo
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        estado_bd = lp.estado if lp else 'SIN CREAR'
    except:
        estado_bd = 'SIN CREAR'
    
    # Lógica para mostrar alertas
    periodo_confirmado = (estado_bd == 'CONFIRMADA')
    periodo_abierto = (estado_bd == 'ABIERTA') or es_periodo_actual  # Período actual siempre abierto
    
    qs = NovedadMensual.objects.filter(periodo=periodo_str).order_by('-fecha')

    # Filtros opcionales
    tipo = (request.GET.get('tipo') or "").strip()
    q    = (request.GET.get('q') or "").strip()

    if tipo:
        qs = qs.filter(tipo__iexact=tipo)
    if q:
        qs = qs.filter(
            Q(descripcion__icontains=q) |
            Q(area__icontains=q) |
            Q(extra__icontains=q) |
            Q(empleado__apellido__icontains=q) |
            Q(empleado__nombre__icontains=q)
        )

    # PAGINACIÓN - 20 por página
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 20)  # 20 novedades por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Tipos disponibles para el selector
    tipos_novedad = (
        NovedadMensual.objects.filter(periodo=periodo_str)
        .values_list('tipo', flat=True).distinct().order_by('tipo')
    )

    contexto = {
        # datos de período para encabezados
        "PERIODO_ANIO": anio,
        "PERIODO_MES": mes,
        "PERIODO_MES_NOMBRE": MONTH_NAMES.get(int(mes), str(mes)),
        "PERIODO": periodo_str,

        # novedades PAGINADAS
        "page_obj": page_obj,
        "novedades": page_obj,  # mantener compatibilidad con template
        "total_novedades": paginator.count,
        
        # filtros aplicados
        "f_tipo": tipo,
        "f_q": q,
        "tipos_novedad": tipos_novedad,

        # control de permisos
        "periodo_confirmado": periodo_confirmado,
        "periodo_abierto": periodo_abierto,
    }
    return render(request, "empleados/novedades_mensuales.html", contexto)