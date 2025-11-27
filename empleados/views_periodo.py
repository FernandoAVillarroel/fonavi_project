from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from .utils import set_periodo_en_sesion, MONTH_NAMES

@login_required(login_url="login")
@require_POST
def seleccionar_periodo(request):
    print("=== DEBUG seleccionar_periodo ===")
    print(f"POST data: {request.POST}")
    print(f"Session ANTES: ANIO={request.session.get('PERIODO_ANIO')}, MES={request.session.get('PERIODO_MES')}, ELEGIDO={request.session.get('PERIODO_ELEGIDO')}")
    
    try:
        anio = int(request.POST.get("anio"))
        mes = int(request.POST.get("mes"))  # viene numérico desde el <option value="num">
        print(f"Valores parseados: anio={anio}, mes={mes}")
    except (TypeError, ValueError) as e:
        print(f"Error parseando valores: {e}")
        messages.error(request, "Período inválido.")
        return redirect("periodo_panel")

    if not 1 <= mes <= 12:
        print(f"Mes fuera de rango: {mes}")
        messages.error(request, "Mes inválido.")
        return redirect("periodo_panel")

    # Usar la función principal, no el aliasf
    set_periodo_en_sesion(request, anio, mes)
    
    print(f"Session DESPUÉS: ANIO={request.session.get('PERIODO_ANIO')}, MES={request.session.get('PERIODO_MES')}, ELEGIDO={request.session.get('PERIODO_ELEGIDO')}")
    print("=== FIN DEBUG ===")

    messages.success(request, f"Período cambiado a {MONTH_NAMES[mes].capitalize()} de {anio}.")
    return redirect("periodo_panel")