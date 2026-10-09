from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class login(LoginView):
    template_name = 'login/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return reverse_lazy('listar_clientes')
        else:
            return reverse_lazy('agendamentos')