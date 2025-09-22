# empleados/context_processors.py
from datetime import date
from .utils import get_periodo_from_session, MONTH_NAMES

def periodo_global(request):
    """
    Variables globales de período para todas las plantillas.
    """
    try:
        anio, mes, per = get_periodo_from_session(request)
    except Exception:
        h = date.today()
        anio, mes, per = h.year, h.month, f"{h.year:04d}-{h.month:02d}"

    hoy = date.today()
    tupla_hoy = (hoy.year, hoy.month)
    tupla_sel = (int(anio), int(mes))

    return {
        "PERIODO_ANIO": int(anio),
        "PERIODO_MES": int(mes),
        "PERIODO_MES_STR": f"{int(mes):02d}",
        "PERIODO_MES_NOMBRE": MONTH_NAMES.get(int(mes), str(mes)),
        "PERIODO_ACTUAL": per,
        "PERIODO": per,
        "PERIODO_ES_ACTUAL": tupla_sel == tupla_hoy,
        "PERIODO_ES_FUTURO": tupla_sel > tupla_hoy,
        "PERIODO_ES_PASADO": tupla_sel < tupla_hoy,
        "PERIODO_ELEGIDO": bool(request.session.get("PERIODO_ELEGIDO", False)),
        # CRÍTICO: Esta variable debe ser una lista de tuplas (número, nombre)
        "MESES": [(i, MONTH_NAMES[i]) for i in range(1, 13)],
    }