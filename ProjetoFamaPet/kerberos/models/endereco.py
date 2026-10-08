from django.db import models
from django.core.validators import RegexValidator


class Endereco(models.Model):
    cep_validator = RegexValidator(
        regex=r'^\d{5}-?\d{3}$',
        message="CEP inválido. Use o formato 00000-000 ou apenas números."
    )

    ESTADOS_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ]

    logradouro = models.CharField("Logradouro/Rua", max_length=150)
    numero = models.CharField("Número", max_length=20, default="S/N", help_text="Digite o número ou S/N")
    complemento = models.CharField("Complemento", max_length=100, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100)
    cidade = models.CharField("Cidade", max_length=100, default="Não informada")
    uf = models.CharField("UF", max_length=2, choices=ESTADOS_CHOICES, default="SP")
    cep = models.CharField("CEP", max_length=9, validators=[cep_validator])

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"
        ordering = ['-id']

    def __str__(self):
        comp = f" - {self.complemento}" if self.complemento else ""
        return f"{self.logradouro}, {self.numero}{comp} - {self.bairro}, {self.cidade}/{self.uf}"

    def clean(self):
        """Higienização de dados antes da validação."""
        if self.cep:
            # Remove caracteres não numéricos para padronização
            cep_limpo = ''.join(filter(str.isdigit, self.cep))
            if len(cep_limpo) == 8:
                self.cep = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        
        if self.uf:
            self.uf = self.uf.upper()

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)