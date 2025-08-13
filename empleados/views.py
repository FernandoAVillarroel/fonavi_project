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


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def presidencia_dashboard(request):
    # 1) Periodos para el selector (incluye HOY aunque no exista en BD)
    periodos = _periodos_con_hoy_primero()

    # 2) Áreas fijas
    areas = [
        'PRESIDENCIA',
        'SECRET. TÉCNICA CONTABLE',
        'PLANES DE EMERGENCIA',
        'SECRETARÍA TEC. SOCIAL',
    ]

    # 3) Selección de mes/año (por GET o por defecto HOY)
    mes_sel, año_sel = _leer_periodo(request, periodos)

    # 4) Área seleccionada
    area_sel = request.GET.get('area', areas[0])

    # 5) Búsqueda de empleados activos
    q = request.GET.get('q', '').strip()
    empleados = Empleado.objects.filter(
        estado=1,
        fecha_salida__isnull=True
    ).order_by('apellido', 'nombre')

    if q:
        if ' ' in q:
            nombre_part, apellido_part = q.split(None, 1)
            empleados = empleados.filter(
                Q(nombre__icontains=nombre_part),
                Q(apellido__icontains=apellido_part)
            )
        else:
            empleados = empleados.filter(
                Q(nombre__icontains=q)   |
                Q(apellido__icontains=q) |
                Q(dni__icontains=q)      |
                Q(cuil__icontains=q)
            ).distinct()

    # 6) Contadores
    total_empleados = Empleado.objects.count()
    total_activos   = Empleado.objects.filter(estado=1, fecha_salida__isnull=True).count()
    total_inactivos = Empleado.objects.filter(Q(estado=0) | Q(fecha_salida__isnull=False)).count()

    return render(request, 'presidencia/dashboard.html', {
        'periodos':         periodos,      # [(mes, nombre_mes, año), ...] (HOY incluido)
        'mes_sel':          mes_sel,
        'año_sel':          año_sel,
        'areas':            areas,
        'area_sel':         area_sel,
        'empleados':        empleados,
        'q':                q,
        'total_empleados':  total_empleados,
        'total_activos':    total_activos,
        'total_inactivos':  total_inactivos,
    })



from decimal import Decimal
from django.urls import reverse
from django.db import transaction
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from .models import (
    Empleado, Preliquidacion, Liquidacion, Calificacion, OficioJudicial,
    NivelBasico,  # importante
)

# ───────────────────────────── Helpers ─────────────────────────────

# helpers en views.py (o donde lo tengas)
from decimal import Decimal

def _extrae_importe(obj):
    if not obj:
        return None
    # ahora también chequea 'nivel' (caso de tu modelo NivelBasico)
    for nombre in ('monto', 'importe', 'basico', 'valor', 'sueldo_basico', 'nivel'):
        val = getattr(obj, nombre, None)
        if val is not None:
            try:
                return Decimal(val)
            except Exception:
                pass
    return None



def _nivel_desde_categoria(cat):
    """
    Devuelve el objeto NivelBasico asociado a la categoría.
    Soporta:
      - FK real: categoria.nivel
      - ID entero: categoria.id_nivel / categoria.nivel_id
    """
    if not cat:
        return None

    # 1) FK real
    nb = getattr(cat, 'nivel', None)
    if nb:
        return nb

    # 2) Campo entero
    for attr in ('id_nivel', 'nivel_id'):
        nivel_id = getattr(cat, attr, None)
        if nivel_id:
            try:
                nivel_id = int(nivel_id)
            except Exception:
                nivel_id = None
            if nivel_id:
                # por PK
                nb = NivelBasico.objects.filter(pk=nivel_id).first()
                if nb:
                    return nb
                # por campo alternativo id_nivel dentro del modelo de niveles
                try:
                    nb = NivelBasico.objects.filter(id_nivel=nivel_id).first()
                    if nb:
                        return nb
                except Exception:
                    pass
    return None


def _nivel_y_basico_de(emp):
    """
    Determina (nivel_obj, basico_decimal) para un empleado:
      1) usa emp.nivel_basico si está presente
      2) si no, resuelve nivel desde la categoría (FK o id)
      3) si no encuentra, devuelve (None, Decimal('0.00'))
    """
    # 1) Nivel asignado directamente al empleado
    nb = getattr(emp, 'nivel_basico', None)
    if nb:
        imp = _extrae_importe(nb)
        if imp is not None:
            return nb, imp

    # 2) Nivel inferido desde la categoría
    nb = _nivel_desde_categoria(getattr(emp, 'categoria', None))
    if nb:
        imp = _extrae_importe(nb)
        if imp is not None:
            return nb, imp

    # 3) Nada
    return None, Decimal('0.00')


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




# views.py
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.urls import reverse
from django.db import transaction
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Empleado, Preliquidacion, OficioJudicial, Calificacion

# si ya lo tenés definido, dejá tu propia versión
def _money(x):
    return Decimal(x or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def generar_preliquidacion(request):
    """
    Genera/regenerea preliquidaciones del período elegido.
    - Toma el básico de la categoría/nivel del empleado.
    - Aplica CALIFICACIÓN (el save() de Preliquidacion ya lo hace; aquí además la seteamos).
    - Recalcula BRUTO, JUB, OS.
    - Aplica OFICIO JUDICIAL: 1=monto fijo, 2=% sobre BRUTO (ajusta si querés otra base).
    - Liquido = Bruto - (Jub + OS + Oficio).
    """
    mes  = int(request.GET.get('mes',  date.today().month))
    año  = int(request.GET.get('año',  date.today().year))
    area = request.GET.get('area', 'TODAS')

    # Empleados activos del área (o todas)
    empleados = (
        Empleado.objects
        .filter(estado=1, fecha_salida__isnull=True)
        .select_related('categoria', 'oficina', 'titulo', 'nivel_basico')
    )
    if area and area != 'TODAS':
        empleados = empleados.filter(area=area)

    # Limpiar preliqs del período/área para regenerar
    preliqs = Preliquidacion.objects.filter(mes=mes, año=año)
    if area and area != 'TODAS':
        preliqs = preliqs.filter(empleado__area=area)
    preliqs.delete()

    sin_basico = []

    with transaction.atomic():
        for emp in empleados:
            # === Resuelve nivel y básico del empleado (usa tu helper existente) ===
            nivel_fk, basico = _nivel_y_basico_de(emp)

            # Crear/actualizar la preliquidación base
            obj, _ = Preliquidacion.objects.update_or_create(
                empleado=emp, año=año, mes=mes,
                defaults={
                    'categoria'        : emp.categoria,
                    'oficina'          : emp.oficina,
                    'titulo'           : emp.titulo,
                    'nivel'            : nivel_fk,
                    'basico'           : basico,
                    'situacion'        : emp.situacion,
                    'categoria_nombre' : getattr(emp.categoria, 'nombre', None),
                    'oficina_nombre'   : getattr(emp.oficina, 'nombre', None),
                    'titulo_completo'  : getattr(emp.titulo, 'titulo_completo', None),
                }
            )

            # === Forzar calificación del período (por claridad) ===
            # Tu modelo Preliquidacion.save() ya la busca; esto asegura el valor antes del save.
            calif = (Calificacion.objects
                        .filter(empleado=emp, año=año, mes=mes)
                        .values_list('calificacion', flat=True)
                        .first())
            obj.calificacion = calif if calif is not None else Decimal('100')

            # Guarda: el save() del modelo calcula:
            # - básico calificado (básico * calif/100)
            # - antigüedad, bonificación por título
            # - suplementos (según tu Categoría)
            # - BRUTO, JUB (11%), OS (5%)
            obj.save()

            # === OFICIO JUDICIAL (del período) ===
            # Regla adoptada aquí:
            #   tipo=1 -> monto fijo
            #   tipo=2 -> % aplicado sobre BRUTO (cambiá a otra base si querés)
            oj = (OficioJudicial.objects
                    .filter(empleado=emp, anio=año, mes=mes)
                    .order_by('-id')
                    .first())

            if oj:
                if oj.tipo == 1:
                    # Monto fijo
                    obj.oficio_judicial = _money(oj.monto_descontar or 0)
                elif oj.tipo == 2:
                    # % sobre BRUTO (podés cambiar a basico_total si esa fuera la regla)
                    base = obj.bruto or Decimal('0')
                    porc = (oj.porcentaje_descontar or Decimal('0')) / Decimal('100')
                    obj.oficio_judicial = _money(base * porc)
                else:
                    obj.oficio_judicial = Decimal('0.00')
            else:
                obj.oficio_judicial = Decimal('0.00')

            # === Recalcular líquido con el oficio incluido ===
            desc = (obj.jubilacion or 0) + (obj.obra_social or 0) + (obj.oficio_judicial or 0)
            obj.liquido = _money((obj.bruto or 0) - desc)

            obj.save(update_fields=['oficio_judicial', 'liquido'])

            if basico is None or basico <= 0:
                sin_basico.append(emp.pk)

    if sin_basico:
        print(f"[PRELIQ {mes}/{año}] Empleados sin básico resuelto: {sin_basico}")

    return redirect(f"{reverse('preliquidacion_overview')}?mes={mes}&año={año}&area={area}")





from datetime import date
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import render
# Asumo que AREAS y MONTH_NAMES ya están definidas en este módulo

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def preliquidacion_overview(request):
    mes  = int(request.GET.get('mes',  date.today().month))
    año  = int(request.GET.get('año',  date.today().year))
    area = request.GET.get('area', 'TODAS')
    q    = (request.GET.get('q') or '').strip()

    qs = (
        Preliquidacion.objects
        .filter(
            mes=mes, año=año,
            empleado__estado=1,
            empleado__fecha_salida__isnull=True
        )
        .select_related('empleado', 'categoria', 'oficina', 'titulo', 'nivel')
        .order_by('empleado__apellido', 'empleado__nombre')
    )

    if area and area != 'TODAS':
        qs = qs.filter(empleado__area=area)

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

    ctx = {
        'preliquidaciones': qs,
        'areas'           : AREAS,                  # incluye 'TODAS'
        'mes_sel'         : mes,
        'año_sel'         : año,
        'area_sel'        : area,
        'q'               : q,
        'month_name'      : MONTH_NAMES.get(mes, str(mes)),
    }
    return render(request, 'presidencia/preliquidacion_overview.html', ctx)


def _get_queryset_and_totals(mes, año, area):
    # 1) Sincronizar Preliquidación → Liquidación
    preqs = Preliquidacion.objects.filter(mes=mes, año=año)
    if area and area != 'TODAS':
        preqs = preqs.filter(empleado__area=area)

    with transaction.atomic():
        for pre in preqs.select_related('empleado'):
            Liquidacion.objects.update_or_create(
                empleado=pre.empleado, mes=mes, año=año,
                defaults={
                    'categoria'         : pre.categoria,
                    'oficina'           : pre.oficina,
                    'titulo'            : pre.titulo,
                    'nivel'             : pre.nivel,
                    'basico'            : pre.basico,
                    'calificacion'      : pre.calificacion,
                    'antiguedad'        : pre.antiguedad,
                    'importe_antiguedad': pre.importe_antiguedad,
                    'importe_titulo'    : pre.importe_titulo,
                    'basico_total'      : pre.basico_total,
                    'supl1'             : pre.supl1,
                    'supl2'             : pre.supl2,
                    'supl3'             : pre.supl3,
                    'supl4'             : pre.supl4,
                    'supl6'             : pre.supl6,
                    'supl8'             : pre.supl8,
                    'supl12'            : pre.supl12,
                    'total_suplementos' : pre.total_suplementos,
                    'bruto'             : pre.bruto,
                    'jubilacion'        : pre.jubilacion,
                    'obra_social'       : pre.obra_social,
                    'oficio_judicial'   : pre.oficio_judicial,
                    'total_descuentos'  : pre.total_descuentos,
                    'liquido'           : pre.liquido,
                    'situacion'         : pre.situacion,
                    'categoria_nombre'  : pre.categoria_nombre,
                    'oficina_nombre'    : pre.oficina_nombre,
                    'titulo_completo'   : pre.titulo_completo,
                }
            )

    # 2) Query base y desgloses
    base_qs = Liquidacion.objects.filter(
        mes=mes, año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True
    )
    if area and area != 'TODAS':
        base_qs = base_qs.filter(empleado__area=area)

    qs_cont = base_qs.filter(situacion='C')
    qs_perm = base_qs.filter(situacion='P')

    # marcar como conformada
    base_qs.update(conformada=True)

    # 3) Totales
    def totals(qs):
        agg = qs.aggregate(bruto=Sum('bruto'), liquido=Sum('liquido'))
        return {
            'count'  : qs.count(),
            'bruto'  : agg['bruto']   or Decimal('0'),
            'liquido': agg['liquido'] or Decimal('0'),
        }

    return base_qs, qs_cont, qs_perm, totals(base_qs), totals(qs_cont), totals(qs_perm)

from datetime import date
from decimal import Decimal
from django.shortcuts import render
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Preliquidacion, Liquidacion
from .views import MONTH_NAMES, is_presidencia

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    mes   = int(request.GET.get('mes', date.today().month))
    año   = int(request.GET.get('año', date.today().year))
    area  = request.GET.get('area', 'PRESIDENCIA')
    tipo  = request.GET.get('tipo', 'todos')

    # 1) Solo empleados activos, mes/año y área correcta
    preqs = Preliquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True
    )
    # Si el área NO es PRESIDENCIA, filtrá por área
    if area and area.upper() != 'PRESIDENCIA':
        preqs = preqs.filter(categoria__nombre=area)

    # 2) Sincroniza con liquidación (sólo para estos empleados activos)
    with transaction.atomic():
        for pre in preqs:
            Liquidacion.objects.update_or_create(
                empleado=pre.empleado,
                mes=mes,
                año=año,
                defaults={
                    'categoria':          pre.categoria,
                    'oficina':            pre.oficina,
                    'titulo':             getattr(pre, 'titulo', None),
                    'nivel':              pre.nivel,
                    'basico':             pre.basico,
                    'calificacion':       pre.calificacion,
                    'antiguedad':         pre.antiguedad,
                    'importe_antiguedad': pre.importe_antiguedad,
                    'importe_titulo':     pre.importe_titulo,
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

    # 3) Tomá sólo las liquidaciones de los empleados de preqs
    empleados_ids = preqs.values_list('empleado_id', flat=True)
    base_qs = Liquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado_id__in=empleados_ids
    )

    # 4) Filtros por tipo de empleado
    if tipo == 'contratados':
        liqs = base_qs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        liqs = base_qs.filter(situacion='P')
        title = 'Permanentes'
    else:
        liqs = base_qs
        title = 'Todos los Empleados'

    # 5) Totales
    tot = {
        'count': liqs.count(),
        'bruto': liqs.aggregate(Sum('bruto'))['bruto__sum'] or Decimal('0'),
        'liquido': liqs.aggregate(Sum('liquido'))['liquido__sum'] or Decimal('0'),
    }

    # 6) Renderizado
    return render(request, 'presidencia/liquidacion_list.html', {
        'mes_sel': mes,
        'año_sel': año,
        'month_name': MONTH_NAMES.get(mes, str(mes)),
        'area_sel': area,
        'tipo': tipo,
        'liqs': liqs.order_by('empleado__apellido', 'empleado__nombre'),
        'tot': tot,
        'title': title
    })




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
# from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect

# —— helper: antigüedad medida al 1° de febrero (corte anual) ——
def _antiguedad_al_1_febrero(fecha_ingreso, hoy=None):
    if not fecha_ingreso:
        return None
    hoy = hoy or date.today()

    # corte de este año
    corte = date(hoy.year, 2, 1)
    # si todavía no llegamos al 1/2, el corte válido es el 1/2 del año anterior
    if hoy < corte:
        corte = date(hoy.year - 1, 2, 1)

    años = (
        corte.year - fecha_ingreso.year
        - ((corte.month, corte.day) < (fecha_ingreso.month, fecha_ingreso.day))
    )
    return max(años, 0)

@login_required(login_url='login')
@user_passes_test(is_presidencia)
def actualizar_antiguedad(request):
    hoy = date.today()

    # solo a modo informativo (por si no se ejecuta el 1/2)
    corte = date(hoy.year, 2, 1)
    if hoy < corte:
        corte = date(hoy.year - 1, 2, 1)
    if (hoy.month, hoy.day) != (2, 1):
        messages.warning(
            request,
            "Esta acción idealmente se ejecuta el 1 de febrero. "
            f"Se recalculó usando el corte {corte.strftime('%d/%m/%Y')}."
        )

    empleados = Empleado.objects.filter(estado=1, fecha_salida__isnull=True)
    actualizados = 0
    for emp in empleados:
        if emp.fecha_ingreso:
            nuevo_valor = _antiguedad_al_1_febrero(emp.fecha_ingreso, hoy=hoy)
            if nuevo_valor is not None and nuevo_valor != emp.antiguedad:
                emp.antiguedad = nuevo_valor
                emp.save(update_fields=['antiguedad'])
            actualizados += 1

    messages.success(
        request,
        f"✅ Se actualizaron antigüedades (corte {corte.strftime('%d/%m/%Y')}) de {actualizados} empleados."
    )
    # → volver a la planilla de empleados
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
from .views     import MONTH_NAMES, is_presidencia


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


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    # Parámetros
    mes   = int(request.GET.get('mes',  date.today().month))
    año   = int(request.GET.get('año',  date.today().year))
    area  = request.GET.get('area', None)
    tipo  = request.GET.get('tipo', 'todos')  # 'todos' | 'contratados' | 'permanentes'

    # QS y totales
    base_qs, qs_contratados, qs_permanentes, tot_all, tot_cont, tot_perm = (
        _get_queryset_and_totals(mes, año, area)
    )

    # Selección según tipo
    if tipo == 'contratados':
        liqs, tot, title = qs_contratados, tot_cont, 'Contratados'
    elif tipo == 'permanentes':
        liqs, tot, title = qs_permanentes, tot_perm, 'Permanentes'
    else:
        liqs, tot, title = base_qs, tot_all, 'Todos los Empleados'

    # Render a pantalla
    return render(request, 'presidencia/liquidacion_list.html', {
        'mes_sel':    mes,
        'año_sel':    año,
        'month_name': MONTH_NAMES.get(mes, str(mes)),
        'area_sel':   area,
        'tipo':       tipo,
        'liqs':       liqs.order_by('empleado__apellido', 'empleado__nombre'),
        'tot':        tot,
        'title':      title,
    })


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    mes   = int(request.GET.get('mes', date.today().month))
    año   = int(request.GET.get('año', date.today().year))
    area  = request.GET.get('area', 'PRESIDENCIA')
    tipo  = request.GET.get('tipo', 'todos')

    preqs = Preliquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True
    )
    if area and area.upper() != 'PRESIDENCIA':
        preqs = preqs.filter(categoria_nombre=area)

    with transaction.atomic():
        for pre in preqs:
            Liquidacion.objects.update_or_create(
                empleado=pre.empleado,
                mes=mes,
                año=año,
                defaults={
                    # TODOS tus campos...
                    'categoria':          pre.categoria,
                    'oficina':            pre.oficina,
                    'titulo':             pre.titulo,
                    'nivel':              pre.nivel,
                    'basico':             pre.basico,
                    'calificacion':       pre.calificacion,
                    'antiguedad':         pre.antiguedad,
                    'importe_antiguedad': pre.importe_antiguedad,
                    'importe_titulo':     pre.importe_titulo,
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

    empleados_ids = preqs.values_list('empleado_id', flat=True)
    base_qs = Liquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado_id__in=empleados_ids,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True
    )

    if tipo == 'contratados':
        liqs = base_qs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        liqs = base_qs.filter(situacion='P')
        title = 'Permanentes'
    else:
        liqs = base_qs
        title = 'Todos los Empleados'

    tot = {
        'count': liqs.count(),
        'bruto': liqs.aggregate(Sum('bruto'))['bruto__sum'] or Decimal('0'),
        'liquido': liqs.aggregate(Sum('liquido'))['liquido__sum'] or Decimal('0'),
    }

    # --> AQUI VA EL CALCULO DE TOTALES POR COLUMNA <--
    totales_col = liqs.aggregate(
        basico=Sum('basico'),
        importe_antiguedad=Sum('importe_antiguedad'),
        importe_titulo=Sum('importe_titulo'),
        basico_total=Sum('basico_total'),
        supl1=Sum('supl1'), supl2=Sum('supl2'), supl3=Sum('supl3'),
        supl4=Sum('supl4'), supl6=Sum('supl6'), supl8=Sum('supl8'), supl12=Sum('supl12'),
        total_suplementos=Sum('total_suplementos'),
        bruto=Sum('bruto'),
        jubilacion=Sum('jubilacion'),
        obra_social=Sum('obra_social'),
        oficio_judicial=Sum('oficio_judicial'),
        total_descuentos=Sum('total_descuentos'),
        liquido=Sum('liquido')
    )

    return render(request, 'presidencia/liquidacion_list.html', {
        'mes_sel': mes,
        'año_sel': año,
        'month_name': MONTH_NAMES.get(mes, str(mes)),
        'area_sel': area,
        'tipo': tipo,
        'liqs': liqs.order_by('empleado__apellido', 'empleado__nombre'),
        'tot': tot,
        'title': title,
        'totales_col': totales_col,  # <-- IMPORTANTE!
    })



# ——————————————————————————————————————————————————————————————————————
# CRUD DE EMPLEADOS, CALIFICACIONES, CATEGORIAS, OFICIOS
# ——————————————————————————————————————————————————————————————————————

# empleados/views.py
from django.views.generic import ListView
from django.db.models import Q
from .models import Empleado, Categoria

class EmpleadoListView(ListView):
    model = Empleado
    template_name = "empleados/empleados_list.html"   # ← plural
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
                combinado = (
                    (Q(nombre__icontains=n1) & Q(apellido__icontains=n2)) |
                    (Q(nombre__icontains=n2) & Q(apellido__icontains=n1))
                )
                base |= combinado
            qs = qs.filter(base)

        if area and area != "TODAS":
            qs = qs.filter(categoria__area=area)

        if situacion in ("P", "C"):
            qs = qs.filter(situacion=situacion)

        if estado == "activos":
            qs = qs.filter(estado=1, fecha_salida__isnull=True)
        elif estado == "inactivos":
            qs = qs.filter(Q(estado=0) | Q(fecha_salida__isnull=False))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["areas"]        = ["TODAS"] + [a for a, _ in Categoria.AREAS]
        ctx["situaciones"]  = ["TODAS", "P", "C"]
        ctx["estados"]      = [("activos", "Activos"), ("inactivos", "Inactivos"), ("todos", "Todos")]
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



from .forms import EmpleadoForm

class EmpleadoCreateView(LoginRequiredMixin, CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('presidencia_dashboard')
    login_url = 'login'


class EmpleadoUpdateView(LoginRequiredMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('presidencia_dashboard')
    login_url = 'login'




class EmpleadoDeleteView(LoginRequiredMixin, DeleteView):
    model = Empleado
    template_name = 'empleados/empleado_confirm_delete.html'
    success_url = reverse_lazy('presidencia_dashboard')
    login_url = 'login'

# empleados/views.py
from .forms import CalificacionForm

from datetime import date
from django.views.generic import ListView
from django.db.models import Q, OuterRef, Subquery, Value, IntegerField
from django.db.models.functions import Coalesce
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Empleado, Calificacion

class CalificacionListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'empleados/calificacion_list.html'
    context_object_name = 'empleados'
    login_url = 'login'

    def get_queryset(self):
        hoy = date.today()
        area = self.request.GET.get('area', 'PRESIDENCIA').upper()
        q = self.request.GET.get('q', '').strip()

        # 1. Empleados activos
        qs = Empleado.objects.filter(
            estado=1,
            fecha_salida__isnull=True
        )

        if area and area != 'PRESIDENCIA':
            qs = qs.filter(categoria__nombre__iexact=area)

        # 2. IDs de empleados ya calificados este mes
        empleados_con_calif = Calificacion.objects.filter(
            mes=hoy.month,
            año=hoy.year
        ).values_list('empleado_id', flat=True)

        # 3. Empleados "nuevos": fecha_ingreso = este mes/año
        empleados_nuevos = qs.filter(
            fecha_ingreso__month=hoy.month,
            fecha_ingreso__year=hoy.year
        )

        # 4. Empleados "no nuevos": fecha_ingreso < este mes/año
        empleados_no_nuevos = qs.exclude(
            id_empleado__in=empleados_nuevos.values_list('id_empleado', flat=True)
        )

        # 5. Empleados "no nuevos" SIN calificación este mes
        sin_calif = empleados_no_nuevos.exclude(id_empleado__in=empleados_con_calif)

        # 6. Solo a los empleados "no nuevos" sin calif les asignás 100 automático
        Calificacion.objects.bulk_create([
            Calificacion(
                empleado=emp,
                mes=hoy.month,
                año=hoy.year,
                calificacion=100
            ) for emp in sin_calif
        ], ignore_conflicts=True)

        # 7. El queryset a mostrar:
        # Solo empleados que YA tienen calificación este mes (no mostramos "nuevos" hasta ser calificados)
        qs = qs.filter(id_empleado__in=empleados_con_calif)

        # 8. Anotaciones de calificacion_actual y pk de calificacion
        calificacion_subq = Calificacion.objects.filter(
            empleado=OuterRef('pk'),
            mes=hoy.month,
            año=hoy.year
        ).values('calificacion')[:1]

        cal_pk_subq = Calificacion.objects.filter(
            empleado=OuterRef('pk'),
            mes=hoy.month,
            año=hoy.year
        ).values('pk')[:1]

        qs = qs.annotate(
            calificacion_actual=Coalesce(
                Subquery(calificacion_subq, output_field=IntegerField()),
                Value(100),
                output_field=IntegerField()
            ),
            cal_pk=Subquery(cal_pk_subq, output_field=IntegerField()),
        )

        # 9. Filtro de búsqueda opcional
        if q:
            partes = q.split()
            if len(partes) == 2:
                qs = qs.filter(
                    (Q(nombre__icontains=partes[0]) & Q(apellido__icontains=partes[1])) |
                    (Q(nombre__icontains=partes[1]) & Q(apellido__icontains=partes[0]))
                )
            else:
                qs = qs.filter(
                    Q(nombre__icontains=q) |
                    Q(apellido__icontains=q) |
                    Q(cuil__icontains=q) |
                    Q(dni__icontains=q)
                )

        return qs.order_by('apellido', 'nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context['areas'] = [
            'PRESIDENCIA',
            'SECRET. TÉCNICA CONTABLE',
            'PLANES DE EMERGENCIA',
            'SECRETARÍA TEC. SOCIAL',
        ]
        context['area_sel']   = self.request.GET.get('area', 'PRESIDENCIA')
        context['q']          = self.request.GET.get('q', '')
        context['mes_actual'] = hoy.month
        context['año_actual'] = hoy.year
        import calendar
        context['month_name'] = calendar.month_name[hoy.month].capitalize()
        return context



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
        return super().form_valid(form)


class CalificacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Calificacion
    form_class = CalificacionForm
    template_name = 'empleados/calificacion_form.html'
    success_url = reverse_lazy('empleados:calificacion-list')
    login_url = 'login'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object and self.object.empleado:
            ctx['empleado'] = self.object.empleado
        return ctx



from datetime import date
import calendar
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Categoria

class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'empleados/categoria_list.html'
    context_object_name = 'categorias'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['areas'] = [
            'PRESIDENCIA',
            'SECRET. TÉCNICA CONTABLE',
            'PLANES DE EMERGENCIA',
            'SECRETARÍA TEC. SOCIAL',
            # Agregá las que necesites
        ]
        context['area_sel'] = self.request.GET.get('area', '')
        hoy = date.today()
        context['mes_actual'] = hoy.month
        context['año_actual'] = hoy.year
        context['month_name'] = calendar.month_name[hoy.month].capitalize()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        area = self.request.GET.get('area')
        if area:
            qs = qs.filter(nombre__iexact=area)
        return qs



class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    fields = [
        'nombre', 'area',
        'sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12',
        'tipo_sup1', 'tipo_sup2', 'tipo_sup3', 'tipo_sup4', 'tipo_sup6', 'tipo_sup8', 'tipo_sup12',
    ]
    template_name = 'empleados/categoria_form.html'
    success_url   = reverse_lazy('empleados:categoria-list')

class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    fields = [
        'nombre', 'area',
        'sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12',
        'tipo_sup1', 'tipo_sup2', 'tipo_sup3', 'tipo_sup4', 'tipo_sup6', 'tipo_sup8', 'tipo_sup12',
    ]
    template_name = 'empleados/categoria_form.html'
    success_url   = reverse_lazy('empleados:categoria-list')


# --- OFICIOS JUDICIALES (LIST/CREATE/UPDATE/DELETE) ---
from decimal import Decimal
from django import forms as dj_forms
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q, OuterRef, Subquery, DecimalField, IntegerField, Value
from django.db.models.functions import Coalesce

from .models import Empleado, OficioJudicial

class OficioJudicialListView(LoginRequiredMixin, ListView):
    template_name = 'empleados/oficiojudicial_list.html'
    context_object_name = 'rows'
    login_url = 'login'
    paginate_by = 100

    def _periodo(self):
        now = timezone.now()
        anio = self.request.GET.get('anio')
        mes  = self.request.GET.get('mes')
        try:
            anio = int(anio) if anio else now.year
        except Exception:
            anio = now.year
        try:
            mes = int(mes) if mes else now.month
        except Exception:
            mes = now.month
        return anio, mes

    def get_queryset(self):
        anio, mes = self._periodo()

        # Subquery: último oficio del período por empleado
        oj_qs = (
            OficioJudicial.objects
            .filter(empleado_id=OuterRef('pk'), anio=anio, mes=mes)
            .order_by('-id')
        )

        # Filtro de estado en la lista (activos | inactivos | todos)
        estado = self.request.GET.get('estado', 'activos')

        qs = (
            Empleado.objects
            .order_by('apellido', 'nombre')
            .annotate(
                oj_id    = Subquery(oj_qs.values('id')[:1]),
                oj_tipo  = Subquery(oj_qs.values('tipo')[:1], output_field=IntegerField()),  # 1=monto, 2=porcentaje
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
            )
        )

        if estado == 'activos':
            qs = qs.filter(estado='1', fecha_salida__isnull=True)
        elif estado == 'inactivos':
            qs = qs.filter(Q(estado='0') | Q(fecha_salida__isnull=False))
        # 'todos' => no se filtra

        # Filtros adicionales
        empleado = self.request.GET.get('empleado')
        tipo     = self.request.GET.get('tipo')   # '1' o '2'
        area     = self.request.GET.get('area')

        if empleado:
            qs = qs.filter(
                Q(apellido__icontains=empleado) |
                Q(nombre__icontains=empleado)   |
                Q(cuil__icontains=empleado)     |
                Q(dni__icontains=empleado)
            )
        if tipo in ('1', '2'):
            qs = qs.filter(oj_id__isnull=False, oj_tipo=int(tipo))
        if area:
            qs = qs.filter(area=area)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anio, mes = self._periodo()
        ctx['anio_actual'] = anio
        ctx['mes_actual']  = mes

        ctx['f_empleado'] = self.request.GET.get('empleado', '')
        ctx['f_anio']     = anio
        ctx['f_mes']      = mes
        ctx['f_tipo']     = self.request.GET.get('tipo', '')
        ctx['f_area']     = self.request.GET.get('area', '')
        ctx['f_estado']   = self.request.GET.get('estado', 'activos')  # <- para el select

        ctx['areas'] = [
            'PRESIDENCIA',
            'SECRET. TÉCNICA CONTABLE',
            'PLANES DE EMERGENCIA',
            'SECRETARÍA TEC. SOCIAL',
        ]
        return ctx


class OficioJudicialCreateView(LoginRequiredMixin, CreateView):
    model = OficioJudicial
    template_name = 'empleados/oficiojudicial_form.html'
    login_url = 'login'

    def get_form_class(self):
        from .forms import OficioJudicialForm
        return OficioJudicialForm

    def dispatch(self, request, *args, **kwargs):
        # Exigir período actual
        now = timezone.now()
        anio = int(request.GET.get('anio') or now.year)
        mes  = int(request.GET.get('mes')  or now.month)
        if anio != now.year or mes != now.month:
            messages.error(request, 'Solo se pueden crear oficios para el período actual.')
            return redirect('empleados:oficiojudicial-list')

        # Exigir empleado
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
        # unique_together (anio, mes, empleado) => update_or_create
        cd = form.cleaned_data
        obj, created = OficioJudicial.objects.update_or_create(
            empleado=self._empleado,
            anio=self._anio,
            mes=self._mes,
            defaults={
                'tipo': cd['tipo'],
                'monto_descontar': cd.get('monto_descontar') or Decimal('0'),
                'porcentaje_descontar': cd.get('porcentaje_descontar') or Decimal('0'),
            }
        )
        messages.success(self.request, f'Oficio judicial {"creado" if created else "actualizado"} correctamente.')
        # Volver a la lista manteniendo período
        url = f"{reverse('empleados:oficiojudicial-list')}?anio={self._anio}&mes={self._mes}"
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
        now = timezone.now()
        if obj.anio != now.year or obj.mes != now.month:
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
from calendar import month_name
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

    month_name_str = month_name[mes_actual].capitalize()

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
