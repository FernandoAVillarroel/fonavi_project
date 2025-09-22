# empleados/views_empleado.py
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DeleteView
from .models import Empleado
from .utils import RequireSelectedPeriodCurrentMixin  # asegúrate del import correcto

class EmpleadoUpdateView(LoginRequiredMixin, RequireSelectedPeriodCurrentMixin, UpdateView):
    model = Empleado
    fields = [
        "apellido", "nombre", "cuil", "dni",
        "categoria", "oficina", "situacion", "estado",
        "fecha_ingreso", "fecha_salida", "area"
    ]
    template_name = "empleados/empleado_form.html"
    redirect_name = 'empleados:empleado-list'
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy(self.redirect_name)

class EmpleadoDeleteView(LoginRequiredMixin, RequireSelectedPeriodCurrentMixin, DeleteView):
    model = Empleado
    template_name = "empleados/empleado_confirm_delete.html"
    redirect_name = 'empleados:empleado-list'
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy(self.redirect_name)
