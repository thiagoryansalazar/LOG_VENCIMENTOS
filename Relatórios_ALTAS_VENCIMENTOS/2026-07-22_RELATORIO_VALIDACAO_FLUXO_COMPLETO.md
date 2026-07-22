# Relatorio de Validacao - Fluxo Completo com Dados Mockados

Data: 2026-07-22

Projeto: ATLAS Vencimentos

Agente responsavel: Codex

agent_id: codex_qa

## Objetivo

Antecipar o entregavel previsto para 23/07/2026: testar o fluxo completo do
Entregavel 6 com dados mockados.

Fluxo validado:

```text
CSV -> AdaptadorCSV -> MapeadorCSV -> Core -> PostgreSQL -> Alerta -> LOG
```

## Ambiente

- Docker Compose ativo.
- Servicos:
  - `db`: PostgreSQL 15.
  - `web`: Django.
- Porta HTTP local:
  - `http://localhost:8001`

## Validacoes Executadas

### Docker

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

Resultado:

- Configuracao Docker valida.
- Containers `atlasvencimentos-db-1` e `atlasvencimentos-web-1` ativos.

### Migrations

```bash
docker compose exec -T web python manage.py migrate
```

Resultado:

- Nenhuma migration pendente.

### Health check

```bash
Invoke-RestMethod -Uri http://localhost:8001/health -Method Get
```

Resultado:

```text
status: ok
```

### Testes automatizados

```bash
docker compose exec -T web python manage.py test -v 2
```

Resultado:

- 31 testes executados.
- 31 testes aprovados.
- 0 falhas.

### Validacao operacional completa

Foi criado o script:

```text
scripts/validar_fluxo_completo.py
```

O script executa:

1. Limpeza controlada dos produtos mockados.
2. Criacao de `ConfiguracaoAlerta` ativa para `VENCIDO`.
3. Criacao de `ConfiguracaoAlerta` ativa para `CRITICO`.
4. Substituicao segura do sender de email por `FakeSender`.
5. Execucao do comando `executar_monitoramento`.
6. Confirmacao de analises, alertas e envios simulados.

Comando executado:

```bash
docker compose exec -T web python scripts/validar_fluxo_completo.py
```

Resultado:

```text
lidos: 6
processados: 6
salvos: 6
atualizados: 0
invalidos: 0
erros: 0
alertas_enviados: 4
alertas_suprimidos: 0
alertas_sem_configuracao: 0
alertas_sem_credencial: 0
analises=6
alertas=4
envios_fake=4
```

## Classificacoes Observadas

Com base em 22/07/2026:

```text
PROD-001 / L2026-001 -> VENCIDO (-12 dias)
PROD-002 / IG2026-014 -> VENCIDO (-5 dias)
PROD-003 / QM2026-022 -> VENCIDO (0 dias)
PROD-004 / SL2026-031 -> CRITICO (2 dias)
PROD-005 / PI2026-018 -> ATENCAO (19 dias)
PROD-006 / AB2026-045 -> NORMAL (34 dias)
```

Observacao importante:

- O produto com `0` dias restantes foi classificado como `VENCIDO`, conforme a
  regra definida pelo usuario.

## Arquivos Criados

- `scripts/validar_fluxo_completo.py`
- `Relatorios_ALTAS_VENCIMENTOS/2026-07-22_RELATORIO_VALIDACAO_FLUXO_COMPLETO.md`

Observacao: a pasta real do projeto usa o nome `Relatórios_ALTAS_VENCIMENTOS`.

## Arquivos Alterados

- `CRONOGRAMA.md`
- `.governanca/LOG.md`

## Status Final

Entregavel de 23/07/2026 antecipado e concluido em 22/07/2026.

O fluxo completo com dados mockados foi validado com sucesso no ambiente Docker
local, usando PostgreSQL e criacao real de registros `AnaliseLote` e `Alerta`.

O envio de email foi simulado por `FakeSender` para evitar dependencia de
credenciais reais ou envio externo durante a validacao.
