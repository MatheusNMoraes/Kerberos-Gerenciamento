from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils import timezone


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='E-mail')


class login(LoginView):
    template_name = 'login/login.html'
    authentication_form = EmailAuthenticationForm
    max_login_attempts = 5
    lockout_minutes = 5

    def dispatch(self, request, *args, **kwargs):
        lock_until = request.session.get('login_lock_until')
        if lock_until:
            if timezone.now().timestamp() < float(lock_until):
                remaining = max(0, int(float(lock_until) - timezone.now().timestamp()))
                context = self.get_context_data()
                context['custom_error'] = (
                    f'Muitas tentativas de login. Tente novamente em {remaining} segundos.'
                )
                messages.error(
                    request,
                    f'Muitas tentativas de login. Tente novamente em {remaining} segundos.'
                )
                return self.render_to_response(context)
            request.session.pop('login_lock_until', None)
            request.session['login_attempts'] = 0
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.pop('login_attempts', None)
        self.request.session.pop('login_lock_until', None)
        return super().form_valid(form)

    def form_invalid(self, form):
        attempts = self.request.session.get('login_attempts', 0) + 1
        self.request.session['login_attempts'] = attempts

        remaining = self.max_login_attempts - attempts
        custom_error = None

        if attempts >= self.max_login_attempts:
            lock_until = timezone.now() + timedelta(minutes=self.lockout_minutes)
            self.request.session['login_lock_until'] = lock_until.timestamp()
            self.request.session['login_attempts'] = 0
            custom_error = (
                'Muitas tentativas inválidas. Sua conta foi temporariamente bloqueada por 5 minutos.'
            )
        elif remaining > 0:
            custom_error = (
                f'Credenciais inválidas. Restam {remaining} tentativas antes do bloqueio.'
            )

        if custom_error:
            messages.error(self.request, custom_error)

        context = self.get_context_data(form=form)
        context['custom_error'] = custom_error
        return self.render_to_response(context, status=400)

    def get_success_url(self):
        user = self.request.user
        if user.is_administrador:
            return reverse_lazy('listar_clientes')
        return reverse_lazy('agendamentos')