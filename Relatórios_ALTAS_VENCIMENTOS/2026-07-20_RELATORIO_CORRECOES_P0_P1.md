# Relatorio - Correcoes P0/P1 do MVP

Data: 2026-07-20

Projeto: ATLAS Vencimentos

Agente: Codex

## Objetivo

Registrar as correcoes executadas para reduzir gaps criticos e importantes do
MVP, com foco em dominio deterministico, validacao de entrada, infraestrutura,
persistencia, seguranca e governanca.

## Escopo executado

### 1. Dominio

- `hoje` passou a ser parametro obrigatorio em:
  - `calcular_dias_restantes`;
  - `classificar_risco`;
  - `monitorar_lote`.
- A API e o script CSV continuam usando a data atual, mas agora passam essa
  data explicitamente para o core.
- O objetivo e impedir que a regra de negocio dependa implicitamente do relogio
  da maquina.

### 2. Validacao de lote

- O campo `quantidade` passou a rejeitar:
  - campo ausente;
  - valor booleano;
  - valor nao numerico;
  - `NaN`;
  - infinito;
  - valor menor ou igual a zero.
- As mensagens de erro foram separadas por tipo de falha.
- Campos de texto passaram a ter limite maximo de 255 caracteres.

### 3. Modelo Lote

- O projeto ja nao usava dataclass para `Lote`; o modelo ja estava convertido
  para Django ORM.
- Foi aplicada validacao equivalente por meio do metodo `clean()`.

### 4. Persistencia

- `AnaliseLote` recebeu:
  - indice composto por `lote` e `codigo_produto`;
  - indice composto por `classificacao` e `data_analise`;
  - restricao de unicidade para `(lote, codigo_produto)`.
- Foi criada a migration:
  - `core/migrations/0002_analiselote_core_analis_lote_665e0e_idx_and_more.py`.

### 5. Infraestrutura

- `Dockerfile` ja estava presente e adequado ao escopo.
- `docker-compose.yml` ja possuia `db` e `web`.
- Foi adicionada rede explicita `atlas_network` para deixar a comunicacao entre
  servicos declarada.

### 6. Seguranca

- Middleware de API Key ja existia e protege as rotas, mantendo `/health`
  publico.
- Foi adicionado rate limiting no Django REST Framework:
  - classe: `AnonRateThrottle`;
  - limite: `100/hour`.

### 7. Governanca

- Foi criada a ADR-0003 para registrar a decisao de tornar a data de referencia
  obrigatoria no dominio.
- A execucao foi registrada em `.governanca/LOG.md` por subagente virtual.

## Validacoes executadas

- `.venv\Scripts\python.exe manage.py check`: aprovado.
- Testes sem banco: 21 testes aprovados.
- `.venv\Scripts\python.exe scripts\importar_csv.py`: aprovado.
- `docker compose config`: aprovado.

## Bloqueios

- `docker compose up -d --build` nao executou porque o Docker Desktop nao estava
  ativo.
- `manage.py migrate`, `showmigrations` e a suite completa `manage.py test -v 2`
  ficaram bloqueados porque o PostgreSQL em `localhost:5432` recusou conexao.

## Status

Codigo implementado, commitado e enviado ao GitHub.

Commit:

```text
24a10e3 fix: harden MVP domain and infrastructure gaps
```

## Proximos passos

1. Ligar Docker Desktop.
2. Executar `docker compose up -d --build`.
3. Executar `.venv\Scripts\python.exe manage.py migrate`.
4. Executar `.venv\Scripts\python.exe manage.py test -v 2`.
