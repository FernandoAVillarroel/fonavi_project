# empleados/views.py

from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Empleado, Calificacion, Categoria, OficioJudicial, Preliquidacion, Liquidacion
from .forms import PreliquidacionForm, LiquidacionForm



# ——————————————————————————————————————————————————————————————————————
# VISTAS CRUD DE LIQUIDACIONES
# ——————————————————————————————————————————————————————————————————————

class LiquidacionListView(LoginRequiredMixin, ListView):
    model = Liquidacion
    template_name = 'empleados/liquidacion_list.html'
    context_object_name = 'liquidaciones'
    login_url = 'login'

@login_required(login_url='login')
def crear_preliq_y_liq(request):
    if request.method == 'POST':
        pre_form = PreliquidacionForm(request.POST)
        liq_form = LiquidacionForm(request.POST)
        if pre_form.is_valid() and liq_form.is_valid():
            pre = pre_form.save()
            liq = liq_form.save(commit=False)
            liq.preliquidacion = pre
            liq.save()
            return redirect('empleados:liquidacion-list')
    else:
        pre_form = PreliquidacionForm()
        liq_form = LiquidacionForm()
    return render(request, 'empleados/combined_form.html', {
        'pre_form': pre_form,
        'liq_form': liq_form,
    })

@login_required(login_url='login')
def liq_edit(request, pk):
    liq = get_object_or_404(Liquidacion, pk=pk)
    pre = liq.preliquidacion
    if request.method == 'POST':
        pre_form = PreliquidacionForm(request.POST, instance=pre)
        liq_form = LiquidacionForm(request.POST, instance=liq)
        if pre_form.is_valid() and liq_form.is_valid():
            pre_form.save()
            liq_form.save()
            return redirect('empleados:liquidacion-list')
    else:
        pre_form = PreliquidacionForm(instance=pre)
        liq_form = LiquidacionForm(instance=liq)
    return render(request, 'empleados/combined_form.html', {
        'pre_form': pre_form,
        'liq_form': liq_form,
    })

## ——————————————————————————————————————————————————————————————————————
# VISTAS PARA EL DASHBOARD DE PRESIDENCIA
# ——————————————————————————————————————————————————————————————————————

MONTH_NAMES = {
    1: 'Enero',   2: 'Febrero',  3: 'Marzo',     4: 'Abril',
    5: 'Mayo',    6: 'Junio',    7: 'Julio',     8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

def is_presidencia(user):
    return user.is_active and user.is_superuser


from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from datetime import date
from .models import Preliquidacion, Empleado


def _periodos_con_hoy_primero():
    """
    Devuelve una lista de tuplas (mes, nombre_mes, año) ordenada desc por año/mes.
    Asegura que (mes_actual, año_actual) esté presente aunque no exista en BD.
    """
    hoy = date.today()
    mes_hoy, año_hoy = hoy.month, hoy.year

    qs = (Preliquidacion.objects
          .values('año', 'mes')
          .distinct()
          .order_by('-año', '-mes'))

    periodos = []
    ya_tiene_hoy = False
    for p in qs:
        m, a = p['mes'], p['año']
        periodos.append((m, MONTH_NAMES.get(m, str(m)), a))
        if m == mes_hoy and a == año_hoy:
            ya_tiene_hoy = True

    # Inserta el período actual al inicio si no estaba
    if not ya_tiene_hoy:
        periodos.insert(0, (mes_hoy, MONTH_NAMES.get(mes_hoy, str(mes_hoy)), año_hoy))

    return periodos


def _leer_periodo(request, periodos):
    """
    Regla:
      - Si vienen mes/año por GET y son válidos, usar esos.
      - Si no vienen, usar HOY (siempre).
    Además, valida rangos por seguridad.
    """
    hoy = date.today()
    mes_default, año_default = hoy.month, hoy.year

    try:
        mes_sel = int(request.GET.get('mes', mes_default))
        año_sel = int(request.GET.get('año', año_default))
    except (TypeError, ValueError):
        mes_sel, año_sel = mes_default, año_default

    # Validaciones mínimas
    if not (1 <= mes_sel <= 12):
        mes_sel = mes_default
    if año_sel < 2000 or año_sel > 2100:  # ajusta a tu rango permitido
        año_sel = año_default

    return mes_sel, año_sel

from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from .models import Empleado, LiquidacionPeriodo, NovedadMensual
from .utils import get_periodo_from_session, q_activo_en_periodo, MONTH_NAMES
# is_presidencia debe estar definido en tu proyecto
from django.contrib import messages

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def presidencia_dashboard(request):
    # --- Período seleccionado desde la sesión ---
    anio, mes, periodo_str = get_periodo_from_session(request)

    # --- Detectar si el período es futuro (comparando primeros de mes) ---
    hoy_1 = date.today().replace(day=1)
    periodo_1 = date(anio, mes, 1)
    es_periodo_futuro = periodo_1 > hoy_1

    # --- Estado del período (y si existe registro de LiquidacionPeriodo) ---
    lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
    estado = lp.estado if lp else 'SIN CREAR'
    periodo_definido = bool(lp)

    # --- Métricas base ---
    if es_periodo_futuro or not periodo_definido:
        # Períodos futuros o sin crear -> TODO EN CERO
        empleados_periodo = Empleado.objects.none()
        total_activos = 0
        total_inactivos = 0
        permanentes = 0
        contratados = 0
    else:
        # Períodos creados (pasados/actual) -> lógica normal
        q = q_activo_en_periodo(anio, mes, prefix="")
        empleados_periodo = Empleado.objects.filter(q).order_by('apellido', 'nombre')

        total_activos = empleados_periodo.count()
        # Inactivos = empleados que NO están activos en el período
        total_inactivos = Empleado.objects.exclude(q).count()

        # Situación laboral (sobre los activos del período)
        permanentes = empleados_periodo.filter(situacion='P').count()
        contratados = empleados_periodo.filter(situacion='C').count()

    # Total = universo (activos + inactivos)
    total_empleados = total_activos + total_inactivos

    # --- Novedades del período seleccionado ---
    novedades = NovedadMensual.objects.filter(periodo=periodo_str).order_by('-fecha', '-id')

    # Estadísticas por tipo de novedad
    stats_novedades = {code: novedades.filter(tipo=code).count()
                       for code, _ in NovedadMensual.Tipo.choices}
    tipos_novedad = [code for code, _ in NovedadMensual.Tipo.choices]

    # --- Nombre del mes para el encabezado ---
    mes_nombre = MONTH_NAMES.get(mes, str(mes)).upper()

    # Periodos para el selector (si usás ese helper)
    periodos_list = []
    try:
        from .utils import _periodos_con_hoy_primero
        periodos_list = _periodos_con_hoy_primero()
    except Exception:
        pass

    # ---------- AVISO CONTROLADO ----------
    # Muestra el mensaje una sola vez al venir del login (bandera de sesión)
    # o siempre que el período NO esté abierto.
    if request.session.pop('show_period_msg', False) or estado != 'ABIERTO':
        messages.info(request, "Seleccioná el período de trabajo: Menú de Gestión → Período.")

    return render(request, 'presidencia/dashboard.html', {
        'periodos': periodos_list,          # Si lo usas en la plantilla
        'mes_sel': mes,
        'año_sel': anio,
        'empleados': empleados_periodo,     # listado del período (o vacío)
        'total_empleados': total_empleados, # = activos + inactivos
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
        'permanentes': permanentes,
        'contratados': contratados,
        'estado': estado,
        'PERIODO_MES_NOMBRE': mes_nombre,
        'PERIODO_ANIO': anio,
        'PERIODO_ELEGIDO': True,            # si usás get_periodo_from_session
        'novedades': novedades,
        'stats_novedades': stats_novedades,
        'tipos_novedad': tipos_novedad,
    })





from datetime import date
import calendar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from .models import Categoria
from .forms import CategoriaForm


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'empleados/categoria_list.html'
    context_object_name = 'categorias'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context['mes_actual'] = hoy.month
        context['año_actual'] = hoy.year
        context['month_name'] = calendar.month_name[hoy.month].capitalize()
        context['q'] = (self.request.GET.get('q') or '').strip()
        return context

    def get_queryset(self):
        qs = (Categoria.objects
              .select_related('nivel')
              .order_by('nombre'))
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'empleados/categoria_form.html'
    success_url = reverse_lazy('empleados:categoria-list')

    def form_valid(self, form):
        form.instance.area = 'PRESIDENCIA'
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'empleados/categoria_form.html'
    success_url = reverse_lazy('empleados:categoria-list')

    def form_valid(self, form):
        form.instance.area = 'PRESIDENCIA'
        return super().form_valid(form)


# ───────────────────────────── Constantes ──────────────────────────

AREAS = [
    'TODAS',
    'PRESIDENCIA',
    'SECRET. TÉCNICA CONTABLE',
    'PLANES DE EMERGENCIA',
    'SECRETARÍA TEC. SOCIAL',
]

def is_presidencia(user):
    return user.is_active and user.is_superuser




# empleados/views.py — BLOQUE 1 (imports + helpers + listado)
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from .models import Empleado

# Helper de presidencia (usa tu auth si existe)
try:
    from .auth import is_presidencia  # pragma: no cover
except Exception:
    def is_presidencia(user):
        return user.is_authenticated and getattr(getattr(user, "perfil", None), "area", "") == "PRESIDENCIA"

# Regla IPVU por período (enero/julio) — si no está en utils, usamos fallback.
try:
    from .utils import calcular_antiguedad_ipvu  # noqa
except Exception:
    def calcular_antiguedad_ipvu(fi, anio, mes):
        if not fi:
            return 0
        base = anio - fi.year
        if mes >= 7:
            base += 1
        return max(base, 0)

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def empleado_list(request):
    """Listado de empleados SOLO del área PRESIDENCIA, con filtros básicos."""
    q          = (request.GET.get("q") or "").strip()
    sit_sel    = request.GET.get("situacion") or "Todas"
    estado_sel = request.GET.get("estado") or "1"   # 1=Activos por defecto

    qs = (Empleado.objects
          .select_related("categoria", "oficina", "titulo")
          .filter(area="PRESIDENCIA"))

    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(dni__icontains=q) |
            Q(cuil__icontains=q)
        )

    if sit_sel in ("P", "C"):
        qs = qs.filter(situacion=sit_sel)

    # 1=activos (estado=1 y sin fecha_salida); 0=inactivos; T=todos
    if estado_sel == "1":
        qs = qs.filter(estado=1, fecha_salida__isnull=True)
    elif estado_sel == "0":
        qs = qs.exclude(estado=1, fecha_salida__isnull=True)

    paginator = Paginator(qs.order_by("apellido", "nombre"), 50)
    page_obj  = paginator.get_page(request.GET.get("page"))

    situaciones = ["Todas", "P", "C"]
    estados     = [("1", "Activos"), ("0", "Inactivos"), ("T", "Todos")]
    qs_params   = f"q={q}&situacion={sit_sel}&estado={estado_sel}"

    ctx = {
        "empleados": page_obj.object_list,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
        "paginator": paginator,
        "q": q,
        "situaciones": situaciones,
        "sit_sel": sit_sel,
        "estados": estados,
        "estado_sel": estado_sel,
        "qs_params": qs_params,
        "areas": ["PRESIDENCIA"],
        "area_sel": "PRESIDENCIA",
    }
    return render(request, "empleados/empleado_list.html", ctx)

# --- Actualización masiva de antigüedad (IPVU) ---
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction

from .models import Empleado

# si ya tenés is_presidencia definido arriba, no vuelvas a declararlo
try:
    from .utils import calcular_antiguedad_ipvu
except Exception:
    calcular_antiguedad_ipvu = None


def _antig_ipvu(fecha_ingreso, anio, mes):
    if not fecha_ingreso:
        return 0
    if calcular_antiguedad_ipvu:
        return calcular_antiguedad_ipvu(fecha_ingreso, anio, mes)
    # Fallback simple por si falta el helper
    base = anio - fecha_ingreso.year
    if mes >= 7:
        base += 1
    return max(base, 0)


@login_required(login_url="login")
@user_passes_test(is_presidencia)
def antiguedad_actualizar(request):
    """Recalcula y persiste Empleado.antiguedad para el PERÍODO ACTUAL."""
    hoy = date.today()
    anio, mes = hoy.year, hoy.month

    qs = Empleado.objects.filter(area="PRESIDENCIA")
    modificados = 0

    with transaction.atomic():
        for e in qs:
            nueva = _antig_ipvu(e.fecha_ingreso, anio, mes)
            if e.antiguedad != nueva:
                e.antiguedad = nueva
                e.save(update_fields=["antiguedad"])
                modificados += 1

    messages.success(
        request,
        f"Antigüedad actualizada para {modificados} empleado(s) — período {mes:02d}/{anio}."
    )
    return redirect("empleados:empleado-list")




# empleados/views.py — BLOQUE 2 (endpoint para persistir antigüedad)
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect

from .models import Empleado

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def antiguedad_actualizar(request):
    """
    Persiste Empleado.antiguedad con la regla IPVU para el PERÍODO ACTUAL.
    La grilla puede mostrar emp.antiguedad_ipvu_actual (dinámico), pero este endpoint
    actualiza la columna para reportes/SQL.
    """
    hoy = date.today()
    anio, mes = hoy.year, hoy.month

    qs = Empleado.objects.filter(fecha_salida__isnull=True).only("pk", "fecha_ingreso", "antiguedad")
    to_update = []
    for e in qs:
        val = calcular_antiguedad_ipvu(e.fecha_ingreso, anio, mes) if e.fecha_ingreso else 0
        if e.antiguedad != val:
            to_update.append(Empleado(pk=e.pk, antiguedad=val))

    if to_update:
        Empleado.objects.bulk_update(to_update, ["antiguedad"])

    messages.success(request, f"Antigüedad actualizada para {len(to_update)} empleado(s).")
    return redirect("empleados:empleado-list")




# ───────────────────────────── Helpers ─────────────────────────────

# empleados/views.py
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import (
    Empleado, Preliquidacion, OficioJudicial, Calificacion, LiquidacionPeriodo,
)

# ——— util de antigüedad por PERÍODO (IPVU: enero +1, julio +1) ———
try:
    from .utils import calcular_antiguedad_ipvu
except Exception:
    calcular_antiguedad_ipvu = None  # fallback si no está disponible

# ---------- helpers básicos ----------
def _money(x):
    return Decimal(x or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _extrae_importe(obj):
    if not obj:
        return None
    for nombre in ("monto", "importe", "basico", "valor", "sueldo_basico", "nivel"):
        val = getattr(obj, nombre, None)
        if val is not None:
            try:
                return Decimal(val)
            except Exception:
                pass
    return None

def _nivel_desde_categoria(cat):
    if not cat:
        return None
    nb = getattr(cat, "nivel", None)
    if nb:
        return nb
    for attr in ("id_nivel", "nivel_id"):
        nivel_id = getattr(cat, attr, None)
        if nivel_id:
            try:
                nivel_id = int(nivel_id)
            except Exception:
                nivel_id = None
            if nivel_id:
                from .models import NivelBasico
                nb = (NivelBasico.objects.filter(pk=nivel_id).first()
                      or getattr(NivelBasico.objects.filter(id_nivel=nivel_id).first(), 'pk', None))
                if nb:
                    return nb
    return None

def _nivel_y_basico_de(emp):
    nv = getattr(emp, "nivel_basico", None) or getattr(emp, "nivel", None)
    if not nv and getattr(emp, "categoria", None):
        nv = _nivel_desde_categoria(emp.categoria)
    return nv, _extrae_importe(nv)

# helpers para $ y suplementos
def _q2(x: Decimal) -> Decimal:
    return Decimal(x or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _calc_sup(base: Decimal, valor, tipo) -> Decimal:
    """
    Si tipo==1 -> 'valor' es porcentaje (p.ej. 60 ó 0.60) sobre 'base'
    Si tipo==2 -> 'valor' es importe fijo en pesos
    """
    v = Decimal(valor or 0)
    t = int(tipo or 1)
    if t == 1:                   # porcentaje
        if v > 1:                # 60 -> 0.60
            v = v / Decimal("100")
        return _q2(base * v)
    # fijo en $
    return _q2(v)

# ---------- permisos (ajustá por tu proyecto) ----------
def is_presidencia(user):
    return user.is_authenticated and user.is_staff

# período desde sesión (fallback simple)
try:
    from .utils import get_periodo_from_session
except Exception:
    def get_periodo_from_session(request):
        hoy = date.today()
        anio = int(request.session.get("PERIODO_ANIO", hoy.year))
        mes  = int(request.session.get("PERIODO_MES", hoy.month))
        return anio, mes, f"{anio:04d}-{mes:02d}"






# arriba del archivo (si no están aún)
from django.db.models import Sum
from django.db.models.functions import Coalesce

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
from datetime import date

# importar helper de antigüedad
try:
    from .utils import calcular_antiguedad_ipvu
except Exception:
    calcular_antiguedad_ipvu = None

# ... tus imports ...

def _q2(valor):
    """Redondea a 2 decimales usando ROUND_HALF_UP"""
    from decimal import Decimal, ROUND_HALF_UP
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# empleados/views.py (busca donde está def _nivel_y_basico_de y pega ANTES):

def to_decimal(raw):
    """Convierte formato argentino (10.000,00) o USA (10,000.00) a Decimal"""
    if raw is None:
        return Decimal('0')
    s = str(raw).strip()
    
    # Si tiene coma, puede ser formato argentino (10.000,00) o USA (10,000.00)
    if ',' in s:
        # Si después de la coma hay 2 dígitos, es decimal argentino
        if ',' in s and len(s.split(',')[-1]) <= 2:
            # Formato argentino: 10.000,50 → quita puntos, coma→punto
            s = s.replace('.', '').replace(',', '.')
        else:
            # Formato USA: 10,000.50 → quita comas
            s = s.replace(',', '')
    # Si solo tiene punto y 2 decimales, ya está en formato USA
    # No hacer nada, ya está correcto
    
    try:
        return Decimal(s)
    except Exception:
        return Decimal('0')


def _nivel_y_basico_de(emp):
    """
    Determina qué nivel (FK) y básico usar para un empleado.
    Retorna: (nivel_fk, basico_decimal)
    """
    from decimal import Decimal
    # Ya NO importes from .utils import to_decimal
    
    if emp.categoria and emp.categoria.nivel:
        return (emp.categoria.nivel, Decimal(str(emp.categoria.nivel.monto)))
    
    if emp.categoria and emp.categoria.basico_manual:
        return (None, to_decimal(emp.categoria.basico_manual))
    
    if hasattr(emp, 'nivel_basico') and emp.nivel_basico:
        return (emp.nivel_basico, Decimal(str(emp.nivel_basico.monto)))
    
    return (None, Decimal("0.00"))


@login_required(login_url="login")
@user_passes_test(is_presidencia)
def generar_preliquidacion(request):
    """
    Regenera preliquidaciones para el período seleccionado, si existe
    LiquidacionPeriodo y éste NO esté CERRADO ni CONFIRMADO.
    Solo genera para empleados activos estrictos: estado=1 y fecha_salida IS NULL.
    """
    anio_ses, mes_ses, _ = get_periodo_from_session(request)
    mes = int(request.GET.get("mes", mes_ses))
    año = int(request.GET.get("año", anio_ses))
    periodo_str = f"{año:04d}-{mes:02d}"

    # Debe existir período y estar ABIERTA (o reabierta)
    lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
    if lp is None:
        messages.error(request, f"No existe un período abierto para {periodo_str}. Ábrelo desde el Panel del Período.")
        return redirect("periodo_panel")
    if lp.estado == getattr(LiquidacionPeriodo, "ESTADO_CERRADA", "CERRADA"):
        messages.error(request, f"El período {periodo_str} está CERRADO. Reábrelo para poder regenerar.")
        return redirect("periodo_panel")
    if lp.estado == getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA"):
        messages.error(request, f"El período {periodo_str} está CONFIRMADO (solo lectura).")
        return redirect("periodo_panel")

    # Si no hay calificaciones, crearlas automáticamente al 100%
    hay_calif = Calificacion.objects.filter(año=año, mes=mes).exists()
    if not hay_calif:
        empleados_activos = Empleado.objects.filter(
            fecha_salida__isnull=True,
            estado=1
        )
        
        creadas = 0
        for emp in empleados_activos:
            Calificacion.objects.create(
                empleado=emp,
                año=año,
                mes=mes,
                calificacion=Decimal("100.00")
            )
            creadas += 1
        
        messages.info(request, f"Se crearon {creadas} calificaciones al 100% para {periodo_str}.")
        hay_calif = True

    hay_oj = OficioJudicial.objects.filter(anio=año, mes=mes).exists()
    
    if not (hay_calif or hay_oj):
        messages.error(request, "No hay datos cargados (Calificaciones u Oficios Judiciales) para este período.")
        return redirect("periodo_panel")

    # Empleados activos estrictos
    empleados = (
        Empleado.objects
        .filter(fecha_salida__isnull=True)
        .filter(Q(estado=1) | Q(estado=True))
        .select_related("categoria", "oficina", "titulo", "nivel_basico")
    )

    # Limpiar preliqs del período
    Preliquidacion.objects.filter(mes=mes, año=año).delete()

    sin_basico = []

    def _d(x):
        return Decimal(x or 0)

    with transaction.atomic():
        for emp in empleados:
            nivel_fk, basico = _nivel_y_basico_de(emp)

            obj, _ = Preliquidacion.objects.update_or_create(
                empleado=emp, año=año, mes=mes,
                defaults={
                    "categoria": emp.categoria,
                    "oficina": emp.oficina,
                    "titulo": getattr(emp, "titulo", None),
                    "nivel": nivel_fk,
                    "basico": basico if basico is not None else Decimal("0.00"),
                    "situacion": getattr(emp, "situacion", None),
                    "categoria_nombre": getattr(emp.categoria, "nombre", None),
                    "oficina_nombre": getattr(emp.oficina, "nombre", None),
                    "titulo_completo": getattr(getattr(emp, "titulo", None), "titulo_completo", None),
                }
            )

            calif = (Calificacion.objects
                     .filter(empleado=emp, año=año, mes=mes)
                     .values_list("calificacion", flat=True)
                     .first())
            obj.calificacion = calif if calif is not None else Decimal("100")

            if calcular_antiguedad_ipvu:
                obj.antiguedad = calcular_antiguedad_ipvu(emp.fecha_ingreso, año, mes)
            else:
                if emp.fecha_ingreso:
                    ref = date(int(año), int(mes), 1)
                    anios = ref.year - emp.fecha_ingreso.year
                    if ref.month >= 7:
                        anios += 1
                    obj.antiguedad = max(anios, 0)
                else:
                    obj.antiguedad = 0

            obj.save()

            bruto_prev = _d(obj.bruto)
            j_prev = _d(obj.jubilacion)
            os_prev = _d(obj.obra_social)
            j_pct = (j_prev / bruto_prev) if bruto_prev else Decimal("0")
            os_pct = (os_prev / bruto_prev) if bruto_prev else Decimal("0")

            cat = emp.categoria
            
            # ========== LÓGICA CONDICIONAL: MONTO MANUAL vs NIVEL ==========
            tiene_basico_manual = cat and getattr(cat, "basico_manual", None)
            
            if tiene_basico_manual:
                # Para empleados con MONTO MANUAL: recalcular todo desde la categoría
                importe_titulo = _d(getattr(obj, "importe_titulo", 0))
                importe_antiguedad = _d(getattr(obj, "importe_antiguedad", 0))
                basico_total = _q2(basico + importe_titulo + importe_antiguedad)
                
                s = {}
                updates = {}
                
                for n in (1, 2, 3, 4, 6, 8, 12):
                    sup_valor = to_decimal(getattr(cat, f"sup{n}", 0))
                    tipo = int(getattr(cat, f"tipo_sup{n}", 1))
                    
                    if tipo == 1:  # Porcentaje sobre BASICO_TOTAL
                        if sup_valor > 1:  # 30 → 0.30
                            sup_valor = sup_valor / Decimal("100")
                        s[n] = _q2(basico_total * sup_valor)
                    else:  # tipo == 2, monto fijo
                        s[n] = _q2(sup_valor)
                    
                    updates[f"supl{n}"] = s[n]
            
            else:
                # Para empleados con NIVEL: lógica original (funciona bien)
                basico_total = _d(getattr(obj, "basico_total", 0))
                
                s = {
                    1: _d(getattr(obj, "supl1", 0)),
                    2: _d(getattr(obj, "supl2", 0)),
                    3: _d(getattr(obj, "supl3", 0)),
                    4: _d(getattr(obj, "supl4", 0)),
                    6: _d(getattr(obj, "supl6", 0)),
                    8: _d(getattr(obj, "supl8", 0)),
                    12: _d(getattr(obj, "supl12", 0)),
                }
                updates = {}

                for n in (4, 6, 8, 12):
                    try:
                        tipo = int(getattr(cat, f"tipo_sup{n}") or 1)
                    except Exception:
                        tipo = 1
                    if tipo == 2:
                        fijo = _q2(_d(getattr(cat, f"sup{n}") or 0))
                        if fijo != s[n]:
                            s[n] = fijo
                            updates[f"supl{n}"] = fijo

            # ========== FIN LÓGICA CONDICIONAL ==========

            suma_suples = _q2(s[1] + s[2] + s[3] + s[4] + s[6] + s[8] + s[12])
            bruto = _q2(basico_total + suma_suples)
            j = _q2(bruto * j_pct)
            os = _q2(bruto * os_pct)

            agg_oj = (OficioJudicial.objects
                      .filter(empleado=emp, anio=año, mes=mes)
                      .aggregate(
                          monto_total=Coalesce(Sum('monto_descontar'), Decimal('0.00')),
                          porc_total=Coalesce(Sum('porcentaje_descontar'), Decimal('0.00')),
                      ))
            oj_monto = _q2(_d(agg_oj['monto_total']))
            oj_pct = _d(agg_oj['porc_total']) / Decimal("100")
            ojd = _q2(oj_monto + (bruto * oj_pct))

            liquido = _q2(bruto - (j + os + ojd))

            updates.update({
                "bruto": bruto,
                "jubilacion": j,
                "obra_social": os,
                "oficio_judicial": ojd,
                "liquido": liquido,
            })

            Preliquidacion.objects.filter(pk=obj.pk).update(**updates)

            if not basico or basico <= 0:
                sin_basico.append(emp.pk)

    if sin_basico:
        messages.warning(
            request,
            f"Empleados sin básico resuelto en {mes:02d}/{año}: {len(sin_basico)} (IDs: {', '.join(map(str, sin_basico))})"
        )

    messages.success(request, f"Preliquidaciones regeneradas para {periodo_str}.")
    return redirect(f"{reverse('empleados:preliquidacion_overview')}?mes={mes}&año={año}&area=TODAS")


# --- Listado de Preliquidaciones (overview) CON PAGINACIÓN ---
from django.shortcuts import render  # si ya está importado, dejalo
from django.db.models import Q       # si ya está importado, dejalo
from datetime import date
import calendar
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Value, IntegerField, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def preliquidacion_overview(request):
    """
    Muestra TODAS las preliquidaciones del período con PAGINACIÓN.
    Filtros: área (por Empleado.area) y búsqueda por DNI/CUIL/Nombre/Apellido.
    """
    mes  = int(request.GET.get("mes",  date.today().month))
    año  = int(request.GET.get("año",  date.today().year))
    area = request.GET.get("area", "TODAS")
    q    = (request.GET.get("q") or "").strip()

    qs = (
        Preliquidacion.objects
        .filter(
            mes=mes, año=año,
            empleado__estado=1,
            empleado__fecha_salida__isnull=True
        )
        .select_related("empleado", "categoria", "oficina", "titulo", "nivel")
        .order_by("empleado__apellido", "empleado__nombre")
    )

    # Filtro por área del empleado (no por nombre de categoría)
    if area and area != "TODAS":
        qs = qs.filter(empleado__area=area)

    # Búsqueda libre por DNI/CUIL/Nombre/Apellido (soporta "Nombre Apellido")
    if q:
        partes = q.split()
        cond = (
            Q(empleado__cuil__icontains=q) |
            Q(empleado__dni__icontains=q)  |
            Q(empleado__nombre__icontains=q) |
            Q(empleado__apellido__icontains=q)
        )
        if len(partes) >= 2:
            cond |= (
                Q(empleado__nombre__icontains=partes[0]) &
                Q(empleado__apellido__icontains=partes[1])
            )
        qs = qs.filter(cond)

    # Lista de áreas disponibles (de empleados activos)
    try:
        areas = ["TODAS"] + sorted([
            a for a in (Empleado.objects
                        .filter(estado=1, fecha_salida__isnull=True)
                        .values_list("area", flat=True)
                        .distinct())
            if a
        ])
    except Exception:
        areas = ["TODAS"]

    month_name = MONTH_NAMES.get(mes, str(mes))

    sort_key = (request.GET.get("sort") or "").strip()
    sort_dir = request.GET.get("dir", "asc").lower()
    allowed_sort = {
        "cuil": "empleado__cuil",
        "nivel": "nivel__id_nivel",
        "basico": "basico",
        "calificacion": "calificacion",
        "antiguedad": "antiguedad",
        "imp_antiguedad": "importe_antiguedad",
        "imp_titulo": "importe_titulo",
        "basico_total": "basico_total",
        "sup1": "supl1",
        "sup2": "supl2",
        "sup3": "supl3",
        "sup4": "supl4",
        "sup6": "supl6",
        "sup8": "supl8",
        "sup12": "supl12",
        "total_suplementos": "total_suplementos",
        "bruto": "bruto",
        "jubilacion": "jubilacion",
        "obra_social": "obra_social",
        "oficio_judicial": "oficio_judicial",
        "total_descuentos": "total_descuentos",
        "liquido": "liquido",
        # strings
        "oficina": "oficina_nombre",
        "categoria": "categoria_nombre",
        "titulo": "titulo_completo",
    }
    if sort_key == "empleado":
        if sort_dir == "desc":
            qs = qs.order_by("-empleado__apellido", "-empleado__nombre")
        else:
            qs = qs.order_by("empleado__apellido", "empleado__nombre")
    elif sort_key in allowed_sort:
        field = allowed_sort[sort_key]
        numeric_keys_int = {"nivel"}
        numeric_keys_dec = {
            "basico", "calificacion", "antiguedad",
            "imp_antiguedad", "imp_titulo", "basico_total",
            "sup1", "sup2", "sup3", "sup4", "sup6", "sup8", "sup12",
            "total_suplementos", "bruto", "jubilacion", "obra_social",
            "oficio_judicial", "total_descuentos", "liquido",
        }
        if sort_key in numeric_keys_int:
            qs = qs.annotate(_sv=Coalesce(F(field), Value(0), output_field=IntegerField()))
            qs = qs.order_by("-_sv" if sort_dir == "desc" else "_sv")
        elif sort_key in numeric_keys_dec:
            qs = qs.annotate(_sv=Coalesce(F(field), Value(Decimal("0.00")), output_field=DecimalField(max_digits=20, decimal_places=2)))
            qs = qs.order_by("-_sv" if sort_dir == "desc" else "_sv")
        else:
            qs = qs.order_by(f"-{field}" if sort_dir == "desc" else field)

    # === PAGINACIÓN ===
    paginator = Paginator(qs, 15)  # 15 registros por página
    page_number = request.GET.get('page', 1)
    
    try:
        preliquidaciones_paginadas = paginator.page(page_number)
    except PageNotAnInteger:
        preliquidaciones_paginadas = paginator.page(1)
    except EmptyPage:
        preliquidaciones_paginadas = paginator.page(paginator.num_pages)

    ctx = {
        "preliquidaciones": preliquidaciones_paginadas,  # Ahora paginado
        "areas"           : areas,
        "mes_sel"         : mes,
        "año_sel"         : año,
        "area_sel"        : area,
        "q"               : q,
        "month_name"      : month_name,
        "paginator"       : paginator,
        "page_obj"        : preliquidaciones_paginadas,
        "total_registros" : qs.count(),
    }
    return render(request, "presidencia/preliquidacion_overview.html", ctx)

# ——————————————————————————————————————————————————————————————————————
# Exportar Liquidaciones a PDF
# ——————————————————————————————————————————————————————————————————————

def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        return result
    path = uri.replace(settings.STATIC_URL, "")
    return os.path.join(settings.STATIC_ROOT, path)


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def exportar_liquidaciones_pdf(request):
    mes   = int(request.GET.get('mes',  date.today().month))
    año   = int(request.GET.get('año',  date.today().year))
    area  = request.GET.get('area', 'PRESIDENCIA')
    tipo  = request.GET.get('tipo', 'todos')

    # MISMO FILTRO QUE EN EL FRONT
    liqs = Liquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True,
    )
    if area and area.upper() != 'PRESIDENCIA':
        liqs = liqs.filter(categoria_nombre=area)

    if tipo == 'contratados':
        liqs = liqs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        liqs = liqs.filter(situacion='P')
        title = 'Permanentes'
    else:
        title = 'Todos los Empleados'

    tot = {
        'count': liqs.count(),
        'bruto': liqs.aggregate(Sum('bruto'))['bruto__sum'] or Decimal('0'),
        'liquido': liqs.aggregate(Sum('liquido'))['liquido__sum'] or Decimal('0'),
    }

    template = get_template('presidencia/liquidacion_pdf.html')
    html     = template.render({
        'mes_sel'   : mes,
        'año_sel'   : año,
        'month_name': MONTH_NAMES[mes],
        'area_sel'  : area,
        'tipo'      : tipo,
        'liqs'      : liqs.order_by('empleado__apellido','empleado__nombre'),
        'tot'       : tot,
        'title'     : title,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="liquidaciones_{mes}_{año}_{tipo}.pdf"'
    )
    pisa_status = pisa.CreatePDF(
        src=BytesIO(html.encode('utf-8')),
        dest=response,
        link_callback=link_callback,
    )
    if pisa_status.err:
        return HttpResponse("Hubo un error generando el PDF", status=500)
    return response



# ——————————————————————————————————————————————————————————————————————
# empleados/views.py — bloque para recalcular antigüedad en Empleado

# empleados/views.py — actualización de antigüedad

from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect

from .models import Empleado
from .utils import get_periodo_from_session, calcular_antiguedad_ipvu

# Permiso
try:
    from .auth import is_presidencia
except Exception:
    def is_presidencia(user):
        return user.is_authenticated and user.is_staff


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def actualizar_antiguedad(request):
    """
    Recalcula y guarda Empleado.antiguedad según REGLA IPVU:
    - Ingreso ene-jun: suma 1 año el 1º enero siguiente
    - Ingreso jul-dic: NO suma año el 1º enero siguiente
    """
    # Período de referencia
    anio, mes, periodo_str = get_periodo_from_session(request)

    messages.info(
        request,
        f"Recalculando antigüedades con regla IPVU para {periodo_str} "
        "(ingreso ene-jun: +1 en enero; jul-dic: espera siguiente enero)."
    )

    empleados = Empleado.objects.filter(estado=1, fecha_salida__isnull=True)
    actualizados = 0
    cambios_realizados = 0

    for emp in empleados:
        if not emp.fecha_ingreso:
            continue

        # Calcular antigüedad según regla IPVU
        nuevo_valor = calcular_antiguedad_ipvu(emp.fecha_ingreso, anio, mes)

        # Solo actualizar si cambió
        if nuevo_valor != (emp.antiguedad or 0):
            emp.antiguedad = nuevo_valor
            emp.save(update_fields=['antiguedad'])
            cambios_realizados += 1

        actualizados += 1

    messages.success(
        request,
        f"✓ Antigüedades recalculadas: {actualizados} empleados procesados, "
        f"{cambios_realizados} actualizaciones realizadas."
    )
    return redirect('empleados:empleado-list')



# VISTA DE PRELIQUIDACION OVERVIEW (CORREGIDA)

# empleados/views.py

import os
from io import BytesIO
from datetime import date
from decimal import Decimal

from django.shortcuts            import render
from django.http                 import HttpResponse
from django.conf                 import settings
from django.contrib.staticfiles  import finders
from django.template.loader      import get_template
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db                   import transaction
from django.db.models            import Sum
from xhtml2pdf                   import pisa

from .models    import Preliquidacion, Liquidacion


def link_callback(uri, rel):
    """
    Convierte URIs de <link> o <img> a rutas absolutas en disco para xhtml2pdf.
    """
    # Primero prueba en staticfiles
    result = finders.find(uri)
    if result:
        return result
    # Si no, asume STATIC_ROOT
    path = uri.replace(settings.STATIC_URL, "")
    return os.path.join(settings.STATIC_ROOT, path)


def _get_queryset_and_totals(mes, año, area):
    """
    Helper que sincroniza Preliquidacion→Liquidacion, devuelve:
    (base_qs, qs_contratados, qs_permanentes, tot_all, tot_cont, tot_perm)
    """
    # 1) sincronizar Liquidaciones
    preqs = Preliquidacion.objects.filter(mes=mes, año=año)
    if area:
        preqs = preqs.filter(categoria__nombre=area)
    with transaction.atomic():
        for pre in preqs:
            Liquidacion.objects.update_or_create(
                empleado=pre.empleado,
                mes=mes,
                año=año,
                defaults={
                    # TODOS tus campos de Preliquidacion → Liquidacion
                    'categoria':          pre.categoria,
                    'oficina':            pre.oficina,
                    'titulo':             pre.titulo,
                    'nivel':              pre.nivel,
                    'basico':             pre.basico,
                    'calificacion':       pre.calificacion,
                    'antiguedad':         pre.antiguedad,
                    'importe_titulo':     pre.importe_titulo,
                    'importe_antiguedad': pre.importe_antiguedad,
                    'basico_total':       pre.basico_total,
                    'supl1':              pre.supl1,
                    'supl2':              pre.supl2,
                    'supl3':              pre.supl3,
                    'supl4':              pre.supl4,
                    'supl6':              pre.supl6,
                    'supl8':              pre.supl8,
                    'supl12':             pre.supl12,
                    'total_suplementos':  pre.total_suplementos,
                    'bruto':              pre.bruto,
                    'jubilacion':         pre.jubilacion,
                    'obra_social':        pre.obra_social,
                    'oficio_judicial':    pre.oficio_judicial,
                    'total_descuentos':   pre.total_descuentos,
                    'liquido':            pre.liquido,
                    'situacion':          pre.situacion,
                    'categoria_nombre':   pre.categoria_nombre,
                    'oficina_nombre':     pre.oficina_nombre,
                    'titulo_completo':    pre.titulo_completo,
                }
            )

    # 2) QS base y sub‑queries
    base_qs       = Liquidacion.objects.filter(
                        mes=mes,
                        año=año,
                        empleado__estado=1,
                        empleado__fecha_salida__isnull=True
                    )
    if area:
        base_qs = base_qs.filter(categoria_nombre=area)
    qs_contratados = base_qs.filter(situacion='C')
    qs_permanentes = base_qs.filter(situacion='P')
    base_qs.update(conformada=True)

    # 3) Totales helper
    def totals(qs):
        agg = qs.aggregate(bruto=Sum('bruto'), liquido=Sum('liquido'))
        return {
            'count':   qs.count(),
            'bruto':   agg['bruto']   or Decimal('0'),
            'liquido': agg['liquido'] or Decimal('0'),
        }

    tot_all  = totals(base_qs)
    tot_cont = totals(qs_contratados)
    tot_perm = totals(qs_permanentes)

    return base_qs, qs_contratados, qs_permanentes, tot_all, tot_cont, tot_perm


# Asegurate de tener estos imports arriba del archivo:
# from decimal import Decimal
# from django.db import transaction
# from django.db.models import Sum
# from django.utils import timezone


# periodo/views.py
from datetime import date
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

def is_presidencia(user):
    return user.is_authenticated and user.is_staff

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def periodo_ver(request):
    mes  = int(request.GET.get('mes',  date.today().month))
    año  = int(request.GET.get('año',  date.today().year))
    tipo = request.GET.get('tipo', 'todos')
    url = f"{reverse('empleados:planillas_confirmadas')}?mes={mes}&año={año}&tipo={tipo}"
    return redirect(url)


# ——————————————————————————————————————————————————————————————————————
# CRUD DE EMPLEADOS, CALIFICACIONES, CATEGORIAS, OFICIOS
# ——————————————————————————————————————————————————————————————————————

# empleados/views.py
from django.views.generic import ListView
from django.db.models import Q
from .models import Empleado, Categoria

class EmpleadoListView(ListView):
    model = Empleado
    template_name = "empleados/empleados_list.html"
    context_object_name = "empleados"
    paginate_by = 20

    def get_queryset(self):
        qs = (Empleado.objects
              .select_related("categoria", "oficina")
              .order_by("apellido", "nombre"))

        q          = (self.request.GET.get("q") or "").strip()
        area       = self.request.GET.get("area", "TODAS")
        situacion  = self.request.GET.get("situacion", "TODAS")
        estado     = self.request.GET.get("estado", "activos")

        if q:
            base = (Q(dni__icontains=q) | Q(cuil__icontains=q) |
                    Q(nombre__icontains=q) | Q(apellido__icontains=q))
            partes = [p for p in q.split() if p]
            if len(partes) >= 2:
                n1, n2 = partes[0], partes[1]
                base |= (
                    (Q(nombre__icontains=n1) & Q(apellido__icontains=n2)) |
                    (Q(nombre__icontains=n2) & Q(apellido__icontains=n1))
                )
            qs = qs.filter(base)

        if area and area != "TODAS":
            qs = qs.filter(categoria__area=area)

        if situacion in ("P", "C"):
            qs = qs.filter(situacion=situacion)

        # FILTROS DE ESTADO CORREGIDOS
        if estado == "activos":
            qs = qs.filter(estado=1)  # Solo activos (estado=1)
        elif estado == "inactivos":
            qs = qs.filter(estado=0)  # Solo inactivos (estado=0)
        elif estado == "retencion":
            qs = qs.filter(estado=2)  # Solo retención (estado=2)
        # 'todos' -> sin filtro

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["areas"]        = ["TODAS"] + [a for a, _ in Categoria.AREAS]
        ctx["situaciones"]  = ["TODAS", "P", "C"]
        # AGREGADA LA OPCIÓN DE RETENCIÓN
        ctx["estados"]      = [
            ("activos", "Activos"),
            ("inactivos", "Inactivos"),
            ("retencion", "Retención de Cargo"),
            ("todos", "Todos")
        ]
        ctx["q"]          = (self.request.GET.get("q") or "").strip()
        ctx["area_sel"]   = self.request.GET.get("area", "TODAS")
        ctx["sit_sel"]    = self.request.GET.get("situacion", "TODAS")
        ctx["estado_sel"] = self.request.GET.get("estado", "activos")

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_params"] = params.urlencode()
        return ctx


    
# empleados/views.py (añade estos imports arriba)
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

# ...ya tienes login_required e is_presidencia importados

@login_required(login_url='login')
@user_passes_test(is_presidencia)
@require_POST
def empleado_toggle_estado(request, pk):
    """
    Alterna el campo 'estado' (1 activo / 0 inactivo) de un empleado y
    devuelve JSON para actualizar la UI sin recargar.
    """
    emp = get_object_or_404(Empleado, pk=pk)

    # Aceptamos solo POST (por seguridad)
    try:
        emp.estado = 0 if int(emp.estado or 0) == 1 else 1
    except Exception:
        return HttpResponseBadRequest("Estado inválido")

    emp.save(update_fields=["estado"])

    return JsonResponse({
        "ok": True,
        "id": emp.pk,
        "estado": int(emp.estado),                # 1 ó 0
        "estado_label": "ACTIVO" if emp.estado == 1 else "INACTIVO",
    })



# empleados/views.py (fragmento)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Empleado, Categoria
from .forms import EmpleadoForm

class EmpleadoCreateView(LoginRequiredMixin, CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('empleados:empleado-list')
    login_url = 'login'

class EmpleadoUpdateView(LoginRequiredMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('empleados:empleado-list')
    login_url = 'login'

class EmpleadoDeleteView(LoginRequiredMixin, DeleteView):
    model = Empleado
    template_name = 'empleados/empleado_confirm_delete.html'
    success_url = reverse_lazy('empleados:empleado-list')
    login_url = 'login'



# --- CALIFICACIONES LIST ---
import re
import calendar
from datetime import date
from calendar import monthrange

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Q, OuterRef, Subquery, Value,
    IntegerField as ModelIntegerField,  # alias para output_field
    BooleanField, SmallIntegerField, PositiveSmallIntegerField,
    CharField, TextField,
)
from django.db.models.functions import Coalesce
from django.views.generic import ListView

from .models import Empleado, Calificacion, Liquidacion, LiquidacionPeriodo, Oficina
from .utils import get_periodo_from_session

# Import perezoso (evita NameError y circularidades)
try:
    from .forms import CalificacionForm  # debe existir en forms.py
except Exception:
    CalificacionForm = None


class CalificacionListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'empleados/calificacion_list.html'
    context_object_name = 'empleados'
    paginate_by = 20
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
    

    # ---- helper interno: "empleado activo en período" ----
    def _q_empleado_activo_periodo(self, anio: int, mes: int, estricto: bool = False) -> Q:
        anio = int(anio); mes = int(mes)
        fin = date(anio, mes, monthrange(anio, mes)[1])

        # detectar tipo del campo estado
        try:
            f = Empleado._meta.get_field("estado")
        except Exception:
            f = None

        if f is None or isinstance(f, (BooleanField, ModelIntegerField, SmallIntegerField, PositiveSmallIntegerField)):
            q_estado = Q(estado=1) | Q(estado=True)
        elif isinstance(f, (CharField, TextField)):
            q_estado = Q(estado__in=["A", "ACTIVO", "1", "true", "True"])
        else:
            q_estado = Q(estado=1) | Q(estado=True)

        if estricto:
            q_salida = Q(fecha_salida__isnull=True)
        else:
            q_salida = Q(fecha_salida__isnull=True) | Q(fecha_salida__gt=fin)

        return q_estado & q_salida

    def get_queryset(self):
        anio, mes, periodo_str = get_periodo_from_session(self.request)
        hoy = date.today()
        es_actual = (anio == hoy.year and mes == hoy.month)
        es_futuro = (anio, mes) > (hoy.year, hoy.month)

        # estado del período
        periodo_confirmado = False
        periodo_abierto = False
        try:
            lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
            if lp:
                if hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA') and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA:
                    periodo_confirmado = True
                elif hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA') and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA:
                    periodo_abierto = True
                elif hasattr(LiquidacionPeriodo, 'ESTADO_CERRADA') and lp.estado == LiquidacionPeriodo.ESTADO_CERRADA:
                    periodo_abierto = False
                else:
                    periodo_abierto = not periodo_confirmado
        except Exception:
            periodo_confirmado = False
            periodo_abierto = True

        self._allow_edit = periodo_abierto and not periodo_confirmado
        self._periodo_confirmado = periodo_confirmado
        self._periodo_abierto = periodo_abierto
        self._es_periodo_actual = es_actual

        oficina_id = (self.request.GET.get('oficina') or '').strip()
        q = (self.request.GET.get('q') or '').strip()

        # Períodos futuros → nada y aviso
        if es_futuro:
            messages.info(self.request, "No se cargaron datos para períodos futuros.")
            return Empleado.objects.none()

        # 1) Empleados ACTIVOS en el PERÍODO
        qs = Empleado.objects.filter(self._q_empleado_activo_periodo(anio, mes, estricto=False))

        # 2) Filtro por oficina (acepta id numérico o texto parcial del nombre)
        if oficina_id and oficina_id.upper() != 'TODAS':
            try:
                oficina_pk = int(oficina_id)
                qs = qs.filter(oficina_id=oficina_pk)
            except ValueError:
                qs = qs.filter(oficina__nombre__icontains=oficina_id)

        # 3) Empleados con calificación cargada en el PERÍODO
        empleados_con_calif = Calificacion.objects.filter(mes=mes, año=anio).values_list('empleado_id', flat=True)

        # 4) Auto-generar calificaciones solo en períodos ABIERTOs
        if periodo_abierto and not periodo_confirmado:
            empleados_no_nuevos = qs.exclude(
                fecha_ingreso__year=anio,
                fecha_ingreso__month=mes
            )
            sin_calif = empleados_no_nuevos.exclude(pk__in=empleados_con_calif)

            calificaciones_a_crear = [
                Calificacion(empleado=emp, mes=mes, año=anio, calificacion=100)
                for emp in sin_calif
            ]
            if calificaciones_a_crear:
                Calificacion.objects.bulk_create(calificaciones_a_crear, ignore_conflicts=True)

            empleados_con_calif = Calificacion.objects.filter(mes=mes, año=anio).values_list('empleado_id', flat=True)

        # 5) Mostrar SOLO empleados con calificación
        qs = qs.filter(pk__in=empleados_con_calif)

        # 6) Si el período está CONFIRMADO, solo los que tienen liquidación
        if periodo_confirmado:
            liq_sub = (Liquidacion.objects
                       .filter(empleado=OuterRef('pk'), año=anio, mes=mes)
                       .values('pk')[:1])
            qs = qs.annotate(
                tiene_liq=Subquery(liq_sub, output_field=ModelIntegerField())
            ).filter(tiene_liq__isnull=False)

        # 7) Anotaciones (calificación actual y pk de calificación)
        calificacion_subq = (Calificacion.objects
                             .filter(empleado=OuterRef('pk'), mes=mes, año=anio)
                             .values('calificacion')[:1])

        cal_pk_subq = (Calificacion.objects
                       .filter(empleado=OuterRef('pk'), mes=mes, año=anio)
                       .values('pk')[:1])

        qs = qs.annotate(
            calificacion_actual=Coalesce(
                Subquery(calificacion_subq, output_field=ModelIntegerField()),
                Value(100),
                output_field=ModelIntegerField()
            ),
            cal_pk=Subquery(cal_pk_subq, output_field=ModelIntegerField()),
        )

        # 8) Búsqueda por nombre/apellido en ambos órdenes + CUIL/DNI
        if q:
            tokens = [t for t in re.split(r"\s+", q) if t]

            # Base: coincide por CUIL o DNI (parcial o completo)
            q_busqueda = Q(cuil__icontains=q) | Q(dni__icontains=q)

            if len(tokens) == 1:
                t = tokens[0]
                q_busqueda |= Q(nombre__icontains=t) | Q(apellido__icontains=t)
            elif len(tokens) >= 2:
                a, b = tokens[0], tokens[1]
                # nombre apellido
                orden_1 = Q(nombre__icontains=a) & Q(apellido__icontains=b)
                # apellido nombre
                orden_2 = Q(nombre__icontains=b) & Q(apellido__icontains=a)
                q_busqueda |= (orden_1 | orden_2)

                # match flexible: TODAS las palabras deben aparecer en nombre o apellido
                q_all = Q()
                for t in tokens:
                    q_all &= (Q(nombre__icontains=t) | Q(apellido__icontains=t))
                q_busqueda |= q_all

            qs = qs.filter(q_busqueda)

        if not qs.exists():
            messages.info(self.request, f"No hay calificaciones para {periodo_str} con los filtros aplicados.")

        # evitar N+1
        return qs.select_related('oficina', 'categoria').order_by('apellido', 'nombre')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anio, mes, periodo_str = get_periodo_from_session(self.request)
        hoy = date.today()

        periodo_confirmado = False
        periodo_abierto = False
        try:
            lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
            if lp:
                if hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA') and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA:
                    periodo_confirmado = True
                elif hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA') and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA:
                    periodo_abierto = True
                elif hasattr(LiquidacionPeriodo, 'ESTADO_CERRADA') and lp.estado == LiquidacionPeriodo.ESTADO_CERRADA:
                    periodo_abierto = False
                else:
                    periodo_abierto = not periodo_confirmado
        except Exception:
            periodo_confirmado = False
            periodo_abierto = True

        es_actual = (anio == hoy.year and mes == hoy.month)

        ctx['oficinas'] = Oficina.objects.all().order_by('nombre')
        ctx['oficina_sel'] = self.request.GET.get('oficina', 'TODAS')

        # nombre de oficina seleccionada (si corresponde)
        oficina_sel = ctx['oficina_sel']
        if oficina_sel and oficina_sel != 'TODAS':
            try:
                ctx['oficina_nombre'] = Oficina.objects.get(pk=int(oficina_sel)).nombre
            except Exception:
                oficina_obj = Oficina.objects.filter(nombre__icontains=oficina_sel).first()
                ctx['oficina_nombre'] = oficina_obj.nombre if oficina_obj else ''
        else:
            ctx['oficina_nombre'] = ''

        ctx['q'] = self.request.GET.get('q', '')
        ctx['mes_actual'] = mes
        ctx['año_actual'] = anio
        ctx['month_name'] = MONTH_NAMES.get(mes, str(mes))
        ctx['periodo_str'] = periodo_str
        ctx['allow_edit'] = periodo_abierto and not periodo_confirmado
        ctx['periodo_confirmado'] = periodo_confirmado
        ctx['periodo_abierto'] = periodo_abierto
        ctx['es_periodo_actual'] = es_actual

        return ctx


class CalificacionCreateView(LoginRequiredMixin, CreateView):
    model = Calificacion
    form_class = CalificacionForm
    template_name = 'empleados/calificacion_form.html'
    success_url = reverse_lazy('empleados:calificacion-list')
    login_url = 'login'

    def form_valid(self, form):
        hoy = date.today()
        form.instance.mes = hoy.month
        form.instance.año = hoy.year
        form.instance.id_usuario = self.request.user  # ← AGREGAR ESTA LÍNEA
        return super().form_valid(form)


class CalificacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Calificacion
    form_class = CalificacionForm
    template_name = 'empleados/calificacion_form.html'
    success_url = reverse_lazy('empleados:calificacion-list')
    login_url = 'login'

    def form_valid(self, form):
        form.instance.id_usuario = self.request.user  # ← AGREGAR ESTA LÍNEA
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object and self.object.empleado:
            ctx['empleado'] = self.object.empleado
        return ctx

from datetime import date
import calendar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from .models import Categoria
from .forms import CategoriaForm


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'empleados/categoria_list.html'
    context_object_name = 'categorias'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context['mes_actual'] = hoy.month
        context['año_actual'] = hoy.year
        context['month_name'] = calendar.month_name[hoy.month].capitalize()
        return context

    def get_queryset(self):
        # Trae en la misma consulta el nivel (para poder mostrar el básico)
        return (Categoria.objects
                .select_related('nivel')    # ← clave para ver cat.nivel.monto / cat.basico
                .order_by('nombre'))


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'empleados/categoria_form.html'
    success_url = reverse_lazy('empleados:categoria-list')

    def form_valid(self, form):
        form.instance.area = 'PRESIDENCIA'
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'empleados/categoria_form.html'
    success_url = reverse_lazy('empleados:categoria-list')

    def form_valid(self, form):
        form.instance.area = 'PRESIDENCIA'
        return super().form_valid(form)






# --- OFICIOS JUDICIALES (LIST) ---
from django import forms as dj_forms
from decimal import Decimal
from calendar import monthrange
from datetime import date as _date
import calendar

from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.db.models import (
    Q, OuterRef, Subquery, DecimalField, IntegerField, Value, Count
)
from django.db.models.functions import Coalesce

from .models import Empleado, OficioJudicial, LiquidacionPeriodo
from .utils import get_periodo_from_session


def _q_activo_en_periodo_empleado(anio: int, mes: int) -> Q:
    fin_periodo = _date(int(anio), int(mes), monthrange(int(anio), int(mes))[1])
    inicio_periodo = _date(int(anio), int(mes), 1)
    return Q(fecha_ingreso__lte=fin_periodo) & (
        Q(fecha_salida__isnull=True) | Q(fecha_salida__gte=inicio_periodo)
    )


class OficioJudicialListView(LoginRequiredMixin, ListView):
    template_name = 'empleados/oficiojudicial_list.html'
    context_object_name = 'rows'
    login_url = 'login'
    paginate_by = 20

    def _periodo(self):
        anio_ses, mes_ses, _ = get_periodo_from_session(self.request)
        try:
            anio = int(self.request.GET.get('anio') or anio_ses)
        except Exception:
            anio = anio_ses
        try:
            mes = int(self.request.GET.get('mes') or mes_ses)
        except Exception:
            mes = mes_ses
        return anio, mes

    def get_queryset(self):
        anio, mes = self._periodo()
        hoy = timezone.now().date()

        periodo_str = f"{anio}-{mes:02d}"
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        periodo_confirmado = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA')
                                  and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA)
        periodo_abierto = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA')
                               and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA)
        es_actual = (anio == hoy.year and mes == hoy.month)

        self._allow_edit = (periodo_abierto and es_actual and not periodo_confirmado)
        self._periodo_confirmado = periodo_confirmado
        self._periodo_abierto = periodo_abierto or (lp is None and es_actual)
        self._is_future = (anio, mes) > (hoy.year, hoy.month)

        # FUTURO → sin listado
        if self._is_future:
            messages.info(self.request, "No se cargaron datos para oficios futuros.")
            return Empleado.objects.none()

        # Empleados existentes en el período
        q_periodo = _q_activo_en_periodo_empleado(anio, mes)

        # Último oficio del período por empleado (más reciente)
        oj_qs = (OficioJudicial.objects
                 .filter(empleado_id=OuterRef('pk'), anio=anio, mes=mes)
                 .order_by('-id'))

        qs = (Empleado.objects
              .filter(q_periodo)
              .order_by('apellido', 'nombre')
              .annotate(
                  oj_id    = Subquery(oj_qs.values('id')[:1]),
                  oj_tipo  = Subquery(oj_qs.values('tipo')[:1], output_field=IntegerField()),
                  oj_monto = Coalesce(
                      Subquery(oj_qs.values('monto_descontar')[:1],
                               output_field=DecimalField(max_digits=12, decimal_places=2)),
                      Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2)),
                  ),
                  oj_porc  = Coalesce(
                      Subquery(oj_qs.values('porcentaje_descontar')[:1],
                               output_field=DecimalField(max_digits=7, decimal_places=2)),
                      Value(Decimal('0.00'), output_field=DecimalField(max_digits=7, decimal_places=2)),
                  ),
                  # related_name correcto en FK: oficios_judiciales
                  cantidad_oficios = Count(
                      'oficios_judiciales',
                      filter=Q(oficios_judiciales__anio=anio, oficios_judiciales__mes=mes)
                  ),
              ))

        # Filtro por estado en el período
        estado = (self.request.GET.get('estado') or 'activos').strip().lower()
        fin_periodo = _date(anio, mes, monthrange(anio, mes)[1])
        if estado == 'activos':
            qs = qs.filter(Q(fecha_salida__isnull=True) | Q(fecha_salida__gt=fin_periodo))
        elif estado == 'inactivos':
            qs = qs.filter(fecha_salida__lte=fin_periodo)

        # Filtros adicionales
        empleado = (self.request.GET.get('empleado') or '').strip()
        tipo     = (self.request.GET.get('tipo') or '').strip()   # '1' o '2'

        if empleado:
            qs = qs.filter(
                Q(apellido__icontains=empleado) |
                Q(nombre__icontains=empleado)   |
                Q(cuil__icontains=empleado)     |
                Q(dni__icontains=empleado)
            )
        if tipo in ('1', '2'):
            qs = qs.filter(oj_id__isnull=False, oj_tipo=int(tipo))

        # Si no es editable → mostrar solo quienes tengan al menos un oficio
        if not self._allow_edit:
            qs = qs.filter(oj_id__isnull=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anio, mes = self._periodo()
        hoy = timezone.now().date()
        periodo_str = f"{anio}-{mes:02d}"
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        periodo_confirmado = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA')
                                  and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA)
        periodo_abierto = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA')
                               and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA)
        es_actual = (anio == hoy.year and mes == hoy.month)

        ctx['anio_actual'] = anio
        ctx['mes_actual']  = mes
        ctx['month_name']  = MONTH_NAMES.get(mes, str(mes))
        ctx['allow_edit']  = (periodo_abierto and es_actual and not periodo_confirmado)
        ctx['periodo_confirmado'] = periodo_confirmado
        ctx['periodo_abierto']    = periodo_abierto or (lp is None and es_actual)
        ctx['es_periodo_actual']  = es_actual
        ctx['is_future']          = (anio, mes) > (hoy.year, hoy.month)

        ctx['f_empleado'] = self.request.GET.get('empleado', '')
        ctx['f_anio']     = anio
        ctx['f_mes']      = mes
        ctx['f_tipo']     = self.request.GET.get('tipo', '')
        ctx['f_estado']   = self.request.GET.get('estado', 'activos')

        # Años / meses
        first_employee = Empleado.objects.order_by('fecha_ingreso').first()
        first_year = first_employee.fecha_ingreso.year if first_employee else timezone.now().year
        current_year = timezone.now().year
        ctx['years'] = list(range(first_year, current_year + 1))
        ctx['months'] = [(i, MONTH_NAMES.get(i, str(i))) for i in range(1, 13)]

        
        return ctx


# ============ DETALLE: lista de oficios de un empleado en el período ============
class OficioJudicialEmpleadoListView(LoginRequiredMixin, ListView):
    template_name = 'empleados/oficiojudicial_empleado_list.html'
    context_object_name = 'oficios'
    login_url = 'login'
    paginate_by = 100

    def _periodo(self):
        anio_ses, mes_ses, _ = get_periodo_from_session(self.request)
        try:
            anio = int(self.request.GET.get('anio') or anio_ses)
        except Exception:
            anio = anio_ses
        try:
            mes = int(self.request.GET.get('mes') or mes_ses)
        except Exception:
            mes = mes_ses
        return anio, mes

    def get_queryset(self):
        self.empleado = get_object_or_404(Empleado, pk=self.kwargs['empleado_id'])
        anio, mes = self._periodo()
        hoy = timezone.now().date()

        periodo_str = f"{anio}-{mes:02d}"
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        periodo_confirmado = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA')
                                  and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA)
        periodo_abierto = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA')
                               and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA)
        es_actual = (anio == hoy.year and mes == hoy.month)

        self._allow_edit = (periodo_abierto and es_actual and not periodo_confirmado)
        self._is_future = (anio, mes) > (hoy.year, hoy.month)

        # Futuros → nada
        if self._is_future:
            messages.info(self.request, "No se cargaron datos para oficios futuros.")
            return OficioJudicial.objects.none()

        # Todos los oficios del empleado en el período, más recientes primero
        return (OficioJudicial.objects
                .filter(empleado=self.empleado, anio=anio, mes=mes)
                .order_by('-id'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anio, mes = self._periodo()
        hoy = timezone.now().date()
        periodo_str = f"{anio}-{mes:02d}"
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        periodo_confirmado = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_CONFIRMADA')
                                  and lp.estado == LiquidacionPeriodo.ESTADO_CONFIRMADA)
        periodo_abierto = bool(lp and hasattr(LiquidacionPeriodo, 'ESTADO_ABIERTA')
                               and lp.estado == LiquidacionPeriodo.ESTADO_ABIERTA)
        es_actual = (anio == hoy.year and mes == hoy.month)

        ctx.update({
            'empleado': self.empleado,
            'anio_actual': anio,
            'mes_actual': mes,
            'month_name': MONTH_NAMES.get(mes, str(mes)),
            'allow_edit': self._allow_edit,
            'periodo_confirmado': periodo_confirmado,
            'periodo_abierto': periodo_abierto or (lp is None and es_actual),
            'es_periodo_actual': es_actual,
            'is_future': self._is_future,
        })
        return ctx


# ============ CREATE / UPDATE / DELETE ============
class OficioJudicialCreateView(LoginRequiredMixin, CreateView):
    model = OficioJudicial
    template_name = 'empleados/oficiojudicial_form.html'
    login_url = 'login'

    def get_form_class(self):
        from .forms import OficioJudicialForm
        return OficioJudicialForm

    def dispatch(self, request, *args, **kwargs):
        # Período del panel: solo se puede crear en el PERÍODO ACTUAL
        anio, mes, _ = get_periodo_from_session(request)
        hoy = timezone.now().date()
        if (anio, mes) != (hoy.year, hoy.month):
            messages.error(request, 'Solo se pueden crear oficios para el período actual.')
            return redirect('empleados:oficiojudicial-list')

        emp_id = request.GET.get('empleado')
        if not emp_id:
            messages.error(request, 'Seleccioná un empleado desde la lista para crear el oficio.')
            return redirect('empleados:oficiojudicial-list')

        self._empleado = get_object_or_404(Empleado, pk=emp_id)
        self._anio = anio
        self._mes = mes
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Inicializar y ocultar campos fijos
        form.fields['empleado'].initial = self._empleado.pk
        form.fields['anio'].initial = self._anio
        form.fields['mes'].initial = self._mes
        form.fields['empleado'].widget = dj_forms.HiddenInput()
        form.fields['anio'].widget = dj_forms.HiddenInput()
        form.fields['mes'].widget = dj_forms.HiddenInput()
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'empleado_obj': self._empleado,
            'anio_fijo': self._anio,
            'mes_fijo': self._mes,
            'modo': 'create',
        })
        return ctx

    def form_valid(self, form):
        # SIEMPRE crear un nuevo oficio (permitimos múltiples por empleado y período)
        obj = form.save(commit=False)
        obj.empleado = self._empleado
        obj.anio = self._anio
        obj.mes = self._mes
        obj.save()

        messages.success(self.request, 'Oficio judicial creado correctamente.')
        # Ver todos los oficios del empleado en el período
        url = f"{reverse('empleados:oficiojudicial-empleado', args=[self._empleado.pk])}?anio={self._anio}&mes={self._mes}"
        return redirect(url)


class OficioJudicialUpdateView(LoginRequiredMixin, UpdateView):
    model = OficioJudicial
    template_name = 'empleados/oficiojudicial_form.html'
    success_url = reverse_lazy('empleados:oficiojudicial-list')
    login_url = 'login'

    def get_form_class(self):
        from .forms import OficioJudicialForm
        return OficioJudicialForm

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        hoy = timezone.now().date()
        if (obj.anio, obj.mes) != (hoy.year, hoy.month):
            messages.error(request, 'Solo se pueden editar oficios del período actual.')
            return redirect('empleados:oficiojudicial-list')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # ocultar campos fijos
        form.fields['empleado'].widget = dj_forms.HiddenInput()
        form.fields['anio'].widget = dj_forms.HiddenInput()
        form.fields['mes'].widget = dj_forms.HiddenInput()
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        ctx.update({
            'empleado_obj': obj.empleado,
            'anio_fijo': obj.anio,
            'mes_fijo': obj.mes,
            'modo': 'update',
        })
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Oficio judicial actualizado.')
        return super().form_valid(form)


class OficioJudicialDeleteView(LoginRequiredMixin, DeleteView):
    model = OficioJudicial
    template_name = 'empleados/oficiojudicial_confirm_delete.html'
    success_url = reverse_lazy('empleados:oficiojudicial-list')
    login_url = 'login'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Oficio judicial eliminado.')
        return super().delete(request, *args, **kwargs)

    

from django.db.models import Q, OuterRef, Subquery
from datetime import date
from .views import MONTH_NAMES
from .models import Empleado, Calificacion

from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

@login_required(login_url='login')
def calificacion_list(request):
    hoy = date.today()
    mes_actual = hoy.month
    año_actual = hoy.year

    area = request.GET.get('area', '')
    q = request.GET.get('q', '').strip()

    # Traer empleados activos filtrados por área
    empleados = Empleado.objects.filter(
        estado=1,
        fecha_salida__isnull=True
    )
    if area:
        empleados = empleados.filter(area__iexact=area)

    # Subquery para obtener calificacion del mes actual por empleado
    cal_subquery = Calificacion.objects.filter(
        empleado=OuterRef('pk'),
        mes=mes_actual,
        año=año_actual
    ).values('calificacion')[:1]

    empleados = empleados.annotate(
        calificacion_actual=Coalesce(Subquery(cal_subquery), Value(''))
    )

    if q:
        empleados = empleados.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(cuil__icontains=q) |
            Q(dni__icontains=q)
        )

    AREAS = (
        Empleado.objects.values_list('area', flat=True)
        .order_by('area')
        .distinct()
    )

    month_name_str = MONTH_NAMES.get(mes_actual, str(mes_actual))

    return render(request, 'empleados/calificacion_list.html', {
        'empleados': empleados.order_by('apellido', 'nombre'),
        'areas': AREAS,
        'area_sel': area,
        'q': q,
        'mes_actual': mes_actual,
        'año_actual': año_actual,
        'month_name': month_name_str,
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def oficiojudicial_list(request):
    # Por ahora devolvemos una plantilla básica
    return render(request, "empleados/oficiojudicial_list.html", {})





