# empleados/views_planillas.py
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
from django.shortcuts import render
from django.template.loader import get_template

try:
    from .models import LiquidacionPeriodo
except Exception:
    LiquidacionPeriodo = None

from .models import Liquidacion


def is_presidencia(user):
    return user.is_authenticated and user.is_staff


def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        return result
    path = uri.replace(settings.STATIC_URL, "")
    if getattr(settings, "STATIC_ROOT", None):
        import os
        return os.path.join(str(settings.STATIC_ROOT), path)
    return path


def _period_bounds(anio: int, mes: int):
    """Primer y último día del mes (incluidos)."""
    start = date(anio, mes, 1)
    end = date(anio, mes, monthrange(anio, mes)[1])
    return start, end


from datetime import date
from calendar import monthrange
from decimal import Decimal
from django.db.models import Sum, Q

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def ver_liquidaciones_confirmadas(request):
    mes  = int(request.GET.get("mes",  date.today().month))
    año  = int(request.GET.get("año",  date.today().year))
    tipo = request.GET.get("tipo", "todos")  # 'todos' | 'permanentes' | 'contratados'
    periodo_str = f"{año:04d}-{mes:02d}"

    # Rangos del mes
    ini = date(año, mes, 1)
    fin = date(año, mes, monthrange(año, mes)[1])

    # Aviso si el período no está confirmado
    if LiquidacionPeriodo is not None:
        lp = LiquidacionPeriodo.objects.filter(periodo=periodo_str).first()
        if lp and lp.estado != getattr(LiquidacionPeriodo, "ESTADO_CONFIRMADA", "CONFIRMADA"):
            messages.info(request, f"El período {periodo_str} no está CONFIRMADO. Se muestran datos informativos.")

    # Base del período
    qs_base = (Liquidacion.objects
               .filter(mes=mes, año=año)
               # activos en el período por fechas (sin forzar tipo del campo 'estado')
               .filter(empleado__fecha_ingreso__lte=fin)
               .filter(Q(empleado__fecha_salida__isnull=True) | Q(empleado__fecha_salida__gte=ini)))

    # Preferimos 'conformada=True' si existe y hay filas; si no, usamos la base
    qs = qs_base
    try:
        qs.model._meta.get_field("conformada")
        qs_conf = qs_base.filter(conformada=True)
        if qs_conf.exists():
            qs = qs_conf
    except Exception:
        pass

    # Filtro por vínculo
    if tipo == "permanentes":
        qs, title = qs.filter(situacion="P"), "Permanentes"
    elif tipo == "contratados":
        qs, title = qs.filter(situacion="C"), "Contratados"
    else:
        title = "Todos"

    agg = qs.aggregate(
        bruto=Sum("bruto"),
        jubilacion=Sum("jubilacion"),
        obra_social=Sum("obra_social"),
        oficio_judicial=Sum("oficio_judicial"),
        liquido=Sum("liquido"),
    )
    totales = {k: (v or Decimal("0")) for k, v in agg.items()}

    ctx = {
        "PERIODO_ACTUAL": periodo_str,
        "mes_sel": mes, "año_sel": año,
        "tipo": tipo, "title": title,
        "planillas": qs.order_by("empleado__apellido", "empleado__nombre"),
        "total_planillas": qs.count(),
        "totales": totales,
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
          .filter(
              empleado__fecha_ingreso__lte=fin
          ).filter(
              Q(empleado__fecha_salida__isnull=True) | Q(empleado__fecha_salida__gte=ini)
          ).filter(
              Q(empleado__estado=1) | Q(empleado__estado=True) | Q(empleado__estado='A')
          ))

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
        bruto=Sum("bruto"),
        jubilacion=Sum("jubilacion"),
        obra_social=Sum("obra_social"),
        oficio_judicial=Sum("oficio_judicial"),
        liquido=Sum("liquido"),
    )
    totales = {k: (v or Decimal("0")) for k, v in agg.items()}

    ctx = {
        "PERIODO_ACTUAL": periodo_str,
        "tipo": tipo, "title": title,
        "planillas": qs.order_by("empleado__apellido", "empleado__nombre"),
        "total_planillas": qs.count(),
        "totales": totales,
    }

    template = get_template("presidencia/planillas_confirmadas_pdf.html")
    html = template.render(ctx)

    from xhtml2pdf import pisa
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), dest=result,
                            link_callback=link_callback, encoding="utf-8")
    if pdf.err:
        return HttpResponse(html)

    resp = HttpResponse(result.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="liquidaciones_{periodo_str}.pdf"'
    return resp
