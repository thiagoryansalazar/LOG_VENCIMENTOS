# Modificacoes do ATLAS Vencimentos para CEREBRO_ENGINEER

Data de envio: 2026-08-02

Origem: ATLAS Vencimentos

Destino: chat `CEREBRO_ENGINEER`

Agente: Codex

agent_id: codex

## Objetivo do registro

Consolidar, em formato Markdown, as modificacoes recentes do projeto ATLAS
Vencimentos para manter o `CEREBRO_ENGINEER` atualizado como base de contexto e
memoria tecnica.

## Estado atual do repositorio

- Repositorio local: `C:\TECH PROJETOS\ATLAS VENCIMENTOS`
- Branch: `main`
- Estado observado em 2026-08-02:
  - `main` esta `ahead 1` em relacao a `origin/main`.
  - Existem alteracoes locais de governanca ainda nao commitadas/pushadas.
- Arquivos locais modificados antes deste envio:
  - `.governanca/DECISOES.md`
  - `.governanca/LOG.md`
  - `.governanca/SUMMARY.md`
  - `.governanca/CONTEXTO_ATUAL.md`

## Linha do tempo tecnica

### 2026-07-21

- Commit `8f99c24`: criado comando `executar_monitoramento`.
- Commit `42f1069`: adicionado relatorio do Entregavel 6.
- Decisao operacional: o MVP usa processamento sincrono; Celery/RabbitMQ ficam
  fora do escopo imediato.

### 2026-07-22

- Commit `83360d6`: validado fluxo completo mockado.
- Fluxo validado:
  - CSV;
  - mapeador;
  - core de monitoramento;
  - PostgreSQL;
  - alerta;
  - API.

### 2026-07-24

- Commit `3fa820e`: formalizada governanca por subagentes.
- Commit `2d495ac`: API v1 e OpenAPI implementadas.
- Commit `74ae59f`: registrado fechamento do Entregavel 7.
- Commit `408b5e7`: adicionado endpoint `GET /api/v1/lotes/<id>`.
- Commit `4f3949f`: finalizado backend MVP com parametrizacao, checklist e
  correcoes.
- Commit `d6d86aa`: registrado versionamento final do backend MVP.
- Commit `e545062`: convertido `Lote` de ORM para dataclass, com ADR-0007.

## Decisoes arquiteturais consolidadas

### Backend como fonte oficial

- Django/DRF e PostgreSQL via Docker sao a base oficial do ATLAS.
- SQLite nao deve ser usado como banco operacional.
- O sistema externo, como ERP ou WMS, continua sendo fonte oficial dos dados de
  origem.
- O ATLAS classifica, persiste analises e expoe inteligencia operacional por
  API.

### API v1 e OpenAPI

Endpoints principais entregues:

- `GET /health`
- `POST /api/v1/lotes/validar`
- `GET /api/v1/lotes`
- `GET /api/v1/lotes/<id>`
- `GET /api/v1/lotes/criticos`
- `POST /api/v1/alertas/disparar`
- `GET /api/schema/`
- `GET /api/docs/`

Autenticacao:

- Endpoints privados usam `X-API-Key`.
- `/health`, `/api/schema/` e `/api/docs/` sao publicos.

### Regras de vencimento

- `0 dias ou menos`: `VENCIDO`
- `1..DIAS_CRITICO`: `CRITICO`
- `DIAS_CRITICO+1..DIAS_ATENCAO`: `ATENCAO`
- Acima de `DIAS_ATENCAO`: `NORMAL`

Variaveis configuraveis:

- `DIAS_CRITICO`, padrao `7`
- `DIAS_ATENCAO`, padrao `30`

Restricao operacional:

- `DIAS_CRITICO` deve ser menor que `DIAS_ATENCAO`.

### Persistencia

- `AnaliseLote`, `Alerta` e `ConfiguracaoAlerta` sao os modelos persistidos do
  MVP.
- `Lote` deixou de ser ORM e passou a ser DTO/dataclass.
- A tabela `src_lote` foi removida por migration porque era um ORM fantasma.

### Alertas

- Envio desacoplado via `EmailSenderInterface`.
- Provider inicial: SMTP/Gmail configuravel por `EMAIL_SENDER_CLASS`.
- Duplicidade suprimida em 24 horas.
- Rate limit simples de email.
- Credenciais reais SMTP/SendGrid ainda pendentes por ambiente.

### Frontend

- ADR-0008 registrada localmente em 2026-07-25.
- Direcao definida:
  - frontend como SPA estatica React/TypeScript/Vite/Tailwind;
  - Django permanece fonte da verdade;
  - frontend nao recalcula risco;
  - prototipo Node/Express fica apenas como referencia visual/historica.
- Fora do MVP frontend:
  - CRUD de lotes;
  - resolucao operacional;
  - historico completo de alertas;
  - Gemini/IA no frontend;
  - dados financeiros.

## Validacoes registradas

Backend MVP validado com:

- `docker compose config`
- `docker compose up -d --build`
- `docker compose exec -T web python manage.py migrate`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test -v 2`
- `docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv --dry-run`
- `docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv`
- `docker compose exec -T web python manage.py spectacular --validate --file /tmp/schema.yaml`

Resultado registrado:

- Suite backend: 44 testes aprovados.
- Monitoramento CSV: 6 lotes processados.
- API manual:
  - `/health`: 200
  - `/api/docs/`: 200
  - `/api/schema/`: 200
  - `/api/v1/lotes` sem API Key: 401
  - `/api/v1/lotes` com API Key: retornou registros
  - `/api/v1/lotes/criticos`: retornou registros criticos/vencidos
  - `/api/v1/lotes/<id>`: 200
  - `/api/v1/lotes/<id>` inexistente: 404

## Pendencias de decisao

- Acesso real ao ERP e formato definitivo de integracao.
- Credenciais reais de SMTP/SendGrid.
- Campo ou fluxo de baixa/resolucao de lotes criticos.
- Contrato final de `empresa` e `unidade`.
- Modelo de autenticacao para producao alem da API Key local.
- Publicacao/versionamento das alteracoes locais de governanca ainda pendentes,
  pois o repositorio foi observado como `ahead 1` e com arquivos modificados.

## Contexto para proximos agentes

Antes de novas implementacoes, ler:

- `.governanca/DECISOES.md`
- `.governanca/CONTEXTO_ATUAL.md`
- `.governanca/LOG.md`
- `CRONOGRAMA.md`
- `MVP_CHECKLIST.md`

Regra principal:

- O backend Django/DRF e a fonte executavel oficial.
- A Wiki e fonte conceitual, nao deve ser alterada pelo Codex.
- Mudancas devem ocorrer no repositorio local do projeto.
- Toda alteracao relevante deve registrar LOG com `agent_id`.
