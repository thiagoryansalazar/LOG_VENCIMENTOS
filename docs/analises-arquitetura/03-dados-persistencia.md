# Análise da Camada de Dados & Persistência

> **Artefato:** Analisado em 19/07/2026  
> **Base de código:** commit atual do `main`

---

## 1. Prontidão para Produção — O que já está adequado

| Aspecto | Status | Observação |
|---|---|---|
| Definição do domínio `Lote` | ✅ Adequado | Dataclass `frozen=True` com `slots=True` — imutável, eficiente. |
| Separação de camadas | ✅ Adequado | `models/`, `services/`, `validators/`, `integrations/` bem isolados. |
| Core de classificação puro | ✅ Adequado | `vencimento.py` não depende de Django, ORM ou I/O. |
| `DEFAULT_AUTO_FIELD` | ✅ Adequado | `BigAutoField` evita colisão de chaves em 32 bits. |
| DRF configurado | ✅ Adequado | Framework REST presente e funcional. |

**Nada na camada de dados atual está pronto para produção**, porque simplesmente **não há camada de persistência implementada**. O que existe são entidades de domínio em memória (`dataclass`) e uma rota de validação que não grava dados em lugar algum.

---

## 2. Gaps Críticos (P0) — Bloqueantes para Produção

### 2.1 Ausência total de modelos Django no banco

O diretório `src/models/` contém **apenas** uma dataclass Python (`lote.py`). **Não existe um único `models.Model` herdando de Django.** Consequentemente:

- `python manage.py makemigrations` não gera migração alguma
- `python manage.py migrate` não cria tabelas
- Nenhum dado é persistido entre requisições

**Arquivo relevante:** `config/settings.py:29-34`

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

O banco SQLite é criado, mas **permanece vazio** — não há tabelas, índices ou constraints.

### 2.2 SQLite em produção (documentado como temporário, mas sem prazo)

`CLOUD.md:13-14` afirma:

> "Em produção, substitua o SQLite por PostgreSQL"

Porém:

- **Não existe configuração de PostgreSQL** em `settings.py` nem em variáveis de ambiente
- **Não há suporte a pooling** (`CONN_MAX_AGE`, `DATABASE_URL`, etc.)
- **Não há SSL/TLS** configurável
- **Não há `psycopg2` ou `asyncpg`** no `requirements.txt`
- **SQLite não suporta concorrência** — trava em escrita simultânea

**Risco:** Se a aplicação for deployada sem trocar o banco, a primeira requisição POST simultânea causará `database is locked`.

### 2.3 Modelos futuros não existem nem como esboço

A documentação (`docs/backend.md:196-202`, `SUGESTOES.md:25-29`, `docs/atlas_api_futura.md:144-149`) menciona:

- `AnaliseLote` — análise enriquecida por lote
- `Alerta` — notificações configuráveis por evento
- `ConfiguracaoAlerta` — regras de disparo de alertas
- Risco por produto
- Sugestão de decisões

**Nenhum destes modelos foi implementado, nem mesmo como `dataclass`.** O nível de detalhe é puramente conceitual (1-2 frases em markdown). Não há:
- Schema de tabela
- Tipos de campo
- Relacionamentos
- Constraints

### 2.4 Migrações: inexistentes

Não há arquivos em `src/migrations/`. O comando `makemigrations` não produz output porque não há `models.Model`.

### 2.5 Índices e consultas: não definidos

Como não há modelos, não há:

| Item | Status |
|---|---|
| Índices em campos de filtro (`lote`, `codigo_produto`, `data_validade`) | ❌ Não definidos |
| `unique_together` ou `UniqueConstraint` | ❌ Não definidos |
| `class Meta: indexes = [...]` | ❌ Não definido |
| `db_index=True` em campos | ❌ Não aplicado |

**Consultas esperadas (inferidas dos endpoints futuros):**

- `GET /api/v1/lotes?status=CRITICO` → filtra por `classificacao` + `data_validade`
- `GET /api/v1/produtos/{codigo}/risco` → filtra por `codigo_produto`
- Agrupamento por produto, contagem de lotes críticos

**Índices necessários (P0):**

```python
class AnaliseLote(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["codigo_produto", "data_validade"]),
            models.Index(fields=["classificacao"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["lote", "codigo_produto"],
                name="uq_lote_produto"
            )
        ]
```

### 2.6 Integridade referencial: não planejada

Os relacionamentos esperados:

```
Lote (fonte externa) 1──N AnaliseLote
Produto (código)     1──N AnaliseLote
AnaliseLote          1──N Alerta
ConfiguracaoAlerta   1──N Alerta
```

Nada disso está modelado. Sem `ForeignKey`, `OneToMany` ou `ManyToMany`, não há:
- `ON DELETE CASCADE`
- `ON DELETE SET NULL`
- `PROTECT` para impedir exclusão acidental

---

## 3. Gaps Importantes (P1) — Devem ser resolvidos antes do go-live

### 3.1 Pool de conexões (PostgreSQL)

Django usa `CONN_MAX_AGE` (default=0) para reuso de conexões. Quando for migrar para PostgreSQL:

- Configurar `CONN_MAX_AGE` para 60-300 segundos (persistent connections)
- Avaliar `django-db-geventpool` ou `pgbouncer` para ambientes com WSGI multi-thread
- **Não usar `CONN_MAX_AGE` com SQLite** — causa `database is locked`

### 3.2 Timeout de conexão

Inexistente no `settings.py`. Para PostgreSQL, necessário:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "connect_timeout": 5,
            "sslmode": "require",
        },
    }
}
```

### 3.3 SSL/TLS

Sem configuração. PostgreSQL em produção (RDS, CloudSQL, Supabase) exige `sslmode=require`.

### 3.4 Backup e恢复

**Zero documentado.** Não há:
- Script de dump (`pg_dump` / `sqlite3 .dump`)
- Política de retenção
- Teste de restore
- Backup automatizado (cron, pg_cron, ou serviço cloud)

### 3.5 Read replicas

Prematuro para o MVP, mas **a arquitetura Django ORM já suporta** `DATABASE_ROUTERS` e réplicas de leitura. Não requer ação imediata, mas o `settings.py` deveria ser estruturado para aceitar múltiplos bancos sem refactor:

```python
DATABASES = {
    "default": {...},  # escrita
    "replica": {...},  # leitura (futuro)
}
DATABASE_ROUTERS = ["config.routers.ReadWriteRouter"]
```

---

## 4. Melhorias Futuras (P2)

### 4.1 Cache (Redis)

Para os endpoints:

- `GET /api/v1/lotes?status=CRITICO` — cache de 1-5 min (dados não mudam em tempo real)
- Classificação de produto repetida — evitar recalcular

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379"),
    }
}
```

Requer `django-redis` ou `redis-py` no `requirements.txt`.

### 4.2 Migrações avançadas

- `RunSQL` para migrações de dados (backfill de classificações históricas)
- `SeparateDatabaseAndState` para refactors de schema sem downtime
- `db_index` vs `Index` funcional (expressões SQL)

### 4.3 Sharding / Partitioning

- PostgreSQL `TABLE PARTITION BY RANGE (data_validade)` — partitioning por mês/ano
- Django não suporta partitioning nativamente; requer `RunSQL` manual ou bibliotecas como `django-postgres-extra`

---

## 5. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Perda de dados (sem backup) | Alta | Alto | Configurar backup imediatamente ao migrar para PostgreSQL |
| Lock de tabela SQLite em concorrência | Alta (se deployar com SQLite) | Alto | Migrar para PostgreSQL antes do go-live |
| Ausência de unique constraint permite lotes duplicados | Média | Alto | Adicionar `UniqueConstraint(lote, codigo_produto)` |
| Falta de índices causa full scan em tabelas com milhares de registros | Média | Médio | Adicionar índices compostos antes do primeiro deploy |
| Conexão sem timeout trava worker | Média | Médio | Configurar `connect_timeout` no `OPTIONS` |
| SSL não configurado expõe dados em trânsito | Baixa (se rede interna) | Alto | Exigir `sslmode=require` |
| Migração manual sem `RunPython` causa inconsistência | Média | Alto | Usar migrations Django desde o primeiro modelo |

---

## 6. Recomendações Priorizadas

### P0 — Bloqueantes (fazer antes do go-live)

1. **Criar modelo Django `AnaliseLote`** com campos:
   - `lote` (CharField), `codigo_produto` (CharField), `nome_produto` (CharField)
   - `quantidade` (DecimalField), `data_validade` (DateField), `local` (CharField)
   - `classificacao` (CharField choices = ClassificacaoRisco)
   - `dias_restantes` (IntegerField)
   - `data_analise` (DateTimeField auto_now_add)
   - Metadados: `db_table`, `indexes`, `UniqueConstraint`

2. **Criar modelo `Alerta`:**
   - `analise` (ForeignKey AnaliseLote)
   - `tipo` (CharField choices)
   - `canal` (CharField — email, webhook, etc.)
   - `disparado_em` (DateTimeField)
   - `lido` (BooleanField)

3. **Criar modelo `ConfiguracaoAlerta`:**
   - `classificacao_alvo` (CharField)
   - `dias_limite` (IntegerField)
   - `canais` (JSONField)

4. **Gerar e aplicar migrations** imediatamente após criar os modelos.

5. **Configurar PostgreSQL** em `settings.py` usando variáveis de ambiente:

```python
import os
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "log_vencimentos"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
            "sslmode": os.getenv("DB_SSLMODE", "require"),
        },
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "300")),
    }
}
```

6. **Adicionar `psycopg2-binary` ou `psycopg`** ao `requirements.txt`.

7. **Adicionar índices compostos** nos modelos conforme item 2.5.

### P1 — Importantes (antes do go-live)

8. **Adicionar `django.contrib.postgres`** para aproveitar `ArrayField`, `JSONField`, `SearchVector`, etc.

9. **Estruturar `settings.py`** com suporte a `DATABASE_URL` via `dj-database-url`:

```
pip install dj-database-url
```

```python
import dj_database_url
DATABASES["default"] = dj_database_url.config(
    default=os.getenv("DATABASE_URL"),
    conn_max_age=300,
    ssl_require=True,
)
```

10. **Documentar estratégia de backup** em `docs/ops.md`:
    - `pg_dump` diário com retenção de 7 dias
    - Teste de restore mensal
    - Backup para storage object (S3/MinIO)

11. **Configurar `ALLOWED_HOSTS` via env** (já feito parcialmente) e garantir `DEBUG=False` em produção.

### P2 — Melhorias futuras

12. Avaliar Redis para cache de consultas repetitivas (classificações, listas de lotes críticos).

13. Avaliar particionamento de tabela `AnaliseLote` por mês (`PARTITION BY RANGE (data_analise)`).

14. Configurar `django-constance` ou tabela de configuração dinâmica para parâmetros de alerta sem deploy.

---

## 7. Diagrama de dados proposto (lógico)

```
┌─────────────────────┐          ┌──────────────────────────┐
│  ConfiguracaoAlerta  │          │     AnaliseLote          │
├─────────────────────┤          ├──────────────────────────┤
│ id (PK)             │──┐       │ id (PK)                  │
│ classificacao_alvo   │  │       │ lote (idx)               │
│ dias_limite         │  │       │ codigo_produto (idx)     │
│ canais (JSON)       │  │       │ nome_produto             │
│ ativo               │  │       │ quantidade               │
└─────────────────────┘  │       │ data_validade (idx)      │
                         │       │ local                    │
                         │       │ classificacao (idx)      │
                         │       │ dias_restantes           │
                         │       │ data_analise (idx)       │
                         │       │                          │
                         │       │ UQ: (lote, codigo_produto)│
                         │       │ IX: (classificacao,      │
                         │       │     data_validade)       │
                         │       └──────────┬───────────────┘
                         │                  │
                         │       ┌──────────▼───────────────┐
                         │       │        Alerta             │
                         │       ├──────────────────────────┤
                         └──────>│ id (PK)                  │
                                 │ configuracao (FK)        │
                                 │ analise (FK)             │
                                 │ tipo                     │
                                 │ canal                    │
                                 │ disparado_em             │
                                 │ lido                     │
                                 └──────────────────────────┘
```
