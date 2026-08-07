# Contexto Atual - ATLAS Vencimentos

Data: 2026-08-07

Agente registrador: Claude Code

agent_id: claude

## Estado do projeto

- Backend MVP validado e versionado em `9cd30b3`; working tree limpa.
- API Django/DRF e PostgreSQL via Docker sao a base oficial.
- OpenAPI esta disponivel por `drf-spectacular`.
- Frontend consome a API Django e nao recria regra de negocio local.
- Frontend versionado em `8dcfdf4` (`main`), com design system proprio sobre
  shadcn/ui + Radix, `DashboardView`, `LotesMonitoradosView`, `LotTable` em
  TanStack Table v8, grafico de distribuicao de risco em Recharts e
  code-splitting por rota.
- Suite do frontend com 36 testes em 8 arquivos; `typecheck`, `test` e `build`
  aprovados.
- Requisitos formalizados em `REQUISITOS.md` (versao 1.1) no repositorio do
  frontend, com RN/RF/RNF numerados e prioridades P1-P3.
- RNF-12 (acessibilidade) fechada: contraste AA atendido nos textos de risco.

## Decisoes vigentes

- A Wiki externa permanece como fonte conceitual, mas nao deve ser alterada
  pelo agente.
- Toda mudanca executavel deve ocorrer no repositorio local do projeto.
- `Lote` e DTO/dataclass; persistencia operacional fica em `AnaliseLote`.
- Lotes criticos nao resolvidos, no MVP, significam analises `CRITICO` ou
  `VENCIDO`.
- `DIAS_CRITICO` e `DIAS_ATENCAO` sao configuraveis por ambiente.
- Frontend MVP deve ser SPA estatica conectada ao Django.
- O MVP sera validado tambem em empresas de materiais de construcao civil,
  alem de supermercados. A generalizacao nao altera o modelo executavel de
  `Lote`/`AnaliseLote`.
- Cor de perigo tem dois usos distintos: `--danger` (#D32F2F) para fundos,
  bordas e series de grafico; `--danger-text` (#EF5350) para texto sobre fundo
  escuro. Badges CRITICO e ATENCAO usam texto escuro sobre a cor de fundo.

## Restricoes atuais

- Nao implementar MCP no MVP.
- Nao introduzir RabbitMQ/Celery antes de necessidade operacional validada.
- Nao usar SQLite como banco operacional.
- Nao gravar segredos em arquivos versionados.
- Nao transformar prototipo Node/Express em backend oficial.

## Pendencias de decisao

- Acesso real ao ERP e formato definitivo de integracao.
- Credenciais reais de SMTP/SendGrid por ambiente.
- Campo ou fluxo de baixa/resolucao de lotes criticos (RF-20).
- Contrato final de `empresa` e `unidade` (RNF-04).
- Modelo de autenticacao adequado para producao alem da API Key local
  (RNF-01a).

## Proximos passos tecnicos

- RF-18: paginacao e filtros server-side em `GET /api/v1/lotes`. Hoje o
  dashboard e os filtros dependem do endpoint trazer tudo e agregar no cliente,
  o que nao escala para volume de supermercado somado a construcao civil.
- RF-19: endpoint agregado de KPIs, substituindo o calculo de metricas no
  cliente.
- Persistencia real das telas de Cadastro, Configuracoes e Usuario, hoje
  placeholders por corte frontend-first.
- Acompanhar advisory high do `react-router`; risco aceito por ora, pois a
  aplicacao e SPA client-side sem RSC.

## Regra de continuidade

Antes de novas implementacoes, o agente deve verificar:

- `.governanca/DECISOES.md`;
- `.governanca/CONTEXTO_ATUAL.md`;
- `CRONOGRAMA.md`;
- `MVP_CHECKLIST.md`;
- `REQUISITOS.md`, no repositorio do frontend;
- estado Git local dos dois repositorios.
