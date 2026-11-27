from django import forms
from django.utils import timezone

from kerberos.models.transporte import SolicitacaoTransporte

DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class SolicitacaoTransporteForm(forms.ModelForm):
    horario_preferido = forms.DateTimeField(
        input_formats=[DATETIME_LOCAL_FORMAT],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format=DATETIME_LOCAL_FORMAT,
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
        self.usuario = usuario

        # Essencial: faz o clean() do model enxergar o agendamento durante
        # o is_valid(), assim a regra "mesmo dia" vira mensagem de erro
        # no formulário em vez de exceção no save().
        self.instance.agendamento = agendamento

        self.fields["observacoes"].widget.attrs["maxlength"] = "500"

        # getattr evita RelatedObjectDoesNotExist caso o usuário não tenha endereço
        endereco = getattr(usuario, "endereco", None)
        if endereco and not self.is_bound:
            self.fields["endereco_retirada"].initial = (
                f"{endereco}, CEP {endereco.cep}"
            )

    def clean_observacoes(self):
        observacoes = (self.cleaned_data.get("observacoes") or "").strip()
        if len(observacoes) > 500:
            raise forms.ValidationError(
                "As observações podem ter no máximo 500 caracteres."
            )
        return observacoes

    def clean_horario_preferido(self):
        # Aqui fica apenas a regra do "futuro". As regras relativas ao
        # agendamento (mesmo dia e antes do horário) ficam no clean() do model,
        # que é a única fonte dessa regra.
        horario = self.cleaned_data["horario_preferido"]
        if horario <= timezone.now():
            raise forms.ValidationError("Informe um horário futuro.")
        return horario


class GerenciarTransporteForm(forms.ModelForm):
    horario_confirmado = forms.DateTimeField(
        input_formats=[DATETIME_LOCAL_FORMAT],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format=DATETIME_LOCAL_FORMAT,
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