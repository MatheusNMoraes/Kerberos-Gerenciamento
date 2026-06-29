from django.db import models

class Usuario(models.Model):
    nome = models.CharField(max_length=100)

class Pet(models.Model):
    nome = models.CharField(max_length=100)

class Agendamento(models.Model):
    nome = models.CharField(max_length=100)


class Endereco(models.Model):
    rua = models.CharField(max_length=100)


class Servico(models.Model):
    status = models.CharField(max_length=30)
