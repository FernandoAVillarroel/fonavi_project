# empleados/views_planillas.py
import os
from datetime import date
from calendar import monthrange
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.staticfiles import finders
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.paginator import Paginator

try:
    from .models import LiquidacionPeriodo
except Exception:
    LiquidacionPeriodo = None

from .models import Liquidacion
from .models import Liquidacion, OficioJudicial


def is_presidencia(user):
    return user.is_authenticated and user.is_staff


def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        return result
    path = uri.replace(settings.STATIC_URL, "")
    if getattr(settings, "STATIC_ROOT", None):
        return os.path.join(str(settings.STATIC_ROOT), path)
    return path


def _period_bounds(anio: int, mes: int):
    """Primer y último día del mes (incluidos)."""
    start = date(anio, mes, 1)
    end = date(anio, mes, monthrange(anio, mes)[1])
    return start, end


@login_required(login_url="login")
@user_passes_test(is_presidencia)
def ver_liquidaciones_confirmadas(request):
    mes  = int(request.GET.get("mes",  date.today().month))
    año  = int(request.GET.get("año",  date.today().year))
    tipo = request.GET.get("tipo", "todos")
    periodo_str = f"{año:04d}-{mes:02d}"

    ini = date(año, mes, 1)
    fin = date(año, mes, monthrange(año, mes)[1])

    if LiquidacionPeriodo is not None:
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        if lp and lp.estado != getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA"):
            messages.info(request, f"El período {periodo_str} no está CONFIRMADO. Se muestran datos informativos.")

    qs_base = (Liquidacion.objects
               .filter(mes=mes, año=año, conformada=True)
               .filter(empleado__fecha_ingreso__lte=fin)
               .filter(Q(empleado__fecha_salida__isnull=True) | Q(empleado__fecha_salida__gte=ini)))

    if tipo == "permanentes":
        qs, title = qs_base.filter(situacion="P"), "Permanentes"
    elif tipo == "contratados":
        qs, title = qs_base.filter(situacion="C"), "Contratados"
    else:
        qs, title = qs_base, "Todos"

    totales_col = qs.aggregate(
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
    
    for k, v in totales_col.items():
        if v is None:
            totales_col[k] = Decimal('0')

    tot = {
        'bruto': totales_col.get('bruto', Decimal('0')),
        'liquido': totales_col.get('liquido', Decimal('0')),
    }

    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    ctx = {
        "PERIODO_ACTUAL": periodo_str,
        "mes_sel": mes,
        "año_sel": año,
        "month_name": MONTH_NAMES.get(mes, str(mes)),
        "tipo": tipo,
        "title": title,
        "liqs": qs.order_by("empleado__apellido", "empleado__nombre"),
        "tot": tot,
        "totales_col": totales_col,
        "total_planillas": qs.count(),
    }
    return render(request, "presidencia/planillas_confirmadas.html", ctx)

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def exportar_liquidaciones_pdf(request):
    mes  = int(request.GET.get("mes",  date.today().month))
    año  = int(request.GET.get("año",  date.today().year))
    tipo = request.GET.get("tipo", "todos")
    periodo_str = f"{año:04d}-{mes:02d}"
    ini, fin = _period_bounds(año, mes)

    qs = (Liquidacion.objects
          .filter(mes=mes, año=año)
          .filter(empleado__fecha_ingreso__lte=fin)
          .filter(Q(empleado__fecha_salida__isnull=True) | Q(empleado__fecha_salida__gte=ini))
          .filter(empleado__estado=1))

    try:
        qs.model._meta.get_field("conformada")
        qs = qs.filter(conformada=True)
    except Exception:
        pass

    if tipo == "permanentes":
        qs, title = qs.filter(situacion="P"), "Permanentes"
    elif tipo == "contratados":
        qs, title = qs.filter(situacion="C"), "Contratados"
    else:
        title = "Todos"

    agg = qs.aggregate(
        basico=Sum("basico"),
        importe_antiguedad=Sum("importe_antiguedad"),
        importe_titulo=Sum("importe_titulo"),
        basico_total=Sum("basico_total"),
        supl1=Sum("supl1"),
        supl2=Sum("supl2"),
        supl3=Sum("supl3"),
        supl4=Sum("supl4"),
        supl6=Sum("supl6"),
        supl8=Sum("supl8"),
        supl12=Sum("supl12"),
        total_suplementos=Sum("total_suplementos"),
        bruto=Sum("bruto"),
        jubilacion=Sum("jubilacion"),
        obra_social=Sum("obra_social"),
        oficio_judicial=Sum("oficio_judicial"),
        total_descuentos=Sum("total_descuentos"),
        liquido=Sum("liquido"),
    )
    totales = {k: (v or Decimal("0")) for k, v in agg.items()}

    # Diccionario de meses
    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # Agrupar liquidaciones por oficina con subtotales
    from itertools import groupby

    planillas_ordenadas = qs.order_by("oficina_nombre", "empleado__apellido", "empleado__nombre")
    oficinas_agrupadas = []

    for oficina, liquidaciones in groupby(planillas_ordenadas, key=lambda x: x.oficina_nombre):
        liqs_list = list(liquidaciones)
        
        # Calcular subtotales de la oficina
        subtotal = {
            'basico': sum((liq.basico or Decimal('0')) for liq in liqs_list),
            'importe_antiguedad': sum((liq.importe_antiguedad or Decimal('0')) for liq in liqs_list),
            'importe_titulo': sum((liq.importe_titulo or Decimal('0')) for liq in liqs_list),
            'basico_total': sum((liq.basico_total or Decimal('0')) for liq in liqs_list),
            'supl1': sum((liq.supl1 or Decimal('0')) for liq in liqs_list),
            'supl2': sum((liq.supl2 or Decimal('0')) for liq in liqs_list),
            'supl3': sum((liq.supl3 or Decimal('0')) for liq in liqs_list),
            'supl4': sum((liq.supl4 or Decimal('0')) for liq in liqs_list),
            'supl6': sum((liq.supl6 or Decimal('0')) for liq in liqs_list),
            'supl8': sum((liq.supl8 or Decimal('0')) for liq in liqs_list),
            'supl12': sum((liq.supl12 or Decimal('0')) for liq in liqs_list),
            'total_suplementos': sum((liq.total_suplementos or Decimal('0')) for liq in liqs_list),
            'bruto': sum((liq.bruto or Decimal('0')) for liq in liqs_list),
            'jubilacion': sum((liq.jubilacion or Decimal('0')) for liq in liqs_list),
            'obra_social': sum((liq.obra_social or Decimal('0')) for liq in liqs_list),
            'oficio_judicial': sum((liq.oficio_judicial or Decimal('0')) for liq in liqs_list),
            'total_descuentos': sum((liq.total_descuentos or Decimal('0')) for liq in liqs_list),
            'liquido': sum((liq.liquido or Decimal('0')) for liq in liqs_list),
            'count': len(liqs_list)
        }
        
        oficinas_agrupadas.append({
            'nombre': oficina or 'Sin oficina',
            'liquidaciones': liqs_list,
            'subtotal': subtotal
        })

    ctx = {
        "PERIODO_ACTUAL": periodo_str,
        "mes_sel": mes,
        "año_sel": año,
        "month_name": MONTH_NAMES.get(mes, str(mes)),
        "tipo": tipo,
        "title": title,
        "oficinas_agrupadas": oficinas_agrupadas,
        "total_planillas": qs.count(),
        "totales": totales,
    }

    template = get_template("presidencia/planillas_confirmadas_pdf.html")
    html = template.render(ctx)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), dest=result,
                            link_callback=link_callback, encoding="utf-8")
    if pdf.err:
        return HttpResponse(html)

    resp = HttpResponse(result.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="liquidaciones_{periodo_str}.pdf"'
    return resp


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def contribuciones_patronales(request):
    """Vista HTML de contribuciones patronales con paginación"""
    mes = int(request.GET.get('mes', date.today().month))
    año = int(request.GET.get('año', date.today().year))
    tipo = request.GET.get('tipo', 'todos')
    
    liqs = Liquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True,
    )
    
    if tipo == 'contratados':
        liqs = liqs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        liqs = liqs.filter(situacion='P')
        title = 'Permanentes'
    else:
        title = 'Todos los Empleados'
    
    # Calcular totales ANTES de paginar
    total_bruto = Decimal('0')
    total_jubilacion = Decimal('0')
    total_obra_social = Decimal('0')
    
    contribuciones_todas = []
    for liq in liqs.order_by('empleado__apellido', 'empleado__nombre'):
        bruto = liq.bruto or Decimal('0')
        contrib_jub = (bruto * Decimal('10.17')) / Decimal('100')
        contrib_os = (bruto * Decimal('6')) / Decimal('100')
        total_contrib = contrib_jub + contrib_os
        
        contribuciones_todas.append({
            'empleado': liq.empleado,
            'bruto': bruto,
            'contrib_jubilacion': contrib_jub,
            'contrib_obra_social': contrib_os,
            'total_contribuciones': total_contrib,
        })
        
        total_bruto += bruto
        total_jubilacion += contrib_jub
        total_obra_social += contrib_os
    
    total_general = total_jubilacion + total_obra_social
    
    # Paginación
    paginator = Paginator(contribuciones_todas, 25)  # 25 por página
    page_number = request.GET.get('page')
    contribuciones_pagina = paginator.get_page(page_number)
    
    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    return render(request, 'presidencia/contribuciones_patronales.html', {
        'mes_sel': mes,
        'año_sel': año,
        'month_name': MONTH_NAMES.get(mes, str(mes)),
        'tipo': tipo,
        'title': title,
        'contribuciones': contribuciones_pagina,  # Paginado
        'total_bruto': total_bruto,
        'total_jubilacion': total_jubilacion,
        'total_obra_social': total_obra_social,
        'total_general': total_general,
        'count': len(contribuciones_todas),
        'is_paginated': paginator.num_pages > 1,
        'page_obj': contribuciones_pagina,
    })


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def exportar_contribuciones_pdf(request):
    """Exportar contribuciones patronales a PDF"""
    mes = int(request.GET.get('mes', date.today().month))
    año = int(request.GET.get('año', date.today().year))
    tipo = request.GET.get('tipo', 'todos')
    
    liqs = Liquidacion.objects.filter(
        mes=mes,
        año=año,
        empleado__estado=1,
        empleado__fecha_salida__isnull=True,
    )
    
    if tipo == 'contratados':
        liqs = liqs.filter(situacion='C')
        title = 'Contratados'
    elif tipo == 'permanentes':
        liqs = liqs.filter(situacion='P')
        title = 'Permanentes'
    else:
        title = 'Todos los Empleados'
    
    contribuciones = []
    total_bruto = Decimal('0')
    total_jubilacion = Decimal('0')
    total_obra_social = Decimal('0')
    
    for liq in liqs.order_by('empleado__apellido', 'empleado__nombre'):
        bruto = liq.bruto or Decimal('0')
        contrib_jub = (bruto * Decimal('10.17')) / Decimal('100')
        contrib_os = (bruto * Decimal('6')) / Decimal('100')
        total_contrib = contrib_jub + contrib_os
        
        contribuciones.append({
            'empleado': liq.empleado,
            'bruto': bruto,
            'contrib_jubilacion': contrib_jub,
            'contrib_obra_social': contrib_os,
            'total_contribuciones': total_contrib,
        })
        
        total_bruto += bruto
        total_jubilacion += contrib_jub
        total_obra_social += contrib_os
    
    total_general = total_jubilacion + total_obra_social
    
    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    template = get_template('presidencia/contribuciones_patronales_pdf.html')
    html = template.render({
        'mes_sel': mes,
        'año_sel': año,
        'month_name': MONTH_NAMES.get(mes, str(mes)),
        'tipo': tipo,
        'title': title,
        'contribuciones': contribuciones,
        'total_bruto': total_bruto,
        'total_jubilacion': total_jubilacion,
        'total_obra_social': total_obra_social,
        'total_general': total_general,
        'count': len(contribuciones),
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contribuciones_patronales_{mes}_{año}_{tipo}.pdf"'
    
    pisa_status = pisa.CreatePDF(
        src=BytesIO(html.encode('utf-8')),
        dest=response,
        link_callback=link_callback,
    )
    
    if pisa_status.err:
        return HttpResponse("Error generando el PDF", status=500)
    
    return response



@login_required(login_url="login")
@user_passes_test(is_presidencia)
def generar_txt_banco(request):
    """
    Genera archivo TXT formato DGISE (29 caracteres) para FONAVI.
    Formato: PLANTA(1) + CONTROL(8) + CODIGO(3) + IMPORTE(10) + CUOTAS(2) + NOVEDAD(1) + MES(2) + AÑO(2)
    
    Campos fijos:
    - CODIGO: 508 (FONAVI)
    - CUOTAS: 01 (mensual)
    - NOVEDAD: 2 (alta)
    """
    # 1. Obtener parámetros de la URL
    mes = int(request.GET.get("mes", date.today().month))
    año = int(request.GET.get("año", date.today().year))
    tipo = request.GET.get("tipo", "todos")
    
    # 2. Buscar liquidaciones del período
    liquidaciones = Liquidacion.objects.filter(
        año=año,
        mes=mes,
        empleado__estado=1,  # Solo activos
        empleado__fecha_salida__isnull=True
    ).select_related('empleado')
    
    # 3. Filtrar por tipo de planta si es necesario
    if tipo == "permanentes":
        liquidaciones = liquidaciones.filter(situacion='P')
    elif tipo == "contratados":
        liquidaciones = liquidaciones.filter(situacion='C')
    
    # 4. Verificar que haya liquidaciones
    if not liquidaciones.exists():
        messages.warning(request, f"No hay liquidaciones para generar TXT en {mes:02d}/{año}.")
        return redirect("empleados:ver_liquidacion_periodo")
    
    # 5. Generar líneas del archivo
    lineas = []
    errores = []
    
    for liq in liquidaciones:
        emp = liq.empleado
        
        # === CAMPO 1: PLANTA (1 carácter) ===
        planta = liq.situacion or 'P'
        
        # === CAMPO 2: CONTROL - DNI (8 caracteres) ===
        dni = str(emp.dni or '').replace('.', '').replace('-', '').strip()
        if not dni or not dni.isdigit():
            errores.append(f"{emp}: DNI inválido o vacío")
            continue
        control = dni.zfill(8)[:8]  # Rellenar con ceros a la izquierda, máximo 8
        
        # === CAMPO 3: CODIGO - FONAVI (3 caracteres) ===
        codigo = "508"
        
        # === CAMPO 4: IMPORTE (10 caracteres) - líquido en centavos ===
        liquido = liq.liquido or Decimal('0')
        
        # Convertir a centavos (multiplicar × 100) y formatear
        monto_centavos = int(liquido * 100)
        if monto_centavos <= 0:
            errores.append(f"{emp}: Líquido $0 (no se incluye en el archivo)")
            continue
        importe = str(monto_centavos).zfill(10)[:10]
        
        # === CAMPO 5: CUOTAS (2 caracteres) ===
        cuotas = "01"  # Mensual
        
        # === CAMPO 6: NOVEDAD (1 carácter) ===
        novedad = "2"  # Alta
        
        # === CAMPO 7: MES (2 caracteres) ===
        mes_str = str(mes).zfill(2)
        
        # === CAMPO 8: AÑO (2 caracteres) - últimos 2 dígitos ===
        año_str = str(año)[-2:]
        
        # === CONSTRUIR LÍNEA COMPLETA (29 caracteres) ===
        linea = f"{planta}{control}{codigo}{importe}{cuotas}{novedad}{mes_str}{año_str}"
        
        # Validar longitud
        if len(linea) != 29:
            errores.append(f"{emp}: Línea inválida (longitud {len(linea)} en lugar de 29)")
            continue
        
        lineas.append(linea)
    
    # 6. Mostrar errores si los hubo
    if errores:
        for error in errores[:5]:  # Mostrar máximo 5 errores
            messages.warning(request, error)
        if len(errores) > 5:
            messages.warning(request, f"... y {len(errores) - 5} error(es) más")
    
    # 7. Verificar que haya al menos una línea válida
    if not lineas:
        messages.error(request, "No se pudo generar ninguna línea válida para el archivo TXT.")
        return redirect("empleados:ver_liquidacion_periodo")
    
    # 8. Generar nombre del archivo: N508mmaa.TXT
    nombre_archivo = f"N508{mes:02d}{str(año)[-2:]}.TXT"
    
    # 9. Crear contenido del archivo
    contenido = "\n".join(lineas)
    
    # 10. Crear respuesta HTTP para descargar el archivo
    response = HttpResponse(contenido, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    
    # 11. Mensaje de éxito
    messages.success(request, f"✓ Archivo {nombre_archivo} generado correctamente con {len(lineas)} registro(s)")
    
    return response