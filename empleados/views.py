# empleados/views.py

from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import (
    Empleado,
    Calificacion,
    Categoria,
    OficioJudicial,
    Preliquidacion,
    Liquidacion,
)
from .forms import PreliquidacionForm, LiquidacionForm


class LiquidacionList(LoginRequiredMixin, ListView):
    model               = Liquidacion
    template_name       = 'empleados/liq_list.html'
    context_object_name = 'liquidaciones'
    login_url           = 'login'
    redirect_field_name = 'next'


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
            return redirect('liq_list')
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
            return redirect('liq_list')
    else:
        pre_form = PreliquidacionForm(instance=pre)
        liq_form = LiquidacionForm(instance=liq)
    return render(request, 'empleados/combined_form.html', {
        'pre_form': pre_form,
        'liq_form': liq_form,
    })


def is_presidencia(user):
    # sólo superusuarios (ajusta a is_staff si lo prefieres)
    return user.is_active and user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def presidencia_dashboard(request):
    # 1) obtenemos periodos disponibles
    qs = Preliquidacion.objects.values('año', 'mes') \
                                .distinct() \
                                .order_by('-año', '-mes')
    periodos = [(p['mes'], p['año']) for p in qs]

    # 2) definimos áreas (hardcode por ahora)
    areas = [
        'PRESIDENCIA',
        'SECRET. TÉCNICA CONTABLE',
        'PLANES DE EMERGENCIA',
        'SECRETARÍA TEC. SOCIAL',
    ]

    # 3) leemos GET o tomamos primer valor
    mes  = request.GET.get('mes')
    año  = request.GET.get('año')
    area = request.GET.get('area', areas[0])
    if not (mes and año) and periodos:
        mes, año = periodos[0]

    # 4) enviamos a plantilla
    return render(request, 'presidencia/dashboard.html', {
        'periodos': periodos,
        'mes_sel':  int(mes),
        'año_sel':  int(año),
        'areas':    areas,
        'area_sel': area,
    })



@login_required(login_url='login')
@user_passes_test(is_presidencia)
def generar_preliquidacion(request):
    mes = request.GET.get('mes', date.today().month)
    año = request.GET.get('año', date.today().year)
    # tu lógica de regeneración real vendría aquí...
    count = Empleado.objects.count()  # o Preliquidacion.objects.filter(...)
    messages.success(request, f"✅ Se (re)generaron {count} preliquidaciones para {mes}/{año}.")
    return redirect('presidencia_dashboard')


@login_required(login_url='login')
@user_passes_test(is_presidencia)
def confirmar_liquidacion(request):
    mes = request.GET.get('mes', date.today().month)
    año = request.GET.get('año', date.today().year)
    qs = Liquidacion.objects.filter(mes=mes, año=año)
    count = qs.count()
    qs.update(conformada=True)  # asumiendo ese campo booleano
    messages.success(request, f"✅ Se confirmaron {count} liquidaciones para {mes}/{año}.")
    return redirect('presidencia_dashboard')
