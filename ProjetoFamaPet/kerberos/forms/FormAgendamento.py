from datetime import date
from django import forms
from ..models import Agendamento

class AgendamentoForm(forms.ModelForm):
    data = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Agendamento
        fields = ["pet", "data", "servicos"]
        widgets = {
            "servicos": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        if usuario:
            self.fields["pet"].queryset = models.Pet.objects.filter(usuario=usuario)