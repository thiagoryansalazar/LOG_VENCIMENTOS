# Relatorio do Entregavel 6 - Orquestracao do Monitoramento

Data: 2026-07-21

Projeto: ATLAS Vencimentos

Agente responsavel: Codex

agent_id: codex_docs

## Objetivo

Implementar e validar o fluxo operacional do MVP para processar lotes a partir
de CSV, classificar vencimentos pelo core, persistir analises no PostgreSQL e
acionar a politica de alertas quando aplicavel.

## Escopo Executado

- Criado comando Django `executar_monitoramento`.
- Criados argumentos operacionais:
  - `--fonte`
  - `--arquivo`
  - `--limite`
  - `--dry-run`
- Integrado o comando ao fluxo existente:
  - `AdaptadorCSV`
  - `MapeadorCSV`
  - `monitorar_lote`
  - `AnaliseLote`
  - `ConfiguracaoAlerta`
  - `disparar_alerta`
- Criado CSV de exemplo `data/lotes_exemplo.csv`.
- Criados testes automatizados para o comando.
- Atualizada governanca de subagentes e LOG.
- Versionada a configuracao `.codex` exigida para subagentes.

## Arquivos Criados

- `.codex/config.toml`
- `.codex/agents/explorer.toml`
- `.codex/agents/designer.toml`
- `.codex/agents/implementer.toml`
- `.codex/agents/tester.toml`
- `.codex/agents/reviewer.toml`
- `core/management/__init__.py`
- `core/management/commands/__init__.py`
- `core/management/commands/executar_monitoramento.py`
- `data/lotes_exemplo.csv`
- `tests/test_commands.py`
- `Relatorios_ALTAS_VENCIMENTOS/2026-07-21_RELATORIO_ENTREGAVEL_6_MONITORAMENTO.md`

Observacao: a pasta real do projeto usa o nome `Relatórios_ALTAS_VENCIMENTOS`.

## Arquivos Alterados

- `.governanca/AGENTES/id_agentes.yaml`
- `.governanca/AGENTES/SUBAGENTES.md`
- `.governanca/LOG.md`

## Funcionamento Arquitetural

O comando `executar_monitoramento` atua como orquestrador operacional.

Ele nao concentra regra de negocio. A responsabilidade dele e conectar as
camadas ja existentes:

1. Leitura da fonte externa via `AdaptadorCSV`.
2. Normalizacao e conversao dos dados via `MapeadorCSV`.
3. Validacao e classificacao do lote via `monitorar_lote`.
4. Persistencia do resultado em `AnaliseLote`.
5. Avaliacao de alertas para lotes `CRITICO` e `VENCIDO`.
6. Registro de resumo operacional no terminal.

Com isso, o core permanece deterministico e reutilizavel, enquanto o comando
fica responsavel por execucao em lote, logs e continuidade do processamento em
caso de erro por linha.

## Regras Implementadas

- O parametro `hoje` e capturado uma vez por execucao.
- O modo `--dry-run` classifica e exibe resultados, mas nao persiste dados e
  nao dispara alertas.
- O modo real persiste analises usando `update_or_create`, respeitando a regra
  de unicidade por `codigo_produto` e `lote`.
- Erros em uma linha nao interrompem o processamento das proximas linhas.
- Alertas so sao avaliados para classificacoes `CRITICO` e `VENCIDO`.
- Se nao houver `ConfiguracaoAlerta` ativa para a classificacao, o comando
  registra `alertas_sem_configuracao` e segue sem falhar.
- Falhas operacionais de alerta, como credenciais ausentes, nao derrubam o
  processamento do lote.

## Validacoes Executadas

### Docker e Django

```bash
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py test -v 2
```

Resultado:

- Migrations: sem migrations pendentes.
- Django check: sem issues.
- Testes: 31 testes executados com sucesso.

### Dry-run com CSV mockado

```bash
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv --dry-run
```

Resultado:

- 6 lotes lidos.
- 6 lotes processados.
- 0 persistidos.
- 0 erros.

### Dry-run com CSV de exemplo

```bash
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_exemplo.csv --dry-run
```

Resultado:

- 6 lotes lidos.
- 6 lotes processados.
- 0 persistidos.
- 0 erros.

### Execucao real

```bash
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv
```

Resultado:

- 6 lotes lidos.
- 6 lotes processados.
- 6 analises persistidas.
- 0 erros.
- 4 lotes alertaveis sem configuracao ativa de alerta.

### Health check

```bash
Invoke-RestMethod -Uri http://localhost:8001/health -Method Get
```

Resultado:

- `status: ok`

## Evidencia de Commit

Commit do entregavel:

```text
8f99c24 feat: add executar monitoramento command
```

Push realizado para:

```text
main -> main
```

## Riscos Residuais

- A execucao real nao enviou email porque nao havia `ConfiguracaoAlerta` ativa
  no banco validado. O comportamento esperado foi registrar os casos como
  `alertas_sem_configuracao`.
- O teste do comando usa mock para `disparar_alerta`; a criacao real de
  registros `Alerta` permanece coberta pelos testes do servico de alerta.
- O rate limit de email continua simples e em memoria, adequado ao MVP, mas
  deve evoluir para cache distribuido quando houver multiplas instancias.

## Status Final

Entregavel 6 concluido e validado.

O ATLAS Vencimentos possui agora um comando operacional para executar o fluxo:

```text
CSV -> Mapeador -> Core -> PostgreSQL -> Politica de Alerta -> Resumo
```

O projeto esta pronto para evoluir para a etapa seguinte do cronograma.
