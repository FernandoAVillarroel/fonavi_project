from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import Liquidacion
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
