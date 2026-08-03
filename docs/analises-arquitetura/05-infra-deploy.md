# Análise de Infraestrutura & Deploy

**Data:** 19/07/2026
**Versão do código analisada:** branches/commits atuais
**Artefatos revisados:** `config/settings.py`, `config/wsgi.py`, `app.py`, `manage.py`, `requirements.txt`, `CLOUD.md`, `SECURITY.md`, `CRONOGRAMA.md`, `.gitignore`, `README.md`

---

## 1. Prontidão para Produção

**Nenhum aspecto está atualmente pronto para produção.** A aplicação encontra-se em estágio inicial de desenvolvimento (MVP com escopo reduzido). Abaixo, os únicos pontos que caminham na direção correta:

| Item | Status | Observação |
|------|--------|------------|
| `ALLOWED_HOSTS` via env var | ✅ Parcial | Lê de `DJANGO_ALLOWED_HOSTS` com fallbar para `localhost,127.0.0.1`. Correto, mas precisa de valor explícito em produção. |
| `SECRET_KEY` via env var | ✅ Parcial | Lê de `DJANGO_SECRET_KEY` com fallback `"unsafe-development-key"`. Sem fallback em produção é aceitável, mas não há validação que impeça o fallback de chegar ao ar. |
| `DEBUG` via env var | ✅ Parcial | Lê de `DJANGO_DEBUG` com fallback `"true"`. Perigoso: se a variável não for definida, produção roda com DEBUG=true. |
| `.gitignore` | ✅ Adequado | Ignora `.env`, `db.sqlite3`, `*.log`, `__pycache__`, `.venv/`, `logs/`. Correto. |
| Documentação de intenção (`CLOUD.md`, `SECURITY.md`) | ✅ Diretrizes claras | Os documentos estabelecem as regras corretas (env vars, sem secrets em código, PostgreSQL em prod). Falta implementação. |

---

## 2. Gaps Críticos (P0) — Bloqueantes para Produção

### 2.1 Separação de Ambientes

**Problema:** Não existe separação de configurações entre dev/staging/production.

- `config/settings.py` é único e monolítico. A mesma configuração é usada em qualquer ambiente.
- Não há módulos como `settings/base.py`, `settings/dev.py`, `settings/prod.py`.
- A variável `DJANGO_SETTINGS_MODULE` é fixa em `config.settings` tanto em `wsgi.py` quanto em `manage.py` — não há mecanismo para trocar o módulo de settings por ambiente.
- Não existe `settings_local.py` ou import condicional para override local.

**Impacto:** Em produção, não é possível ter configurações diferentes para banco de dados, logging, cache, segurança sem modificar o mesmo arquivo, o que torna o deploy frágil e propenso a erro humano.

**Arquivos afetados:** `config/settings.py:1-47`, `config/wsgi.py:6`, `manage.py:7`

### 2.2 Variáveis de Ambiente e Secrets

**Problema:** Secrets estão parcialmente externalizados, mas com fallbacks inseguros e faltam variáveis críticas.

| Variável | Status | Problema |
|----------|--------|----------|
| `DJANGO_SECRET_KEY` | Parcial | fallback `"unsafe-development-key"` — se a env var não for definida em produção, a chave é pública e previsível. |
| `DJANGO_DEBUG` | ❌ Inseguro | fallback `"true"` — produção roda em DEBUG se esquecerem de setar. |
| `DJANGO_ALLOWED_HOSTS` | ✅ Ok | fallback aceitável para dev (`localhost,127.0.0.1`). |
| `DATABASE_URL` | ❌ Ausente | Não existe. Não há suporte a `dj-database-url` ou `DATABASE_URL`. |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | ❌ Ausente | Nenhuma variável para configurar PostgreSQL. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | ❌ Ausente | Necessário para Central de Alertas (Entregável 5 do cronograma). |
| `API_KEY` | ❌ Ausente | Necessário para Entregável 7 (API Key fixa). |
| `DJANGO_LOG_LEVEL` | ❌ Ausente | Não há configuração de logging que leia env vars. |
| `DJANGO_SECURE_SSL_REDIRECT`, `HSTS_SECONDS` | ❌ Ausente | Sem suporte a HTTPS/HSTS. |
| Carregamento de `.env` | ❌ Ausente | Não usa `python-dotenv` nem `django-environ`. |

**Arquivos afetados:** `config/settings.py:7-13`, `requirements.txt:1-2`

### 2.3 Docker

**Problema:** Não existe nenhum artefato Docker.

- ❌ `Dockerfile` ausente
- ❌ `docker-compose.yml` ausente
- ❌ `.dockerignore` ausente
- ❌ `docker-compose.override.yml` (para dev) ausente

**Impacto:** A aplicação não pode ser empacotada, distribuída ou executada de forma padronizada. Cada deploy exige configuração manual do ambiente Python, dependências, banco e aplicação. Isso inviabiliza:
- Reprodutibilidade entre máquinas
- Testes em container local
- Deploy em qualquer plataforma cloud (Render, Fly.io, Railway, ECS, etc.)
- Uso de PostgreSQL em container (previsto no cronograma para o dia 13/07)

**Referência no cronograma:** CRONOGRAMA.md marca para o dia 13/07 a configuração de "PostgreSQL via Docker" — atualmente não implementado.

### 2.4 Banco de Dados em Produção

**Problema:** `settings.py` usa exclusivamente SQLite.

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

Pontos críticos:
- **Nenhuma preparação para PostgreSQL.** A engine, nome, host, porta, usuário e senha estão hardcoded para SQLite. Não há leitura de `DATABASE_URL` nem variáveis individuais de conexão.
- **Não há dependência de `psycopg2` ou `psycopg2-binary`** no `requirements.txt`.
- **SQLite em produção** não suporta concorrência, tem performance limitada e não é adequado para ambientes multi-usuário.
- **Migrations** existem mas não há script de inicialização de banco.
- **CLOUD.md** afirma "Em produção, substitua o SQLite por PostgreSQL" — mas não há mecanismo automatizado para isso.

### 2.5 Static/Media Files

**Problema atenuado:** A aplicação atual não tem frontend, Django Admin desabilitado (`TEMPLATES = []`), e não serve arquivos estáticos ou de mídia.

**Risco futuro:** Quando `drf-spectacular` for adicionado (Entregável 7), ele gera documentação Swagger/ReDoc que depende de static files. Também, se o Django Admin for ativado no futuro, será necessário servir static files. Atualmente não há:
- `STATIC_URL`, `STATIC_ROOT`, `STATICFILES_DIRS` configurados
- `MEDIA_URL`, `MEDIA_ROOT` configurados
- Nenhuma estratégia para servir static files em produção (WhiteNoise, CDN, S3, nginx)

### 2.6 Logging

**Problema:** Não existe configuração de logging no Django.

```python
# settings.py — nenhuma variável LOGGING
```

Consequências:
- Logs vão apenas para o console do servidor WSGI (stdout/stderr do Gunicorn/uWSGI).
- Sem rotação de logs, nível configurável, handlers para arquivo, formato estruturado.
- Sem separação entre logs de aplicação, acesso, erro.
- **SECURITY.md** afirma "Logs não devem conter credenciais, payloads completos nem dados críticos" — mas sem um logging configurado, não há como garantir isso.

**Recomendação para P0:** Adicionar dicionário `LOGGING` com:
- Console handler para dev (nível DEBUG)
- Arquivo rotacionado para produção (nível INFO/WARNING)
- Logger separado para `django.request` (erros HTTP)
- Formato JSON estruturado se possível (ou no mínimo com timestamp, nível, módulo)

### 2.7 HTTPS/SSL e Proxy Reverso

**Problema:** A aplicação não está preparada para rodar atrás de um proxy reverso.

Ausências:
- Nenhuma configuração de `SECURE_PROXY_SSL_HEADER` — necessário para identificar corretamente requisições HTTPS vindas de nginx/caddy/AWS ALB
- `SECURE_SSL_REDIRECT` — não configurado
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — não configurados (embora sessões/CSRF não estejam ativos no momento)
- `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` — não configurados
- `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS` — não configurados (middleware `SecurityMiddleware` está ativo, mas sem as configurações correspondentes)
- `CORS` — sem configuração (`django-cors-headers` não está no `requirements.txt`)

**Impacto:** Se implantado atrás de nginx ou Load Balancer, o Django pode interpretar incorretamente o schema HTTP, gerar redirects para HTTP em vez de HTTPS, e ficar vulnerável a ataques de downgrade.

---

## 3. Gaps Importantes (P1) — Deveriam ser Resolvidos Antes do Go-Live

### 3.1 CI/CD

**Problema:** Não existe pipeline de CI/CD.

- Nenhum arquivo `.github/workflows/*.yml`
- Nenhum `Jenkinsfile`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`
- Testes não rodam automaticamente em nenhum evento de push/PR
- Deploy é manual (presumivelmente via scp, rsync ou git pull no servidor)
- Nenhuma verificação de lint, tipo, segurança antes de merge

**Impacto:** Cada deploy é um evento manual de alto risco. Sem validação automatizada, erros de sintaxe, quebra de testes ou regressões podem chegar em produção.

### 3.2 Health Check — Readiness + Liveness

**Problema:** Apenas `GET /health` existe, e retorna um simples "ok".

```
src/routes/health.py — não foi analisado, mas o README lista apenas GET /health
```

Para orquestração (Kubernetes, ECS, Nomad), são necessários múltiplos probes:
- **Liveness probe:** o processo está vivo? (pode ser o atual `/health`)
- **Readiness probe:** a aplicação está pronta para receber tráfego? (banco de dados disponível, migrations aplicadas)
- **Startup probe:** a aplicação terminou de inicializar? (útil para apps com warmup lento)

O endpoint atual não verifica conectividade com banco de dados nem estado interno.

### 3.3 Observabilidade

**Problema:** Nenhum sistema de observabilidade está configurado.

- ❌ **APM** — sem Sentry, New Relic, Datadog, Elastic APM
- ❌ **Métricas** — sem Prometheus, OpenTelemetry, Django-Prometheus
- ❌ **Alertas** — sem integração com PagerDuty, OpsGenie, Slack webhooks
- ❌ **Estruturação de logs** — logs não são estruturados (JSON), não podem ser ingeridos por Loki/ELK
- ❌ **Tracing distribuído** — não aplicável no momento (sem microsserviços)

**Impacto:** Se a aplicação falhar em produção, não há como diagnosticar causa raiz sem acessar o servidor manualmente. Em cenário de baixa latência (prazo de 31/07), isso é aceitável para MVP, mas deve ser priorizado antes de qualquer usuário real depender do sistema.

### 3.4 Gestão de Dependências

**Problema:** `requirements.txt` com apenas 2 dependências e sem lock file.

```
Django>=5.2,<5.3
djangorestframework>=3.16,<3.17
```

Issues:
- **Range aberto** — `>=5.2,<5.3` pode pegar qualquer versão entre 5.2.0 e 5.2.x. Sem lock file, cada `pip install` pode resolver versões diferentes, quebrando a reprodutibilidade.
- **Dependências transitivas** — Django puxa `asgiref`, `sqlparse`, etc. Sem lock, as versões dessas libs variam.
- **Faltam dependências de produção** — `gunicorn`, `psycopg2-binary`, `python-dotenv` (ou `django-environ`), `django-cors-headers`, `whitenoise` (quando necessário), `sentry-sdk`.
- **Sem ferramenta moderna** — Poetry, pip-tools ou Pipenv não são usados. A melhor prática atual para projetos Django é Poetry ou pip-tools para manter `requirements.in` + `requirements.txt` compilado.

**Necessidades futuras (já identificadas no cronograma):**
- `psycopg2-binary` — PostgreSQL
- `python-dotenv` — carregar `.env`
- `gunicorn` — servidor WSGI de produção
- `drf-spectacular` — documentação OpenAPI
- Pacote SMTP (`smtplib` é built-in, mas para SendGrid: `sendgrid`)

### 3.5 Scripts de Inicialização

**Problema:** Não há script de inicialização ou entrypoint.

Faltam:
- **Script de entrypoint**: que rode `migrate`, colete static files (quando aplicável), crie superusuário (se necessário), e inicie o servidor
- **Seed data**: dados iniciais para validação do MVP
- **`manage.py`** é o único entrypoint — mas em produção, deve-se usar `gunicorn config.wsgi:application`

**CRONOGRAMA.md** prevê no dia 13/07: "Rodar `python manage.py migrate`" — mas não há automação.

---

## 4. Melhorias Futuras (P2)

### 4.1 Orquestração

- **Kubernetes:** Para um MVP com prazo até 31/07, Kubernetes é over-engineering. Avaliar apenas após confirmação de escala.
- **Docker Compose já é suficiente** para o MVP: define o container da app + PostgreSQL + volume de dados.

### 4.2 Service Mesh

- Istio, Linkerd ou Consul Connect não se justificam no estágio atual.
- Aplicação monolítica com uma única API. Service mesh só seria relevante com múltiplos serviços, retry policies, circuit breakers — cenário não previsto para MVP.

### 4.3 Multi-Cloud

- Não se aplica neste momento. Provedor único (provavelmente Render, Fly.io ou uma VPS) é a abordagem correta para MVP.
- Para multi-cloud no futuro, considerar containerização (já resolvido com Docker) e armazenamento externalizado (S3-compatible para arquivos, PostgreSQL gerenciado).

### 4.4 Cache e Filas

- **CRONOGRAMA.md** explicitamente exclui RabbitMQ e Celery do MVP.
- Redis poderia ser útil para cache de consultas de API e sessão, mas não é necessário para o fluxo sincrono do MVP.

### 4.5 Infraestrutura como Código

- Terraform ou Pulumi para provisionamento de cloud — não necessário para MVP com deploy simplificado.
- Ansible para configurar VPS — opcional, mas recomendado se for usar servidor bare-metal/VPS.

---

## 5. Riscos

### 5.1 Riscos de Downtime

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-----------:|:-------:|-----------|
| Sem health check adequado | Alta | Médio | Implementar `/health` com verificação de DB |
| Sem containerização | Alta | Alto | Dockerizar antes do deploy |
| Sem script de entrypoint | Média | Alto | Criar `entrypoint.sh` |
| Sem rollback automatizado | Alta | Alto | Docker + tag versionada permite rollback simples |

### 5.2 Riscos de Segurança

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-----------:|:-------:|-----------|
| `DEBUG=True` em produção se env var não for setada | Alta | Crítico | Remover fallback de DEBUG ou validar em `ready()` |
| `SECRET_KEY` com fallback inseguro | Média | Crítico | Remover fallback, lançar exceção se não definida |
| SQLite em produção | Média | Alto | PostgreSQL obrigatório |
| Log não sanejado | Média | Alto | Configurar logging com filtro de dados sensíveis |
| Sem CORS | Média | Médio | Adicionar `django-cors-headers` |
| Sem HTTPS | Baixa (se atrás de proxy) | Alto | Configurar `SECURE_*` settings |

### 5.3 Riscos de Configuração Incorreta

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-----------:|:-------:|-----------|
| `DJANGO_SETTINGS_MODULE` fixo | Alta | Alto | Usar env var para selecionar settings module |
| Sem validação de env vars em startup | Alta | Médio | Adicionar validação com `django-environ` ou `pydantic-settings` |
| Falta de `.env.example` | Média | Médio | Criar `.env.example` com todas as vars documentadas |

### 5.4 Riscos de Vazamento de Secrets

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-----------:|:-------:|-----------|
| `.env` versionado | Baixa (.gitignore correto) | Crítico | Verificar `git status` antes de commits |
| Secrets em logs | Média | Alto | Configurar filtro de logging |
| API Key hardcoded | Variável (não implementado ainda) | Crítico | Usar env var para API Key |

---

## 6. Recomendações Priorizadas

### P0 — Bloqueantes (resolver antes de qualquer deploy)

| # | Ação | Arquivos envolvidos | Esforço |
|---|------|-------------------|:-------:|
| 1 | **Criar Dockerfile e docker-compose.yml** com app + PostgreSQL. Definir `entrypoint.sh` que rode migrations e inicie o servidor. | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `entrypoint.sh` | 2h |
| 2 | **Remover fallbacks inseguros** de `SECRET_KEY` e `DEBUG`. Validar em `AppConfig.ready()` ou `settings.py` que as vars obrigatórias existem. | `config/settings.py:7-8`, `src/apps.py` | 30min |
| 3 | **Adicionar suporte a PostgreSQL** via `DATABASE_URL` ou vars individuais. Usar `dj-database-url` ou `django-environ`. Adicionar `psycopg2-binary` ao `requirements.txt`. | `config/settings.py:29-34`, `requirements.txt` | 1h |
| 4 | **Adicionar `gunicorn`** ao `requirements.txt` e configurar `docker-compose` para usá-lo como servidor WSGI. | `requirements.txt`, `docker-compose.yml` | 30min |
| 5 | **Adicionar `python-dotenv`** e carregar `.env` se existir (dev) ou usar vars do ambiente (production). | `config/settings.py`, `manage.py`, `requirements.txt` | 30min |
| 6 | **Configurar logging** no Django (`LOGGING` dict): console + arquivo rotacionado, níveis por ambiente, filtro para dados sensíveis. | `config/settings.py` | 1h |
| 7 | **Criar `.env.example`** com todas as variáveis de ambiente documentadas (DJANGO_SECRET_KEY, DJANGO_DEBUG, DATABASE_URL, DJANGO_ALLOWED_HOSTS, EMAIL_*, API_KEY). | `.env.example` | 30min |

### P1 — Importantes (resolver antes do go-live)

| # | Ação | Arquivos envolvidos | Esforço |
|---|------|-------------------|:-------:|
| 8 | **Configurar `SECURE_PROXY_SSL_HEADER` e demais `SECURE_*` settings** (HSTS, SSL redirect, cookie secure). | `config/settings.py` | 30min |
| 9 | **Melhorar `/health` endpoint** para verificar conectividade com banco de dados e estado da aplicação (liveness + readiness). | `src/routes/health.py` | 1h |
| 10 | **Adicionar Sentry** (`sentry-sdk`) para monitoramento de erros em produção. | `config/settings.py`, `requirements.txt` | 1h |
| 11 | **Congelar dependências com lock file.** Usar `pip freeze > requirements.lock` ou migrar para Poetry. | `requirements.txt` (ou `pyproject.toml` + `poetry.lock`) | 1h |
| 12 | **Criar script de entrypoint** que execute `migrate`, valide env vars, colete static files (se aplicável) e inicie Gunicorn. | `entrypoint.sh` (ou `entrypoint.py`) | 1h |
| 13 | **Configurar CI/CD básico** (GitHub Actions): rodar `python manage.py test` em push/PR. Se deploy for automatizado, adicionar step de deploy. | `.github/workflows/ci.yml` | 2h |

### P2 — Melhorias Futuras

| # | Ação | Esforço |
|---|------|:-------:|
| 14 | Migrar para `pyproject.toml` com Poetry (gestão de dependências moderna). | 2h |
| 15 | Adicionar `django-cors-headers` se a API for consumida por frontend web. | 30min |
| 16 | Adicionar `whitenoise` para servir static files (necessário apenas se Django Admin ou drf-spectacular forem ativados). | 1h |
| 17 | Migrar para ASGI (uvicorn + django-channels ou starlette) se houver necessidade de websockets ou alta concorrência. | 4h+ |
| 18 | Kubernetes manifests (`deployment.yaml`, `service.yaml`, `ingress.yaml`, `configmap.yaml`, `secret.yaml`). | 4h |
| 19 | Terraform para provisionamento de infraestrutura cloud. | 4h+ |
| 20 | Prometheus + Grafana para métricas de aplicação. | 4h+ |

---

## 7. Checklist de Go-Live

Para colocar em produção com segurança (MVP), a sequência recomendada é:

1. ✅ **Dockerizar** (P0 #1 + #4) — empacota a aplicação
2. ✅ **PostgreSQL** (P0 #3) — banco adequado
3. ✅ **Env vars** (P0 #2 + #5 + #7) — segurança básica
4. ✅ **Logging** (P0 #6) — visibilidade
5. ✅ **Script de entrypoint** (P1 #12) — inicialização confiável
6. ✅ **HTTPS/Proxy** (P1 #8) — segurança de transporte
7. ✅ **Health check** (P1 #9) — readiness para orquestração
8. ✅ **Sentry** (P1 #10) — monitoramento de erros
9. ✅ **CI** (P1 #13) — validação automatizada

O prazo do cronograma (31/07) é apertado. Recomenda-se priorizar os itens P0 e ignorar P2 por ora, conforme a própria regra de ouro do projeto: "funciona > perfeito".

---

## 8. Resumo da Arquitetura-Alvo de Deploy

```
                    +-----------+
                    |  Cliente  |
                    +-----+-----+
                          |
                        HTTPS
                          |
                    +-----+--------+
                    |  Proxy Reverso |
                    | (nginx/Caddy)  |
                    +-----+---------+
                          |
                    +-----+---------+
                    |  Gunicorn      |  (container)
                    | Django/DRF     |
                    +-----+---------+
                          |
                    +-----+---------+
                    |  PostgreSQL   |  (container ou gerenciado)
                    +---------------+

Variáveis de ambiente: .env (dev) ou env do container (prod)
Monitoramento: Sentry para erros, logs via stdout (JSON) para Loki/ELK
```

---

## 9. Referências

- `config/settings.py` — configuração atual (47 linhas, monolítica)
- `CLOUD.md` — diretrizes de cloud (env vars, PostgreSQL, sem secrets em código)
- `SECURITY.md` — diretrizes de segurança
- `CRONOGRAMA.md` — cronograma do MVP com datas e entregáveis
- `.gitignore` — exclusão de secrets e artefatos
- `README.md` — documentação do projeto
