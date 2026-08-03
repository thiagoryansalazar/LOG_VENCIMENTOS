# Contexto Atual - ATLAS Vencimentos

Data: 2026-07-28

Agente registrador: Codex

agent_id: codex

## Estado do projeto

- Backend MVP validado e versionado.
- API Django/DRF e PostgreSQL via Docker sao a base oficial.
- OpenAPI esta disponivel por `drf-spectacular`.
- Frontend deve consumir a API Django; nao deve recriar regra de negocio local.

## Decisoes vigentes

- A Wiki externa permanece como fonte conceitual, mas nao deve ser alterada pelo
  Codex.
- Toda mudanca executavel deve ocorrer no repositorio local do projeto.
- `Lote` e DTO/dataclass; persistencia operacional fica em `AnaliseLote`.
- Lotes criticos nao resolvidos, no MVP, significam analises `CRITICO` ou
  `VENCIDO`.
- `DIAS_CRITICO` e `DIAS_ATENCAO` sao configuraveis por ambiente.
- Frontend MVP deve ser SPA estatica conectada ao Django.

## Restricoes atuais

- Nao implementar MCP no MVP.
- Nao introduzir RabbitMQ/Celery antes de necessidade operacional validada.
- Nao usar SQLite como banco operacional.
- Nao gravar segredos em arquivos versionados.
- Nao transformar prototipo Node/Express em backend oficial.

## Pendencias de decisao

- Acesso real ao ERP e formato definitivo de integracao.
- Credenciais reais de SMTP/SendGrid por ambiente.
- Campo ou fluxo de baixa/resolucao de lotes criticos.
- Contrato final de `empresa` e `unidade`.
- Modelo de autenticacao adequado para producao alem da API Key local.

## Regra de continuidade

Antes de novas implementacoes, o agente deve verificar:

- `.governanca/DECISOES.md`;
- `.governanca/CONTEXTO_ATUAL.md`;
- `CRONOGRAMA.md`;
- `MVP_CHECKLIST.md`;
- estado Git local.
