# empleados/views_novedades.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Q

from .models import NovedadMensual
from .utils import get_periodo_from_session, MONTH_NAMES

# Si ya tenés este helper en otro lado, podés borrar esta función y reusar la tuya
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
            Q(extra__icontains=q)
        )

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

        # listado y filtros
        "novedades": qs,
        "tipos_novedad": tipos_novedad,
        "f_tipo": tipo,
        "f_q": q,
    }
    return render(request, "empleados/novedades_mensuales.html", contexto)
