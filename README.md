# ATLAS Vencimentos

Backend para consultar e validar dados de lotes, calcular dias restantes para o
vencimento e classificar riscos operacionais.

O sistema funciona como uma camada preventiva sobre dados operacionais mantidos
por sistemas externos. Ele nao substitui ERP, WMS ou outra fonte oficial e nao
se torna o proprietario principal dos dados monitorados.

Na visao futura, o ATLAS Vencimentos evolui para um hub de inteligencia de
estoque: consome dados de uma fonte autorizada, classifica e enriquece riscos de
vencimento, e expoe essa inteligencia por API para outros sistemas.

## Visao geral

Nesta primeira iteracao, a API recebe um lote em JSON, valida seu contrato
minimo e devolve a quantidade de dias para o vencimento e a classificacao de
risco.

O sistema de origem permanece como fonte de verdade. Na arquitetura-alvo, o
ATLAS Vencimentos sera acionado por evento ou por uma alternativa configurada,
consultara os dados necessarios, normalizara, monitorara e alertara. Ele nao
gravara correcoes diretamente na fonte. A conferencia fisica cabe a operacao e
a decisao cabe ao gestor, que atualiza o sistema oficial quando necessario.

Stack inicial:

- Python 3.11 ou superior;
- Django;
- Django REST Framework;
- drf-spectacular para OpenAPI;
- PostgreSQL via Docker.

## Modulos

- `src/integrations`: contratos da Camada de Integracao Externa, modos de
  acionamento, mapeamento e adaptadores por fonte.
- `src/validators`: validacao e normalizacao de dados de entrada.
- `src/services`: monitoramento, calculo de vencimento, classificacao de risco,
  servico de alerta e envio de email desacoplado.
- `src/models`: entidades do dominio.
- `src/routes`: endpoints HTTP da API.
- `src/utils`: funcoes auxiliares compartilhadas.

## Fluxo arquitetural

```text
Sistema de origem
  -> evento ou webhook, preferencialmente
  -> consulta agendada, quando nao ha evento
  -> importacao de arquivo, como alternativa
  -> Camada de Integracao Externa
  -> adaptador da fonte
  -> mapeador de campos
  -> valida e normaliza
  -> Monitoramento de Vencimentos
  -> Central de Alertas
  -> Gestor e operacao fisica
```

Os tres modos convergem para o mesmo contrato interno:

```text
EVENTO
CONSULTA_AGENDADA
ARQUIVO
```

Quando um evento carregar apenas identificador e dados minimos, o adaptador sera
o elemento ativo que consulta o registro completo na fonte autorizada. O
contrato definitivo do evento, autenticacao, idempotencia, replay e tratamento
de ordem ainda precisam ser definidos antes de criar um receptor HTTP.

A capacidade de integracao depende da porta oferecida pela fonte - webhook,
API, banco somente leitura, arquivo ou fila - e nao da linguagem usada pelo
sistema externo.

O contrato canonico planejado contem `codigo_produto`, `nome_produto`, `lote`,
`quantidade`, `data_validade`, `local` e `status`. O endpoint atual ainda nao
recebe `status`, pois sua origem, semantica e obrigatoriedade precisam ser
validadas antes da implementacao.

O setor alimenticio permanece como MVP. A futura generalizacao para outros
tipos de prazo, conformidade e risco nao altera automaticamente o modelo
executavel de `Lote`.

## Visao futura da API

A API deve ser tratada como parte do produto, nao apenas como entrada para um
frontend.

No futuro, outros sistemas poderao consumir a inteligencia gerada pelo Atlas:

- ERP de precos: sugerir desconto para produtos criticos;
- CRM: priorizar atendimento ou contato com lojas/unidades afetadas;
- BI: alimentar dashboards de risco e perdas evitadas;
- agentes de IA: decidir ou sugerir acoes a partir da classificacao.

Exemplo de resposta enriquecida esperada:

```json
{
  "lote": "L2026-01",
  "produto": {
    "codigo": "PROD-001",
    "nome": "Leite integral"
  },
  "validade": "2026-07-15",
  "dias_restantes": 3,
  "classificacao": "CRITICO",
  "recomendacao": "Vender com urgencia. Desconto sugerido: 15%"
}
```

Para o MVP, essa visao implica bom desenho de contrato, versionamento, erros
consistentes e autenticacao planejada. Nao implica implementar ERP de precos,
CRM, Redis, Celery ou MCP agora.

Detalhes: `docs/atlas_api_futura.md`.

## Estado atual

Implementado:

- API Django/DRF;
- autenticacao por API Key;
- validacao e normalizacao do lote;
- servico inicial de Monitoramento de Vencimentos por lote;
- calculo de dias restantes e classificacao de risco;
- memoria operacional em PostgreSQL;
- contrato abstrato e somente leitura para fontes externas;
- especializacao do adaptador para consulta ao ERP;
- adaptador CSV para ingestao mockada;
- modos de integracao por evento, consulta agendada ou arquivo;
- contrato de mapeamento entre registro externo e payload canonico;
- Central de Alertas por email com provedor configuravel;
- supressao de alertas duplicados em 24 horas;
- rate limit simples de 5 emails por minuto;
- API v1 para consulta de lotes, lotes criticos e disparo manual de alertas;
- documentacao OpenAPI com `drf-spectacular`.

Ainda nao implementado:

- conector real com ERP;
- receptor de webhook e contrato canonico do evento;
- repeticao, replay e ordenacao de eventos;
- monitoramento continuo e persistente;
- RabbitMQ, Celery Worker e Celery Beat;
- frontend e isolamento por empresa.

PostgreSQL e usado como banco operacional do MVP. O projeto nao deve depender
de SQLite.

Classificacao atual:

- `VENCIDO`: 0 dias ou menos;
- `CRITICO`: entre 1 e `DIAS_CRITICO` dias;
- `ATENCAO`: entre `DIAS_CRITICO + 1` e `DIAS_ATENCAO` dias;
- `NORMAL`: acima de `DIAS_ATENCAO` dias.

Valores padrao do MVP:

- `DIAS_CRITICO=7`;
- `DIAS_ATENCAO=30`.

Regra operacional: `DIAS_CRITICO` deve ser menor que `DIAS_ATENCAO`.

## Variaveis de ambiente

Crie um arquivo `.env` na raiz a partir do `.env.example`.

Variaveis principais:

```env
DATABASE_URL=postgres://atlas_user:atlas_pass@localhost:5432/atlas_db
ATLAS_API_KEY=atlas-mvp-2026
DIAS_CRITICO=7
DIAS_ATENCAO=30
EMAIL_SENDER_CLASS=src.services.email.GmailSender
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_TIMEOUT=30
EMAIL_RATE_LIMIT_PER_MINUTE=5
```

## Execucao local

```bash
python -m venv .venv
python -m pip install -r requirements.txt
docker compose up -d db
python manage.py migrate
python manage.py runserver
```

## Execucao com Docker

```bash
docker compose up -d --build
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py check
```

Por padrao, a API fica disponivel em:

```text
http://localhost:8001
```

## Alertas por email

O envio de email e desacoplado da regra de negocio por meio da interface
`EmailSenderInterface`.

A implementacao padrao e `src.services.email.GmailSender`, configurada por
`EMAIL_SENDER_CLASS`. Para trocar o provedor, crie uma classe que implemente
`enviar(destinatario, assunto, corpo)` e altere a variavel no `.env`.

Variaveis principais:

```env
EMAIL_SENDER_CLASS=src.services.email.GmailSender
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_RATE_LIMIT_PER_MINUTE=5
```

Regras atuais:

- `CRITICO` e `VENCIDO` geram alerta quando houver uma `AnaliseLote` persistida.
- O mesmo `analise_lote` com a mesma classificacao nao dispara email duplicado
  dentro de 24 horas.
- O limite padrao e 5 emails por minuto em memoria.
- Cada envio cria um registro em `Alerta` com `enviado_em` preenchido.

## Endpoints

- `GET /health`
- `POST /lotes/validar`
- `POST /api/v1/lotes/validar`
- `GET /api/v1/lotes`
- `GET /api/v1/lotes?codigo_produto=XXX&lote=YYY`
- `GET /api/v1/lotes/<id>`
- `GET /api/v1/lotes/criticos`
- `POST /api/v1/alertas/disparar`
- `GET /api/schema/`
- `GET /api/docs/`

`/health`, `/api/schema/` e `/api/docs/` sao publicos.

Os demais endpoints exigem:

```http
X-API-Key: sua-chave
```

### Validar lote

Exemplo:

```json
{
  "codigo_produto": "PROD-001",
  "nome_produto": "Leite integral",
  "lote": "L2026-01",
  "quantidade": 12,
  "data_validade": "2026-07-15",
  "local": "Deposito A"
}
```

### Consultar analises

```bash
curl -H "X-API-Key: atlas-mvp-2026" http://localhost:8001/api/v1/lotes
```

Filtros opcionais:

```bash
curl -H "X-API-Key: atlas-mvp-2026" "http://localhost:8001/api/v1/lotes?codigo_produto=PROD-001&lote=L2026-001"
```

### Consultar lotes criticos

No MVP, lotes criticos nao resolvidos sao interpretados como analises com
classificacao `CRITICO` ou `VENCIDO`.

```bash
curl -H "X-API-Key: atlas-mvp-2026" http://localhost:8001/api/v1/lotes/criticos
```

### Disparar alerta manual

```bash
curl -X POST http://localhost:8001/api/v1/alertas/disparar \
  -H "Content-Type: application/json" \
  -H "X-API-Key: atlas-mvp-2026" \
  -d "{\"analise_lote_id\": 1, \"destinatario\": \"gestor@empresa.com\"}"
```

## Testes

```bash
python manage.py check
python manage.py test -v 2
```

Validacao final esperada do backend MVP via Docker:

```bash
docker compose up -d --build
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py test -v 2
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv --dry-run
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv
```

As decisoes e o primeiro ciclo PDCA estao documentados em
`docs/backend.md`.
