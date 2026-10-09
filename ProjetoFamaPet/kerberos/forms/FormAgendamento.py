from django import forms
from kerberos.models.agendamento import Agendamento
from kerberos.models.pet import Pet
from kerberos.models.servico import Servico


class AgendamentoForm(forms.ModelForm):
    data = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Data e Horário"
    )

    servicos = forms.ModelMultipleChoiceField(
        queryset=Servico.objects.filter(ativo=True),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Serviços Desejados"
    )

    class Meta:
        model = Agendamento
        fields = ["pet", "data"]

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

        # 1. Regra de Negócio por Perfil
        if usuario and getattr(usuario, "is_authenticated", False):
            if usuario.is_staff:
                # Administrador/Staff pode selecionar QUALQUER pet cadastrado no petshop
                self.fields["pet"].queryset = Pet.objects.all().select_related("usuario")
                # Exibe o nome do Tutor ao lado do nome do Pet para o Admin não se confundir
                self.fields["pet"].label_from_instance = (
                    lambda obj: f"{obj.nome} (Tutor: {obj.usuario.nome})"
                )
            else:
                # Cliente comum só seleciona seus próprios pets
                self.fields["pet"].queryset = Pet.objects.filter(usuario=usuario)
        else:
            self.fields["pet"].queryset = Pet.objects.none()

        # 2. Se for edição, pré-carrega os serviços selecionados
        if self.instance and self.instance.pk:
            self.fields["servicos"].initial = [
                item.servico_id for item in self.instance.itens.all()
            ]

    def clean_pet(self):
        pet = self.cleaned_data.get("pet")
        # Apenas valida se o pet pertence ao usuário caso NÃO seja admin
        if self.usuario and not self.usuario.is_staff and pet and pet.usuario != self.usuario:
            raise forms.ValidationError("O pet selecionado não pertence à sua conta.")
        return pet