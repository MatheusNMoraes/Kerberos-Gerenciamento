from django.db import models


class Endereco(models.Model):
    rua = models.CharField(max_length=100)
    numero = models.IntegerField()
    bairro = models.CharField(max_length=100)
    cep = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.rua}, {self.numero}"


class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)

    endereco = models.ForeignKey(Endereco, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class Pet(models.Model):

    PORTE_CHOICES = [
        ("Pequeno", "Pequeno"),
        ("Médio", "Médio"),
        ("Grande", "Grande"),
    ]

    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField()
    especie = models.CharField(max_length=50)
    raca = models.CharField(max_length=50)
    porte = models.CharField(max_length=20, choices=PORTE_CHOICES)
    observacao = models.TextField(blank=True)

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nome


class Agendamento(models.Model):

    STATUS_CHOICES = [
        ("Pendente", "Pendente"),
        ("Confirmado", "Confirmado"),
        ("Concluído", "Concluído"),
        ("Cancelado", "Cancelado"),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="agendamentos")
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="agendamentos")
    data = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pendente")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    servicos = models.ManyToManyField(Servico, through="ServicoAgendamento")

    def __str__(self):
        return f"{self.pet.nome} - {self.data.strftime('%d/%m/%Y %H:%M')}"


class ServicoAgendamento(models.Model):
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["agendamento", "servico"],
                name="unique_servico_agendamento"
            )
        ]

    def __str__(self):
        return f"{self.agendamento} - {self.servico}"
