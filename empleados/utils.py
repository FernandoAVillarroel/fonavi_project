# empleados/utils.py
from datetime import date
from calendar import monthrange
from django.db.models import (
    Q,
    BooleanField,
    IntegerField,
    SmallIntegerField,
    PositiveSmallIntegerField,
    CharField,
    TextField,
)

# -----------------------------
# Constantes y helpers simples
# -----------------------------
MONTH_NAMES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo',  6: 'junio',   7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}

def month_name(mes: int) -> str:
    try:
        return MONTH_NAMES[int(mes)]
    except Exception:
        return str(mes)


# ----------------------------------
# Período en sesión (lectura/escritura) - CORREGIDO
# ----------------------------------
def set_periodo_en_sesion(request, anio: int, mes: int) -> None:
    """
    Setea el período de trabajo en la sesión y marca que fue elegido explícitamente.
    """
    anio = int(anio)
    mes = int(mes)
    
    # Validar mes
    if mes < 1 or mes > 12:
        # Si el mes es inválido, no hacer nada y salir
        return
    
    # Guardar en sesión
    request.session["PERIODO_ANIO"] = anio
    request.session["PERIODO_MES"] = mes
    request.session["PERIODO_STR"] = f"{anio:04d}-{mes:02d}"
    
    # SIEMPRE marcar como elegido cuando se llama explícitamente
    request.session["PERIODO_ELEGIDO"] = True
    
    # Forzar que Django guarde la sesión
    request.session.modified = True

# Alias por compatibilidad si en algún lugar llamabas a este nombre
def set_periodo_in_session(request, anio: int, mes: int) -> None:
    set_periodo_en_sesion(request, anio, mes)

def get_periodo_from_session(request):
    """
    Devuelve (anio:int, mes:int, periodo_str:'YYYY-MM') desde la sesión.
    Si no existe, cae al mes/año de HOY y normaliza el mes a 1..12.
    """
    hoy = date.today()
    
    # Obtener valores de la sesión o usar valores por defecto
    anio_sesion = request.session.get("PERIODO_ANIO")
    mes_sesion = request.session.get("PERIODO_MES")
    
    # Determinar si estamos usando valores por defecto o de sesión
    if anio_sesion is None or mes_sesion is None:
        # Usar período por defecto (hoy)
        anio = hoy.year
        mes = hoy.month
        request.session["PERIODO_ELEGIDO"] = False  # ← NO fue elegido
    else:
        # Usar valores de sesión
        anio = int(anio_sesion)
        mes = int(mes_sesion)
    
    # Validar mes
    if mes < 1 or mes > 12:
        mes = hoy.month
        request.session["PERIODO_MES"] = mes
    
    per = f"{anio:04d}-{mes:02d}"
    request.session["PERIODO_STR"] = per
    return anio, mes, per


# ----------------------------------
# Utilidades de período/fecha
# ----------------------------------
def period_bounds(anio: int, mes: int):
    """Devuelve (ini, fin) del mes seleccionado (date, date)."""
    anio = int(anio)
    mes = int(mes)
    ini = date(anio, mes, 1)
    fin = date(anio, mes, monthrange(anio, mes)[1])
    return ini, fin


# -------------------------------------------------------
# Filtro de "empleado activo en el período" (genérico)
# -------------------------------------------------------
def q_activo_en_periodo(anio: int, mes: int, estricto: bool = False, prefix: str = "empleado__") -> Q:
    """
    Construye un Q para filtrar "activo en el período" sobre distintos modelos.

    Reglas:
      - estado activo (1/True o textos típicos 'A', 'ACTIVO', '1', 'true', 'True')
      - y:
          estricto=False → (fecha_salida IS NULL o > fin del mes)
          estricto=True  → (fecha_salida IS NULL)

    `prefix` permite aplicarlo sobre modelos relacionados:
      - Liquidacion/Preliquidacion: prefix="empleado__"  (DEFAULT)
      - Empleado (directo):         prefix=""

    Ejemplos:
      Liquidacion.objects.filter(q_activo_en_periodo(2025, 9))                  # usa empleado__
      Empleado.objects.filter(q_activo_en_periodo(2025, 9, prefix=""))          # directo
    """
    anio = int(anio)
    mes = int(mes)
    fin = date(anio, mes, monthrange(anio, mes)[1])

    # Import tardío para evitar ciclos
    from .models import Empleado
    try:
        f_estado = Empleado._meta.get_field("estado")
    except Exception:
        f_estado = None

    def F(nombre: str) -> str:
        return f"{prefix}{nombre}" if prefix else nombre

    # Tipo del campo estado: numérico/bool vs texto
    if f_estado is None or isinstance(
        f_estado,
        (BooleanField, IntegerField, SmallIntegerField, PositiveSmallIntegerField),
    ):
        q_estado = (
            Q(**{F("estado"): 1})
            | Q(**{F("estado"): True})
            | Q(**{F("estado"): "1"})
        )
    elif isinstance(f_estado, (CharField, TextField)):
        q_estado = Q(**{F("estado") + "__in": ["A", "ACTIVO", "1", "true", "True"]})
    else:
        # Fallback conservador
        q_estado = Q(**{F("estado"): 1}) | Q(**{F("estado"): True})

    if estricto:
        q_salida = Q(**{F("fecha_salida") + "__isnull": True})
    else:
        q_salida = Q(**{F("fecha_salida") + "__isnull": True}) | Q(
            **{F("fecha_salida") + "__gt": fin}
        )

    return q_estado & q_salida

# Alias muy usado en vistas previas (compatibilidad):
def q_empleado_activo_en_periodo(anio: int, mes: int, estricto: bool = False) -> Q:
    """Versión con el prefijo 'empleado__' ya aplicado (histórico)."""
    return q_activo_en_periodo(anio, mes, estricto=estricto, prefix="empleado__")



# empleados/utils.py
from django.utils import timezone
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def selected_period_is_current(request) -> bool:
    """True si el período en sesión coincide con (año, mes) actuales."""
    anio, mes, _ = get_periodo_from_session(request)
    now = timezone.now()
    return (anio, mes) == (now.year, now.month)


# --- Decorador para FBV (function-based views) ---
def require_selected_period_current(redirect_name: str):
    """
    Bloquea acciones si el período seleccionado no es el actual.
    Uso:
      @require_selected_period_current('empleados:empleado-list')
      def empleado_update(request, ...):
          ...
    """
    def _decorator(viewfunc):
        @wraps(viewfunc)
        def _wrapped(request, *args, **kwargs):
            if not selected_period_is_current(request):
                messages.error(request, "No podés modificar empleados cuando el período seleccionado no es el actual.")
                return redirect(redirect_name)
            return viewfunc(request, *args, **kwargs)
        return _wrapped
    return _decorator


# --- Mixin para CBV (class-based views) ---
class RequireSelectedPeriodCurrentMixin:
    redirect_name = 'empleados:empleado-list'  # cambiá si tu nombre es otro

    def dispatch(self, request, *args, **kwargs):
        if not selected_period_is_current(request):
            messages.error(request, "No podés modificar empleados cuando el período seleccionado no es el actual.")
            return redirect(self.redirect_name)
        return super().dispatch(request, *args, **kwargs)


# empleados/utils.py
from datetime import date

def calcular_antiguedad_ipvu(fecha_ingreso, anio, mes):
    """
    Regla IPVU:
      - Antigüedad base se mide al 1.º de enero del año del PERÍODO.
      - En el 2.º semestre (mes >= 7) se suma +1.
      - Ej.: ingreso 11/12/2017, período 09/2025 -> base enero 2025 = 7; 2.º semestre => 8.
    """
    if not fecha_ingreso:
        return 0

    anio = int(anio); mes = int(mes)
    ref_enero = date(anio, 1, 1)

    # años "cumplidos" al 1.º de enero del año del período
    base = anio - fecha_ingreso.year
    if (fecha_ingreso.month, fecha_ingreso.day) > (1, 1):
        base -= 1
    base = max(base, 0)

    # +1 para el segundo semestre
    if mes >= 7:
        base += 1

    return base