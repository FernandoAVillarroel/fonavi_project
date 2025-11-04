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

def calcular_antiguedad_ipvu(fecha_ingreso, anio_ref, mes_ref):
    """
    Calcula antigüedad según REGLA IPVU:
    - Ingreso en primeros 6 meses (ene-jun): suma 1 año el 1º enero siguiente
    - Ingreso en últimos 6 meses (jul-dic): NO suma año el 1º enero siguiente
    
    Ejemplos:
    - Ingreso 15/03/2024 → 01/01/2025: 1 año ✓
    - Ingreso 15/08/2024 → 01/01/2025: 0 años ✓
    - Ingreso 15/08/2024 → 01/01/2026: 1 año ✓
    """
    if not fecha_ingreso:
        return 0
    
    ref = date(anio_ref, mes_ref, 1)
    
    # Si la referencia es anterior al ingreso, antigüedad = 0
    if ref < fecha_ingreso:
        return 0
    
    # Años transcurridos desde el año de ingreso
    anios = anio_ref - fecha_ingreso.year
    
    # Aplicar regla IPVU según mes de ingreso
    if fecha_ingreso.month <= 6:
        # Ingresó enero-junio: suma 1 año desde el 1º enero siguiente
        return anios
    else:
        # Ingresó julio-diciembre: NO suma el 1º enero siguiente
        # Recién suma desde el segundo 1º enero
        return max(anios - 1, 0)



# empleados/utils.py
from django.utils import timezone

def get_periodo_actual():
    """Devuelve el período actual en formato YYYY-MM"""
    now = timezone.now()
    return now.strftime("%Y-%m")

def get_novedades_por_periodo(periodo):
    """Obtiene todas las novedades de un período específico"""
    from .models import Novedad
    return Novedad.objects.filter(periodo=periodo).select_related('empleado')

def crear_novedad_manual(periodo, tipo, descripcion, empleado=None, objeto_relacionado=None):
    """Crea una novedad manualmente"""
    from .models import Novedad
    from django.contrib.contenttypes.models import ContentType
    
    novedad = Novedad(
        periodo=periodo,
        tipo=tipo,
        descripcion=descripcion,
        empleado=empleado
    )
    
    if objeto_relacionado:
        novedad.content_type = ContentType.objects.get_for_model(objeto_relacionado)
        novedad.object_id = objeto_relacionado.id
    
    novedad.save()
    return novedad

# empleados/utils.py
from decimal import Decimal

def to_decimal(raw):
    """Convierte formato argentino (10.000,00) a Decimal"""
    if raw is None:
        return Decimal('0')
    s = str(raw).strip()
    s = s.replace('.', '').replace(',', '.')  # quita miles, coma → punto
    try:
        return Decimal(s)
    except Exception:
        return Decimal('0')