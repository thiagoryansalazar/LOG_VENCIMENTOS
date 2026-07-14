# Sugestoes tecnicas

As ideias abaixo nao representam compromisso de implementacao. Cada item deve
ser validado quanto a valor operacional, custo, dependencias e risco de ampliar
o LOG_VENCIMENTOS para o escopo de um ERP.

## Integracao

- Criar conectores autorizados e somente leitura para ERPs.
- Importar CSV/XLSX por mapeamento de colunas versionado.
- Disponibilizar API externa com autenticacao e isolamento por empresa.
- Produzir diagnostico de qualidade antes de aceitar uma fonte.

## API como produto

- Tratar a API como interface principal de consumo da inteligencia do Atlas, nao
  apenas como apoio ao frontend.
- Versionar a API, preferencialmente em `/api/v1/`.
- Documentar o contrato com OpenAPI antes de permitir dependencia de sistemas
  externos.
- Retornar dados enriquecidos para permitir consumo por ERP de precos, CRM, BI e
  agentes de IA.
- Avaliar API Key para o MVP e planejar migracao futura para JWT/OAuth2 com
  escopos.
- Planejar, mas nao implementar prematuramente, endpoints como:
  - `GET /api/v1/lotes?status=CRITICO`;
  - `GET /api/v1/produtos/{codigo}/risco`;
  - `POST /api/v1/alertas/configurar`;
  - `POST /api/v1/decisoes/sugerir`.

## Captura assistida

- Usar OCR para sugerir dados de etiquetas, sempre com confirmacao humana.
- Usar scanner para localizar produtos sem presumir lote e validade no codigo
  de barras.

## Monitoramento e produto

- Processar sincronizacoes e alertas por eventos.
- Criar dashboards de criticidade, alertas e conferencias.
- Enviar notificacoes por canais configuraveis.
- Medir tempo entre alerta, conferencia e acao.
