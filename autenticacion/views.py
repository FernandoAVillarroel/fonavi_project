# autenticacion/views.py

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class MyLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Si viene ?next=... lo respeta,
        si no, redirige al dashboard de Presidencia.
        """
        return self.get_redirect_url() or reverse_lazy('presidencia_dashboard')
