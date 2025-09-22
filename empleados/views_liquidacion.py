# empleados/views_liquidacion.py
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.utils import timezone  # usar timezone.now()

from .models import (
    LiquidacionPeriodo,
    Preliquidacion,
    Liquidacion,
    Calificacion,      # necesario
    OficioJudicial,    # necesario
)

# --------------------------------------------
# Helpers de período guardado en sesión
# --------------------------------------------
def _per_default():
    """Devuelve (año, mes, 'YYYY-MM') del HOY."""
    h = date.today()
    return h.year, h.month, f"{h.year:04d}-{h.month:02d}"

def set_periodo_in_session(request, anio, mes):
    request.session["PERIODO_ANIO"] = int(anio)
    request.session["PERIODO_MES"]  = int(mes)
    request.session["PERIODO_STR"]  = f"{int(anio):04d}-{int(mes):02d}"

def get_periodo_from_session(request):
    """Lee (año, mes) de sesión o setea el actual si no hay nada."""
    anio = request.session.get("PERIODO_ANIO")
    mes  = request.session.get("PERIODO_MES")
    if not anio or not mes:
        anio, mes, per = _per_default()
        set_periodo_in_session(request, anio, mes)
        return anio, mes, per
    return int(anio), int(mes), f"{int(anio):04d}-{int(mes):02d}"

# Para el <select> de meses
MESES = [f"{i:02d}" for i in range(1, 13)]

# --------------------------------------------
# Permisos (usa tu helper real si existe)
# --------------------------------------------
try:
    from .auth import is_presidencia  # tu implementación real
except Exception:
    def is_presidencia(user):
        return user.is_authenticated and (user.is_staff or user.is_superuser
                                          or user.groups.filter(name="PRESIDENCIA").exists())

# --------------------------------------------
# Utilidades
# --------------------------------------------
def _es_periodo_actual(anio: int, mes: int) -> bool:
    hoy = date.today()
    return (int(anio), int(mes)) == (hoy.year, hoy.month)

def _periodo_str(anio: int, mes: int) -> str:
    return f"{int(anio):04d}-{int(mes):02d}"

# --------------------------------------------
# Panel del período
# --------------------------------------------
@login_required(login_url="login")
@user_passes_test(is_presidencia)
def periodo_panel(request):
    # Período seleccionado (o actual si no hubiera)
    anio, mes, periodo_str = get_periodo_from_session(request)
    mes = int(mes)
    PERIODO_MES_STR = f"{mes:02d}"

    # Estados declarados en el modelo
    S_ABIERTA     = getattr(LiquidacionPeriodo, "ESTADO_ABIERTA",    "ABIERTA")
    S_CERRADA     = getattr(LiquidacionPeriodo, "ESTADO_CERRADA",    "CERRADA")
    S_CONFIRMADA  = getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA")

    # Objeto de período (si existe)
    lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
    estado = lp.estado if lp else "SIN CREAR"
    existe_liq = bool(lp)

    # Métricas
    preliqs_count   = Preliquidacion.objects.filter(año=anio, mes=mes).count()
    planillas_count = Liquidacion.objects.filter(año=anio, mes=mes).count()

    # Flags de UI
    show_crear = show_reabrir = show_cerrar = show_confirmar = False
    show_regenerar = show_ver_liq = False
    block_reason = None

    es_actual = _es_periodo_actual(anio, mes)

    if not existe_liq:
        # Mostrar “Abrir período”. La vista validar á que sea el actual.
        show_crear = True
    else:
        if estado == S_ABIERTA:
            show_regenerar = True
            show_cerrar    = True
        elif estado == S_CERRADA:
            show_confirmar = True
            show_reabrir   = es_actual  # solo actual
            if not es_actual:
                block_reason = "La reapertura solo está permitida para el período en curso."
        elif estado == S_CONFIRMADA:
            show_ver_liq = planillas_count > 0
            show_reabrir = es_actual    # solo actual
            if not es_actual:
                block_reason = "La reapertura solo está permitida para el período en curso."

    ctx = {
        "PERIODO_ANIO": anio,
        "PERIODO_MES_STR": PERIODO_MES_STR,
        "PERIODO_ACTUAL": periodo_str,
        "MESES": MESES,

        "estado": estado,
        "existe_liq": existe_liq,
        "block_reason": block_reason,

        "preliqs_count": preliqs_count,
        "planillas_count": planillas_count,

        "show_crear": show_crear,
        "show_reabrir": show_reabrir,   # SOLO true en período actual
        "show_cerrar": show_cerrar,
        "show_confirmar": show_confirmar,
        "show_regenerar": show_regenerar,
        "show_ver_liq": show_ver_liq,
    }
    return render(request, "presidencia/periodo_panel.html", ctx)

# --------------------------------------------
# Abrir período (solo actual)
# --------------------------------------------
@login_required(login_url="login")
@user_passes_test(is_presidencia)
def crear_liquidacion(request):
    anio, mes, per = get_periodo_from_session(request)
    if not _es_periodo_actual(anio, mes):
        messages.error(request, "Solo se puede abrir el período actual.")
        return redirect("periodo_panel")

    # Requiere algún dato de entrada
    if not (Calificacion.objects.filter(año=anio, mes=mes).exists() or
            OficioJudicial.objects.filter(anio=anio, mes=mes).exists()):
        messages.error(request, "No hay datos cargados (Calificaciones u Oficios Judiciales).")
        return redirect("periodo_panel")

    obj, created = LiquidacionPeriodo.objects.get_or_create(
        periodo=f"{anio:04d}-{mes:02d}",
        defaults={"abierta_por": request.user}
    )
    if created:
        messages.success(request, "Período abierto (ABIERTA).")
    else:
        messages.info(request, f"El período ya existe en estado {obj.estado}.")
    return redirect("periodo_panel")

# --------------------------------------------
# Cerrar período (desde ABIERTA)
# --------------------------------------------
@login_required(login_url="login")
@user_passes_test(is_presidencia)
def cerrar_liquidacion(request):
    anio, mes, per = get_periodo_from_session(request)
    obj = LiquidacionPeriodo.objects.filter(periodo=per).first()
    if not obj:
        messages.error(request, "Primero abrí el período.")
        return redirect("periodo_panel")
    if obj.estado != LiquidacionPeriodo.ESTADO_ABIERTA:
        messages.warning(request, f"Solo se puede cerrar si está ABIERTA (actual: {obj.estado}).")
        return redirect("periodo_panel")

    obj.estado = LiquidacionPeriodo.ESTADO_CERRADA
    obj.cerrada_por = request.user
    obj.fecha_cerrada = timezone.now()
    obj.save(update_fields=["estado", "cerrada_por", "fecha_cerrada"])
    messages.success(request, "Período cerrado.")
    return redirect("periodo_panel")

# --------------------------------------------
# Reabrir período (solo el actual; incluso si CONFIRMADO)
# --------------------------------------------
@login_required(login_url="login")
@user_passes_test(is_presidencia)
def reabrir_liquidacion(request):
    """
    Reabre el período guardado en sesión SOLO si coincide con el período actual.
    Permite reabrir aunque esté CERRADO o CONFIRMADO.
    """
    anio, mes, per = get_periodo_from_session(request)

    if not _es_periodo_actual(anio, mes):
        messages.error(request, "Solo se puede reabrir el período en curso.")
        return redirect("periodo_panel")

    obj = LiquidacionPeriodo.objects.filter(periodo=per).first()
    if not obj:
        # Si no existe, lo abrimos como ABIERTA
        LiquidacionPeriodo.objects.create(
            periodo=per,
            estado=LiquidacionPeriodo.ESTADO_ABIERTA,
            abierta_por=request.user,
        )
        messages.success(request, f"Período {per} abierto.")
        return redirect("periodo_panel")

    # Poner en ABIERTA y limpiar marcas de cierre/confirmación
    obj.estado = LiquidacionPeriodo.ESTADO_ABIERTA
    obj.fecha_cerrada = None
    obj.fecha_confirmada = None
    obj.cerrada_por = None
    obj.confirmada_por = None
    obj.save(update_fields=["estado", "fecha_cerrada", "fecha_confirmada", "cerrada_por", "confirmada_por"])
    messages.success(request, f"Período {per} reabierto (solo permitido para el período actual).")
    return redirect("periodo_panel")

# --------------------------------------------
# Helpers + Confirmar período + Vista de lectura
# --------------------------------------------
from decimal import Decimal
from datetime import date
from calendar import monthrange

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import (
    Q, BooleanField, IntegerField, SmallIntegerField,
    PositiveSmallIntegerField, CharField, TextField
)
from django.shortcuts import redirect, render
from django.utils import timezone

from .utils import get_periodo_from_session
from .models import LiquidacionPeriodo, Preliquidacion, Liquidacion, Empleado

# --- quién puede entrar (usa tu helper real si lo tienes) ---
try:
    from .auth import is_presidencia  # tu implementación real
except Exception:
    def is_presidencia(user):
        return user.is_authenticated and user.is_staff


# ---- Q dinámico para "empleado activo" según tipo de campo 'estado' ----
def _q_estado_activo() -> Q:
    """
    Devuelve un Q que representa 'empleado activo' respetando el tipo de
    Empleado.estado (numérico/bool vs char) para evitar ValueError en filtros.
    """
    try:
        f = Empleado._meta.get_field("estado")
    except Exception:
        # fallback seguro: tratamos como numérico/bool
        return Q(empleado__estado=1) | Q(empleado__estado=True)

    if isinstance(f, (BooleanField, IntegerField, SmallIntegerField, PositiveSmallIntegerField)):
        return Q(empleado__estado=1) | Q(empleado__estado=True)
    elif isinstance(f, (CharField, TextField)):
        # contempla valores típicos de texto
        return Q(empleado__estado__in=["A", "ACTIVO", "1", "true", "True"])
    # fallback
    return Q(empleado__estado=1) | Q(empleado__estado=True)


def filtro_activo_en_periodo(anio: int, mes: int, estricto: bool = False) -> Q:
    """
    Activo si:
      - estado activo (_q_estado_activo), y
      - (sin fecha_salida o fecha_salida > fin del mes)  [modo normal]
    Si estricto=True: exige fecha_salida IS NULL.
    """
    anio = int(anio); mes = int(mes)
    fin = date(anio, mes, monthrange(anio, mes)[1])

    estado_q = _q_estado_activo()
    if estricto:
        salida_q = Q(empleado__fecha_salida__isnull=True)
    else:
        salida_q = Q(empleado__fecha_salida__isnull=True) | Q(empleado__fecha_salida__gt=fin)

    return estado_q & salida_q


# --------------------------------------------
# Confirmar período (desde CERRADA)
# --------------------------------------------
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    """
    Copia SOLO preliquidaciones de empleados activos estrictos y confirma.
    Marca 'conformada=True' si el campo existe. Nunca inserta basico NULL.
    """
    anio, mes, periodo_str = get_periodo_from_session(request)

    lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
    if not lp:
        messages.error(request, "No existe ese período.")
        return redirect("periodo_panel")

    S_CERRADA    = getattr(LiquidacionPeriodo, "ESTADO_CERRADA", "CERRADA")
    S_CONFIRMADA = getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA")

    if lp.estado != S_CERRADA:
        messages.warning(request, f"Para confirmar debe estar CERRADA (actual: {lp.estado}).")
        return redirect("periodo_panel")

    # Sanea preliqs con basico NULL por las dudas
    Preliquidacion.objects.filter(año=anio, mes=mes, basico__isnull=True).update(basico=Decimal("0.00"))

    base_qs = (Preliquidacion.objects
               .filter(año=anio, mes=mes)
               .select_related("empleado", "categoria", "oficina", "titulo", "nivel"))

    qs_activos = base_qs.filter(filtro_activo_en_periodo(anio, mes, estricto=True))

    total_pre   = base_qs.count()
    a_confirmar = qs_activos.count()
    omitidos    = total_pre - a_confirmar

    # Limpiamos planillas previas del período
    Liquidacion.objects.filter(año=anio, mes=mes).delete()

    def D(x, fallback="0.00"):
        try:
            return Decimal(x if x is not None else fallback)
        except Exception:
            return Decimal(fallback)

    # ¿existe el campo 'conformada'?
    HAS_CONFORMADA = any(f.name == "conformada" for f in Liquidacion._meta.get_fields())

    objs = []
    for p in qs_activos:
        data = {
            "empleado": p.empleado,
            "año": anio, "mes": mes,
            "categoria": getattr(p, "categoria", None),
            "oficina": getattr(p, "oficina", None),
            "titulo": getattr(p, "titulo", None),
            "nivel": getattr(p, "nivel", None),

            "basico": D(p.basico),                       # <- nunca NULL
            "basico_total": D(getattr(p, "basico_total", None)),
            "antiguedad": (getattr(p, "antiguedad", 0) or 0),
            "calificacion": D(getattr(p, "calificacion", None), "100"),

            "supl1": D(getattr(p, "supl1", None)),
            "supl2": D(getattr(p, "supl2", None)),
            "supl3": D(getattr(p, "supl3", None)),
            "supl4": D(getattr(p, "supl4", None)),
            "supl6": D(getattr(p, "supl6", None)),
            "supl8": D(getattr(p, "supl8", None)),
            "supl12": D(getattr(p, "supl12", None)),

            "bruto": D(getattr(p, "bruto", None)),
            "jubilacion": D(getattr(p, "jubilacion", None)),
            "obra_social": D(getattr(p, "obra_social", None)),
            "oficio_judicial": D(getattr(p, "oficio_judicial", None)),
            "liquido": D(getattr(p, "liquido", None)),

            "situacion": getattr(p, "situacion", None),
            "categoria_nombre": getattr(p, "categoria_nombre", None),
            "oficina_nombre": getattr(p, "oficina_nombre", None),
            "titulo_completo": getattr(p, "titulo_completo", None),
        }
        if HAS_CONFORMADA:
            data["conformada"] = True  # 👈 grabamos 1/True en cada fila creada
        objs.append(Liquidacion(**data))

    with transaction.atomic():
        if objs:
            Liquidacion.objects.bulk_create(objs, batch_size=500)
            # por si tu backend mapea boolean raro, reforzamos el update
            if HAS_CONFORMADA:
                Liquidacion.objects.filter(año=anio, mes=mes).update(conformada=True)

        lp.estado = S_CONFIRMADA
        lp.confirmada_por = request.user
        lp.fecha_confirmada = timezone.now()
        lp.save(update_fields=["estado", "confirmada_por", "fecha_confirmada"])

    messages.success(
        request,
        f"Período {periodo_str} confirmado. Creadas: {a_confirmar}. Omitidas por inactivos: {omitidos}."
    )
    return redirect("periodo_panel")




# ----------------------------------------------------------
# Vista de solo lectura de planillas CONFIRMADAS
# ----------------------------------------------------------
# empleados/views_liquidacion.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect


@login_required(login_url="login")
@user_passes_test(is_presidencia)
def ver_liquidacion_periodo(request):
    """Vista SOLO LECTURA de planillas confirmadas del período en sesión."""
    anio, mes, periodo_str = get_periodo_from_session(request)

    # Verificamos que el período esté confirmado
    lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
    if not lp or lp.estado != getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA"):
        messages.warning(request, f"El período {periodo_str} no está confirmado.")
        return redirect("periodo_panel")

    # Base: todas las planillas del período
    qs_base = (Liquidacion.objects
               .filter(año=anio, mes=mes)
               .select_related("empleado", "categoria", "oficina", "titulo")
               .order_by("empleado__apellido", "empleado__nombre"))

    # Preferimos 'conformada=True' si existe y hay filas; si no, usamos la base
    qs = qs_base
    try:
        Liquidacion._meta.get_field("conformada")
        qs_conf = qs_base.filter(conformada=True)
        if qs_conf.exists():
            qs = qs_conf
    except Exception:
        pass

    # Intentamos ocultar inactivos actuales (estado activo + sin fecha_salida).
    # Si el filtro deja vacío mientras hay planillas, mostramos sin filtrar (fallback).
    qs_filtrado = qs.filter(filtro_activo_en_periodo(anio, mes, estricto=True))
    if qs.exists() and not qs_filtrado.exists():
        messages.info(
            request,
            "No se pudo aplicar el filtro de 'solo activos' sin dejar la lista vacía. "
            "Se muestran todas las planillas confirmadas del período."
        )
        qs_final = qs
    else:
        qs_final = qs_filtrado

    return render(request, "presidencia/ver_liquidacion_periodo.html", {
        "PERIODO_ACTUAL": periodo_str,
        "planillas": qs_final,
        "total_planillas": qs_final.count(),
    })
