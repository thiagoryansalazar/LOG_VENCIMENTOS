from django.db import models


class ClassificacaoVencimento(models.TextChoices):
    VENCIDO = "VENCIDO", "Vencido"
    CRITICO = "CRITICO", "Critico"
    ATENCAO = "ATENCAO", "Atencao"
    NORMAL = "NORMAL", "Normal"


class AnaliseLote(models.Model):
    nome_produto = models.CharField(max_length=255, blank=True)
    codigo_produto = models.CharField(max_length=100)
    lote = models.CharField(max_length=100)
    quantidade_inicial = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    quantidade_atual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    data_validade = models.DateField()
    dias_restantes = models.IntegerField()
    classificacao = models.CharField(
        max_length=20,
        choices=ClassificacaoVencimento.choices,
    )
    # auto_now, e nao auto_now_add: o campo representa a data da ultima
    # analise. Como o monitoramento reaproveita o registro por
    # (lote, codigo_produto) via update_or_create, auto_now_add congelava a
    # data na primeira execucao enquanto dias_restantes seguia sendo
    # recalculado.
    data_analise = models.DateTimeField(auto_now=True)
    local = models.CharField(max_length=100, blank=True)
    unidade = models.CharField(max_length=50, blank=True)
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


class HistoricoLote(models.Model):
    analise_lote = models.ForeignKey(
        AnaliseLote,
        on_delete=models.CASCADE,
        related_name="historico_alteracoes",
    )
    usuario = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_lotes",
    )
    quantidade_anterior = models.DecimalField(max_digits=12, decimal_places=3)
    quantidade_nova = models.DecimalField(max_digits=12, decimal_places=3)
    local_anterior = models.CharField(max_length=100, blank=True)
    local_novo = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Historico de lote"
        verbose_name_plural = "Historicos de lotes"

    def __str__(self) -> str:
        return f"{self.analise_lote} alterado em {self.criado_em:%Y-%m-%d %H:%M}"


class EventoOperacional(models.Model):
    tipo = models.CharField(max_length=50)
    descricao = models.TextField()
    total_lotes = models.PositiveIntegerField(null=True, blank=True)
    usuario = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_operacionais",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Evento operacional"
        verbose_name_plural = "Eventos operacionais"

    def __str__(self) -> str:
        return f"{self.tipo} em {self.criado_em:%Y-%m-%d %H:%M}"


class ConexaoSistema(models.Model):
    # Limite deliberado do MVP: cada cliente tem seu proprio deployment, entao
    # nao ha isolamento por tenant aqui -- o limite protege contra o operador
    # acumular conexoes esquecidas/nao usadas, nao contra outros clientes.
    MAX_CONEXOES = 3

    nome_sistema = models.CharField(max_length=100, blank=True)
    api_url_encrypted = models.TextField(blank=True)
    webhook_url_encrypted = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["criado_em", "id"]
        verbose_name = "Conexao de sistema"
        verbose_name_plural = "Conexoes de sistemas"

    def __str__(self) -> str:
        return self.nome_sistema or "Conexao de sistema"


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
