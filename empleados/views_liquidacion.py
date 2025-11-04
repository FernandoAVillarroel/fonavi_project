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
        # Mostrar “Abrir período”
        show_crear = True
    else:
        if estado == S_ABIERTA:
            show_regenerar = True
            show_cerrar    = True
        elif estado == S_CERRADA:
            show_confirmar = True
            show_reabrir   = es_actual  # solo actual (cambiá a True si querés permitir reabrir cualquier mes)
            if not es_actual:
                block_reason = "La reapertura solo está permitida para el período en curso."
        elif estado == S_CONFIRMADA:
            show_ver_liq = planillas_count > 0
            show_reabrir = es_actual
            if not es_actual:
                block_reason = "La reapertura solo está permitida para el período en curso."

    # Nombre del mes
    from calendar import month_name
    PERIODO_MES_NOMBRE = month_name[mes].capitalize()

    ctx = {
        "PERIODO_ANIO": anio,
        "PERIODO_MES": mes,                       # <- necesario para los href
        "PERIODO_MES_STR": PERIODO_MES_STR,
        "PERIODO_MES_NOMBRE": PERIODO_MES_NOMBRE, # <- para encabezado
        "PERIODO_ACTUAL": periodo_str,
        "MESES": MESES,

        "estado": estado,
        "existe_liq": existe_liq,
        "block_reason": block_reason,

        "preliqs_count": preliqs_count,
        "planillas_count": planillas_count,

        "show_crear": show_crear,
        "show_reabrir": show_reabrir,   # SOLO true en período actual (o cambialo)
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

    # Abrir SIEMPRE (sin exigir datos cargados)
    obj, created = LiquidacionPeriodo.objects.get_or_create(
        periodo=per,
        defaults={
            "estado": getattr(LiquidacionPeriodo, "ESTADO_ABIERTA", "ABIERTA"),
            "abierta_por": request.user,
            **({"fecha_creada": timezone.now()} if hasattr(LiquidacionPeriodo, "fecha_creada") else {}),
        }
    )

    if not created and obj.estado != getattr(LiquidacionPeriodo, "ESTADO_ABIERTA", "ABIERTA"):
        # Reabrir en caso de que existiera en otro estado
        obj.estado = getattr(LiquidacionPeriodo, "ESTADO_ABIERTA", "ABIERTA")
        if hasattr(obj, "fecha_cerrada"): obj.fecha_cerrada = None
        if hasattr(obj, "fecha_confirmada"): obj.fecha_confirmada = None
        if hasattr(obj, "cerrada_por"): obj.cerrada_por = None
        if hasattr(obj, "confirmada_por"): obj.confirmada_por = None
        obj.abierta_por = request.user
        campos = ["estado", "abierta_por"]
        for f in ("fecha_cerrada", "fecha_confirmada", "cerrada_por", "confirmada_por"):
            if hasattr(obj, f):
                campos.append(f)
        obj.save(update_fields=campos)
        messages.success(request, f"Período {per} abierto (reabierto).")
    else:
        messages.success(request, f"Período {per} abierto (ABIERTA).")

    # Aviso informativo si aún no hay datos de entrada
    if not (Calificacion.objects.filter(año=anio, mes=mes).exists() or
            OficioJudicial.objects.filter(anio=anio, mes=mes).exists()):
        messages.info(request, "Período abierto. Cargá Calificaciones u Oficios antes de generar preliquidaciones.")

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
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Preliquidacion, Liquidacion, LiquidacionPeriodo
from .utils import get_periodo_from_session

# Permiso
def is_presidencia(user):
    return user.is_authenticated and user.is_staff

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    """Confirma liquidaciones y redirige a la vista con paginación"""
    mes  = int(request.GET.get('mes',  date.today().month))
    año  = int(request.GET.get('año',  date.today().year))
    area = request.GET.get('area', 'PRESIDENCIA')
    tipo = request.GET.get('tipo', 'todos')
    periodo_str = f"{año:04d}-{mes:02d}"

    preqs = Preliquidacion.objects.filter(
        mes=mes, año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True
    )
    if area and area.upper() not in ('TODAS', 'PRESIDENCIA'):
        preqs = preqs.filter(categoria_nombre=area)

    with transaction.atomic():
        for pre in preqs:
            Liquidacion.objects.update_or_create(
                empleado=pre.empleado, mes=mes, año=año,
                defaults={
                    'categoria': pre.categoria,
                    'oficina': pre.oficina,
                    'titulo': pre.titulo,
                    'nivel': pre.nivel,
                    'basico': pre.basico,
                    'calificacion': pre.calificacion,
                    'antiguedad': pre.antiguedad,
                    'importe_antiguedad': pre.importe_antiguedad,
                    'importe_titulo': pre.importe_titulo,
                    'basico_total': pre.basico_total,
                    'supl1': pre.supl1,
                    'supl2': pre.supl2,
                    'supl3': pre.supl3,
                    'supl4': pre.supl4,
                    'supl6': pre.supl6,
                    'supl8': pre.supl8,
                    'supl12': pre.supl12,
                    'total_suplementos': pre.total_suplementos,
                    'bruto': pre.bruto,
                    'jubilacion': pre.jubilacion,
                    'obra_social': pre.obra_social,
                    'oficio_judicial': pre.oficio_judicial,
                    'total_descuentos': pre.total_descuentos,
                    'liquido': pre.liquido,
                    'situacion': pre.situacion,
                    'categoria_nombre': pre.categoria_nombre,
                    'oficina_nombre': pre.oficina_nombre,
                    'titulo_completo': pre.titulo_completo,
                    'conformada': True,
                }
            )

        lp, _ = LiquidacionPeriodo.objects.get_or_create(
            periodo=periodo_str,
            defaults={
                "estado": getattr(LiquidacionPeriodo, "ESTADO_ABIERTA", "ABIERTA"),
                "fecha_creada": timezone.now(),
            },
        )
        lp.estado = getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA")
        lp.fecha_confirmada = timezone.now()
        lp.confirmada_por = request.user
        lp.save(update_fields=["estado", "fecha_confirmada", "confirmada_por"])

    messages.success(request, f"✅ Liquidaciones confirmadas. Período {periodo_str} marcado como CONFIRMADO.")
    
    # REDIRECT a la vista que ya tiene paginación
    from django.shortcuts import redirect
    from django.urls import reverse
    return redirect(f"{reverse('ver_liquidacion_periodo')}?mes={mes}&año={año}&tipo={tipo}")


# ----------------------------------------------------------
# Vista de solo lectura de planillas CONFIRMADAS
# ----------------------------------------------------------
# empleados/views_liquidacion.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect
from decimal import Decimal
from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def ver_liquidacion_periodo(request):
    """Vista SOLO LECTURA de planillas confirmadas del período con PAGINACIÓN."""
    
    # Leer mes y año: PRIMERO de GET, si no hay usar sesión
    mes_get = request.GET.get('mes')
    año_get = request.GET.get('año')
    
    if mes_get and año_get:
        mes = int(mes_get)
        anio = int(año_get)
        periodo_str = f"{anio:04d}-{mes:02d}"
    else:
        anio, mes, periodo_str = get_periodo_from_session(request)
    
    tipo = request.GET.get('tipo', 'todos')

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

    # Preferimos 'conformada=True' si existe y hay filas
    qs = qs_base
    try:
        Liquidacion._meta.get_field("conformada")
        qs_conf = qs_base.filter(conformada=True)
        if qs_conf.exists():
            qs = qs_conf
    except Exception:
        pass

    # Filtro por tipo de agente
    if tipo == 'contratados':
        qs = qs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        qs = qs.filter(situacion='P')
        title = 'Permanentes'
    else:
        title = 'Todos los Empleados'

    # Intentamos ocultar inactivos actuales
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

    # Calcular totales ANTES de paginar
    totales = qs_final.aggregate(
        basico=Sum('basico'),
        importe_antiguedad=Sum('importe_antiguedad'),
        importe_titulo=Sum('importe_titulo'),
        basico_total=Sum('basico_total'),
        supl1=Sum('supl1'),
        supl2=Sum('supl2'),
        supl3=Sum('supl3'),
        supl4=Sum('supl4'),
        supl6=Sum('supl6'),
        supl8=Sum('supl8'),
        supl12=Sum('supl12'),
        total_suplementos=Sum('total_suplementos'),
        bruto=Sum('bruto'),
        jubilacion=Sum('jubilacion'),
        obra_social=Sum('obra_social'),
        oficio_judicial=Sum('oficio_judicial'),
        total_descuentos=Sum('total_descuentos'),
        liquido=Sum('liquido'),
    )
    
    # Convertir None a Decimal('0')
    for k, v in totales.items():
        if v is None:
            totales[k] = Decimal('0')

    # === PAGINACIÓN ===
    paginator = Paginator(qs_final, 20)  # 20 registros por página
    page_number = request.GET.get('page', 1)
    
    try:
        planillas_paginadas = paginator.page(page_number)
    except PageNotAnInteger:
        planillas_paginadas = paginator.page(1)
    except EmptyPage:
        planillas_paginadas = paginator.page(paginator.num_pages)
        
    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    return render(request, "presidencia/ver_liquidacion_periodo.html", {
        "PERIODO_ACTUAL": periodo_str,
        "mes_sel": mes,
        "año_sel": anio,
        "tipo": tipo,
        "title": title,
        "planillas": planillas_paginadas,
        "total_planillas": qs_final.count(),
        "totales": totales,
        "paginator": paginator,
        "page_obj": planillas_paginadas,
        "month_name": MONTH_NAMES.get(mes, str(mes)),
    })