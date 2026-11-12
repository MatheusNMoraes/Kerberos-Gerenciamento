from django import forms
from django.utils import timezone

from kerberos.models.transporte import SolicitacaoTransporte


class SolicitacaoTransporteForm(forms.ModelForm):
    horario_preferido = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        label="Horário preferido para retirada",
    )

    class Meta:
        model = SolicitacaoTransporte
        fields = [
            "endereco_retirada",
            "horario_preferido",
            "observacoes",
            "politica_aceita",
        ]
        widgets = {
            "endereco_retirada": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "maxlength": 500}
            ),
            "observacoes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "politica_aceita": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "endereco_retirada": "Endereço de retirada",
            "observacoes": "Observações para a equipe",
            "politica_aceita": "Li e concordo com a política de transporte.",
        }

    def __init__(self, *args, agendamento, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.agendamento = agendamento

        endereco = usuario.endereco
        if endereco and not self.is_bound:
            self.fields["endereco_retirada"].initial = (
                f"{endereco}, CEP {endereco.cep}"
            )

    def clean_horario_preferido(self):
        horario = self.cleaned_data["horario_preferido"]
        if horario <= timezone.now():
            raise forms.ValidationError("Informe um horário futuro.")
        if horario >= self.agendamento.data:
            raise forms.ValidationError(
                "A retirada precisa ocorrer antes do horário do agendamento."
            )
        return horario


class GerenciarTransporteForm(forms.ModelForm):
    horario_confirmado = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        required=False,
        label="Horário confirmado",
    )

    class Meta:
        model = SolicitacaoTransporte
        fields = ["status", "horario_confirmado", "taxa"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "taxa": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
        }
        labels = {"taxa": "Taxa do transporte"}
