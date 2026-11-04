from django import forms

from kerberos.models.horario import ExcecaoHorario


class HorarioDiaForm(forms.Form):
    fechado = forms.BooleanField(
        label="Fechado",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    hora_abertura = forms.TimeField(
        label="Abre",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
    )
    hora_fechamento = forms.TimeField(
        label="Fecha",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
    )
    pausa_inicio = forms.TimeField(
        label="Início da pausa",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
    )
    pausa_fim = forms.TimeField(
        label="Fim da pausa",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("fechado"):
            return cleaned_data

        inicio = cleaned_data.get("hora_abertura")
        fim = cleaned_data.get("hora_fechamento")
        pausa_inicio = cleaned_data.get("pausa_inicio")
        pausa_fim = cleaned_data.get("pausa_fim")

        if not inicio:
            self.add_error("hora_abertura", "Informe a abertura ou marque o dia como fechado.")
        if not fim:
            self.add_error("hora_fechamento", "Informe o fechamento ou marque o dia como fechado.")
        if inicio and fim and inicio >= fim:
            self.add_error("hora_fechamento", "O fechamento deve ser após a abertura.")
        if bool(pausa_inicio) != bool(pausa_fim):
            self.add_error("pausa_fim", "Informe os dois horários da pausa.")
        if inicio and fim and pausa_inicio and pausa_fim:
            if not inicio < pausa_inicio < pausa_fim < fim:
                self.add_error("pausa_fim", "A pausa deve ficar dentro do expediente.")
        return cleaned_data


class ExcecaoHorarioForm(forms.ModelForm):
    class Meta:
        model = ExcecaoHorario
        fields = (
            "data",
            "fechado",
            "hora_abertura",
            "hora_fechamento",
            "pausa_inicio",
            "pausa_fim",
            "motivo",
        )
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fechado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hora_abertura": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "hora_fechamento": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "pausa_inicio": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "pausa_fim": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "motivo": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("fechado"):
            for campo in ("hora_abertura", "hora_fechamento", "pausa_inicio", "pausa_fim"):
                cleaned_data[campo] = None
        return cleaned_data