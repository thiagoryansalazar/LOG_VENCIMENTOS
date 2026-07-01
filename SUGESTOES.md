# Sugestoes tecnicas

As ideias abaixo nao representam compromisso de implementacao. Cada item deve
ser validado quanto a valor operacional, custo, dependencias e risco de ampliar
o LOG_VENCIMENTOS para o escopo de um ERP.

## Integracao

- Criar conectores autorizados e somente leitura para ERPs.
- Importar CSV/XLSX por mapeamento de colunas versionado.
- Disponibilizar API externa com autenticacao e isolamento por empresa.
- Produzir diagnostico de qualidade antes de aceitar uma fonte.

## Captura assistida

- Usar OCR para sugerir dados de etiquetas, sempre com confirmacao humana.
- Usar scanner para localizar produtos sem presumir lote e validade no codigo
  de barras.

## Monitoramento e produto

- Processar sincronizacoes e alertas por eventos.
- Criar dashboards de criticidade, alertas e conferencias.
- Enviar notificacoes por canais configuraveis.
- Medir tempo entre alerta, conferencia e acao.
