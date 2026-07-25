# MVP Checklist - ATLAS Vencimentos

Data de referencia: 2026-07-24

Objetivo: controlar o fechamento do backend MVP antes da proxima etapa de
frontend.

## Entregavel 1 - Infraestrutura base

- [x] Django e Django REST Framework configurados.
- [x] PostgreSQL configurado via Docker.
- [x] `docker-compose.yml` com servicos `db` e `web`.
- [x] Variaveis de ambiente documentadas em `.env.example`.
- [x] API Key configurada por `ATLAS_API_KEY`.
- [x] Endpoint publico `GET /health`.

## Entregavel 2 - Camada de extracao

- [x] Interface abstrata de fonte externa.
- [x] Interface abstrata de mapeamento.
- [x] Adaptador CSV implementado.
- [x] Mapeador CSV implementado.
- [x] Arquivo `data/lotes_mockados.csv` disponivel para testes.
- [ ] Consulta SQL direta ao ERP real, pendente de acesso ao banco do ERP.

## Entregavel 3 - Core de vencimento

- [x] Validacao e normalizacao de lote.
- [x] Modelo de dominio `Lote`.
- [x] Calculo de dias restantes.
- [x] Regra `0 dias ou menos -> VENCIDO`.
- [x] Classificacao `CRITICO`, `ATENCAO` e `NORMAL`.
- [x] `DIAS_CRITICO` parametrizado por ambiente.
- [x] `DIAS_ATENCAO` parametrizado por ambiente.
- [x] Teste automatizado cobrindo limites configuraveis.

## Entregavel 4 - Memoria operacional

- [x] App `core` criado.
- [x] Model `AnaliseLote`.
- [x] Model `Alerta`.
- [x] Model `ConfiguracaoAlerta`.
- [x] Models registrados no Django Admin.
- [x] Migrations geradas e aplicadas no PostgreSQL.
- [x] Consultas basicas usando Django ORM.

## Entregavel 5 - Central de alertas

- [x] Interface `EmailSenderInterface`.
- [x] Implementacao SMTP/Gmail configuravel.
- [x] `EMAIL_SENDER_CLASS` configuravel.
- [x] Supressao de alertas duplicados em 24 horas.
- [x] Rate limit simples de email.
- [x] Registro em `Alerta` criado a cada envio realizado.
- [ ] Credenciais reais SMTP/SendGrid, pendentes por ambiente.

## Entregavel 6 - Orquestracao do fluxo completo

- [x] Comando `python manage.py executar_monitoramento`.
- [x] Leitura via CSV.
- [x] Mapeamento para contrato interno.
- [x] Chamada ao core de monitoramento.
- [x] Persistencia de `AnaliseLote`.
- [x] Disparo de alerta quando aplicavel.
- [x] Modo `--dry-run`.
- [x] Tratamento para continuar apos falha em lote individual.

## Entregavel 7 - API v1 e OpenAPI

- [x] `POST /api/v1/lotes/validar`.
- [x] `GET /api/v1/lotes`.
- [x] `GET /api/v1/lotes?codigo_produto=XXX&lote=YYY`.
- [x] `GET /api/v1/lotes/<id>`.
- [x] `GET /api/v1/lotes/criticos`.
- [x] `POST /api/v1/alertas/disparar`.
- [x] `GET /api/schema/`.
- [x] `GET /api/docs/`.
- [x] Endpoints privados protegidos por `X-API-Key`.
- [x] Documentacao OpenAPI publica.

## Validacao final

- [x] `docker compose config`.
- [x] `docker compose up -d --build`.
- [x] `docker compose exec -T web python manage.py migrate`.
- [x] `docker compose exec -T web python manage.py check`.
- [x] `docker compose exec -T web python manage.py test -v 2`.
- [x] `docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv --dry-run`.
- [x] `docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv`.
- [x] `docker compose exec -T web python manage.py spectacular --validate --file /tmp/schema.yaml`.
- [x] Validacao manual de `/health`.
- [x] Validacao manual de `/api/docs/`.
- [x] Validacao manual de `/api/schema/`.
- [x] Validacao manual de endpoint privado sem `X-API-Key` retornando 401.
- [x] Validacao manual de endpoint privado com `X-API-Key`.
- [x] Validacao manual de `/api/v1/lotes/criticos`.
- [x] Validacao manual de `/api/v1/lotes/<id>`.
- [x] Validacao manual de `/api/v1/lotes/<id>` inexistente retornando 404.

## Pendencias fora do backend MVP

- [ ] Conexao real com ERP.
- [ ] Credenciais reais de email por ambiente.
- [ ] Campo ou processo de baixa operacional de lotes criticos.
- [ ] Decisao final sobre `empresa` e `unidade` no contrato.
- [ ] Frontend.
- [ ] RabbitMQ/Celery para processamento assincrono.
