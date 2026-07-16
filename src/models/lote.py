from django.db import models


class Lote(models.Model):
    codigo_produto = models.CharField(max_length=100)
    nome_produto = models.CharField(max_length=255)
    lote = models.CharField(max_length=100)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    data_validade = models.DateField()
    local = models.CharField(max_length=255)

    class Meta:
        ordering = ["data_validade", "codigo_produto", "lote"]
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self) -> str:
        return f"{self.codigo_produto} / {self.lote}"
