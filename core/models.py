from django.db import models


class ClassificacaoVencimento(models.TextChoices):
    VENCIDO = "VENCIDO", "Vencido"
    CRITICO = "CRITICO", "Critico"
    ATENCAO = "ATENCAO", "Atencao"
    NORMAL = "NORMAL", "Normal"


class AnaliseLote(models.Model):
    codigo_produto = models.CharField(max_length=100)
    lote = models.CharField(max_length=100)
    data_validade = models.DateField()
    dias_restantes = models.IntegerField()
    classificacao = models.CharField(
        max_length=20,
        choices=ClassificacaoVencimento.choices,
    )
    data_analise = models.DateTimeField(auto_now_add=True)
    origem = models.CharField(max_length=100)

    class Meta:
        ordering = ["-data_analise", "codigo_produto", "lote"]
        indexes = [
            models.Index(fields=["lote", "codigo_produto"]),
            models.Index(fields=["classificacao", "data_analise"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["lote", "codigo_produto"],
                name="unique_analise_lote_codigo_produto",
            )
        ]
        verbose_name = "Analise de lote"
        verbose_name_plural = "Analises de lotes"

    def __str__(self) -> str:
        return f"{self.codigo_produto} / {self.lote} - {self.classificacao}"


class Alerta(models.Model):
    analise_lote = models.ForeignKey(
        AnaliseLote,
        on_delete=models.CASCADE,
        related_name="alertas",
    )
    classificacao = models.CharField(
        max_length=20,
        choices=ClassificacaoVencimento.choices,
    )
    mensagem = models.TextField()
    enviado_em = models.DateTimeField(null=True, blank=True)
    destinatario = models.CharField(max_length=255)

    class Meta:
        ordering = ["enviado_em", "-id"]
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"

    def __str__(self) -> str:
        status = "enviado" if self.enviado_em else "pendente"
        return f"{self.classificacao} para {self.destinatario} ({status})"


class ConfiguracaoAlerta(models.Model):
    classificacao = models.CharField(
        max_length=20,
        choices=ClassificacaoVencimento.choices,
    )
    canal = models.CharField(max_length=50)
    destinatario = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["classificacao", "canal", "destinatario"]
        verbose_name = "Configuracao de alerta"
        verbose_name_plural = "Configuracoes de alerta"

    def __str__(self) -> str:
        status = "ativa" if self.ativo else "inativa"
        return f"{self.classificacao} via {self.canal} para {self.destinatario} ({status})"
