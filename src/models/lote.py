from django.db import models
from django.core.exceptions import ValidationError


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

    def clean(self) -> None:
        super().clean()
        campos_texto = {
            "codigo_produto": self.codigo_produto,
            "nome_produto": self.nome_produto,
            "lote": self.lote,
            "local": self.local,
        }
        erros = {
            campo: "Este campo nao pode ser vazio."
            for campo, valor in campos_texto.items()
            if not isinstance(valor, str) or not valor.strip()
        }
        if self.data_validade is None:
            erros["data_validade"] = "Informe uma data valida."
        if erros:
            raise ValidationError(erros)
