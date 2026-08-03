# Documento Unificado de Prontidão para Produção

**Data:** 19/07/2026
**Prazo do MVP:** 31/07/2026
**Versão do código:** branch `main` (commit atual)

---

## 1. Sumário Executivo

O projeto LOG_VENCIMENTOS_APP encontra-se em **estágio inicial de desenvolvimento**. A arquitetura está conceitualmente madura — separação de responsabilidades, uso de Ports & Adapters para integrações, imutabilidade de modelos, tipagem forte — mas **nenhuma camada está totalmente pronta para produção**. O core de classificação de risco (`vencimento.py`) é o único componente que poderia ir para produção isoladamente; todo o restante requer trabalho significativo.

Foram identificados **25 gaps críticos (P0)**, **17 gaps importantes (P1)** e **22 melhorias futuras (P2)** distribuídos entre as 6 camadas analisadas. Os maiores riscos concentram-se em: (a) **ausência total de autenticação**, (b) **falta de containerização e banco inadequado (SQLite)**, e (c) **camada de integração com ERP sem implementação concreta**. O prazo de 31/07 é factível apenas para um MVP estritamente funcional (API validar+classificar sem persistência) se a equipe focar exclusivamente nos P0s mais críticos e adiar todo o resto.

---

## 2. Matriz de Prontidão por Camada

| Camada | Status | P0 | P1 | P2 | Justificativa |
|--------|--------|----|----|----|---------------|
| API & Transport | 🔴 | 6 | 3 | 6 | Sem autenticação, rate limit, exception handler global, versionamento ou CORS. Formato de resposta inconsistente entre endpoints. |
| Domínio & Serviços | 🟡 | 7 | 4 | 4 | Core de classificação sólido, mas funções não-determinísticas, NaN/Inf aceito, timezone ausente, modelo sem autoproteção. Correções são rápidas (10-30min cada). |
| Dados & Persistência | 🔴 | 5 | 5 | 3 | **Nenhum modelo Django existe.** Banco SQLite vazio. Sem migrações, índices, integridade referencial ou suporte a PostgreSQL. |
| Integrações Externas | 🔴 | 4 | 5 | 5 | Contratos abstratos corretos (Ports & Adapters), mas **nenhuma implementação concreta**. Sem resiliência, credenciais ou mapeador. |
| Infra & Deploy | 🔴 | 7 | 5 | 7 | Sem Docker, sem PostgreSQL, sem separação de ambientes, fallbacks inseguros (DEBUG=true, SECRET_KEY pública), sem logging configurado, sem HTTPS. |
| Testes & Qualidade | 🟡 | 5 | 7 | 6 | Estrutura de testes exemplar (isolados, determinísticos), mas cobertura ~66% (validador ~45%). Sem testes de segurança, CI/CD, lint ou carga. |

**Legenda:** 🟢 Pronto | 🟡 Parcial | 🔴 Não pronto

---

## 3. Gaps Críticos (P0) — Transversal e Priorizado

### 3.1 Segurança e Controle de Acesso

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.1** | API pública sem autenticação | API, Testes | `REST_FRAMEWORK` desabilita `DEFAULT_AUTHENTICATION_CLASSES` e `DEFAULT_PERMISSION_CLASSES`. Qualquer requisição anônima é processada sem verificação. | Atacante pode validar lotes de terceiros (vazamento de dados comerciais), consumir recursos sem restrição. | 1 dia |
| **P0.2** | DEBUG=true como fallback em produção | Infra | `DJANGO_DEBUG` com fallback `"true"`. Se a env var não for definida em produção, tracebacks completos são expostos via HTTP. | Exposição da estrutura interna do sistema (caminhos de arquivo, variáveis, stack traces). | 0,1 dia |
| **P0.3** | SECRET_KEY com fallback inseguro | Infra | `DJANGO_SECRET_KEY` com fallback `"unsafe-development-key"`, valor público e conhecido. | Permite forjar sessões, tokens CSRF, assinaturas. | 0,1 dia |
| **P0.4** | Rate limiting ausente | API, Testes | Nenhum throttling configurado no DRF. Sem proteção contra abuso de requisições. | Ataque de negação de serviço simples: bombardear `POST /lotes/validar` sem limite, consumindo CPU. | 0,5 dia |
| **P0.5** | CORS não configurado | API | `django-cors-headers` não instalado. Nenhuma configuração `CORS_*` presente. | Navegador bloqueia requisições de frontend SPA em domínio diferente. Se intencional (apenas cliente servidor), precisa ser documentado. | 0,5 dia |
| **P0.6** | HTTPS/SSL e proxy reverso não preparados | Infra | Sem `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS. | Django atrás de nginx/ALB interpreta schema errado, gera redirects para HTTP, vulnerável a downgrade. | 0,5 dia |

### 3.2 Infraestrutura e Deploy

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.7** | Docker ausente | Infra | Nenhum `Dockerfile`, `docker-compose.yml`, `.dockerignore` ou entrypoint. Aplicação não pode ser empacotada/ distribuída de forma padronizada. | Cada deploy depende de configuração manual do ambiente. Inviabiliza reprodutibilidade, testes em container e deploy em cloud. | 2h |
| **P0.8** | Separação de ambientes ausente | Infra | `settings.py` monolítico. `DJANGO_SETTINGS_MODULE` fixo em `config.settings`. Sem `settings/base.py`, `settings/dev.py`, `settings/prod.py`. | Impossível ter configurações diferentes por ambiente sem modificar o mesmo arquivo. Deploy frágil e propenso a erro humano. | 1 dia |
| **P0.9** | Logging não configurado | Infra, Domínio | Nenhum dicionário `LOGGING` no settings.py. Nenhum `import logging` nos serviços ou validadores. Logs vão apenas para stdout do servidor WSGI. | Operação cega em produção: erros passam despercebidos, impossível auditar requisições, sem rastreabilidade. | 1h |
| **P0.10** | Gerenciamento de variáveis de ambiente ausente | Infra, Integrações | Não usa `python-dotenv`, `django-environ` ou `dj-database-url`. Nenhum `.env.example`. Faltam variáveis para `DATABASE_URL`, `API_KEY`, `EMAIL_*`, `DB_*`. | Secrets seriam hardcoded quando implementados. Configuração de produção depende de documentação manual e não de código. | 1h |

### 3.3 Persistência e Dados

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.11** | Nenhum modelo Django existe | Dados | `src/models/lote.py` contém apenas uma dataclass Python. Nenhum `models.Model`. `makemigrations` não gera nada. | Nenhum dado é persistido entre requisições. Impossível consultar histórico, gerar relatórios ou rastrear alterações. | 2-3 dias |
| **P0.12** | SQLite configurado para produção | Dados, Infra | `DATABASES["default"]["ENGINE"]` é `sqlite3`. SQLite não suporta concorrência — trava em escrita simultânea. `CLOUD.md` diz para trocar por PostgreSQL mas não há mecanismo. | Primeira requisição POST simultânea causa `database is locked`. Sem suporte a pooling, SSL ou conexões concorrentes. | 1 dia |
| **P0.13** | Migrações e índices inexistentes | Dados | Nenhum arquivo em `src/migrations/`. Nenhum índice definido para campos de filtro esperados (`codigo_produto`, `data_validade`, `classificacao`). | Full scan em tabelas com milhares de registros. Impossível fazer rollback de schema. | Incluso no P0.11 |

### 3.4 Domínio e Validação

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.14** | Funções não-determinísticas (date.today()) | Domínio | `calcular_dias_restantes`, `classificar_risco`, `monitorar_lote` usam `date.today()` como fallback quando `hoje=None`. | Mesma chamada retorna resultados diferentes em dias diferentes. Testes são frágeis e não-determinísticos. Containers em fusos diferentes classificam o mesmo lote de forma distinta. | 15 min |
| **P0.15** | NaN e Infinity aceitos como quantidade | Domínio | `float('nan')` e `float('inf')` passam na validação pois são `isinstance(..., float)` e `NaN <= 0` é `False`. | NaN propaga para o banco — corrompe dados, quebra comparações e serialização JSON. | 10 min |
| **P0.16** | Timezone não definido | Domínio | Nenhuma importação de `pytz`, `zoneinfo` ou manipulação de timezone. `date.today()` retorna data local sem fuso. | Erro de classificação de 1 dia perto da meia-noite entre fusos. Ex.: cliente -03:00 às 23h → servidor UTC já é dia seguinte. | 30 min |
| **P0.17** | Sem limite de tamanho de campos texto | Domínio | Qualquer string é aceita — inclusive de 1MB. Sem `max_length` no validador. | DoS via strings longas (OOM), estouro de limite de coluna no banco, lentidão na serialização. | 10 min |
| **P0.18** | Mensagens de erro genéricas para quantidade | Domínio | `"Deve ser um numero maior que zero."` cobre 4 situações distintas (ausente, bool, não-numérico, <=0). | Cliente não consegue distinguir o erro exato para se recuperar adequadamente. | 15 min |
| **P0.19** | Modelo Lote sem autoproteção | Domínio | `Lote` é dataclass sem `__post_init__`. Pode-se criar `Lote(codigo_produto="", data_validade=date(2020,1,1))` sem validação. | Novos códigos podem pular o validador e criar instâncias inválidas. | 20 min |
| **P0.20** | Exception handler global ausente | API, Domínio | Sem `EXCEPTION_HANDLER` no DRF. Exceções não tratadas retornam página HTML de erro do Django (500). | Cliente JSON não consegue interpretar resposta. Vazamento de informação em DEBUG=True. | 0,5 dia |

### 3.5 API e Transporte

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.21** | Versionamento da API ausente | API | Rotas sem prefixo `/api/v1/`. Sem `DEFAULT_VERSIONING_CLASS`. | Qualquer mudança no contrato quebra todos os consumidores simultaneamente. Sem período de coexistência. | 0,5 dia |
| **P0.22** | Validação de payload não-dict frágil | API, Domínio | `validar_lote` recebe `request.data` sem validação prévia na view. Se payload não for dict, erro usa campo `"payload"` que não faz parte do contrato esperado. | Cliente recebe erro em formato inconsistente com o resto da API. | 15 min |
| **P0.23** | Injeção de dependência concreta | Domínio | `monitorar_lote` importa `validar_lote` e `classificar_risco` diretamente. Mock via `patch` é frágil — quebra com refatoração de imports. | Testes quebram silenciosamente com mudanças de caminho de importação. Dificulta substituição de implementações. | 15 min |

### 3.6 Integrações Externas

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.24** | Nenhum adaptador concreto de ERP | Integrações | `AdaptadorConsultaERP` e `AdaptadorFonteExterna` são classes abstratas. Não existe implementação que faça chamada HTTP, leia arquivo ou consuma fila. | Sistema **não consegue obter nenhum dado real** de fontes externas. Se MVP depende de integração, está bloqueado. | 2-3 dias |
| **P0.25** | Resiliência zero em integrações | Integrações | Sem retry, circuit breaker, timeout, fallback ou graceful degradation para chamadas externas. | Se ERP estiver fora do ar, chamada lança exceção ou trava indefinidamente. Sistema inteiro pode falhar. | 1-2 dias |
| **P0.26** | Mapeador de campos sem implementação | Integrações | `MapeadorCampos` define apenas contrato `mapear()`. Não há implementação que traduza campos do ERP para o payload canônico. | Mesmo com adaptador concreto, dados brutos do ERP não seriam traduzidos para o formato esperado por `validar_lote`. | 0,5 dia |

### 3.7 Testes e Qualidade

| ID | Título | Camada | Descrição | Impacto | Esforço |
|----|--------|--------|-----------|---------|---------|
| **P0.27** | Cobertura de testes insuficiente | Testes | ~66% geral, ~45% no validador. Cenários de borda não testados: payload não-dict, quantidade booleana/negativa/zero/NaN, strings gigantes, data como objeto date, campos extras. | Qualquer mudança no validador tem ~55% de chance de quebrar sem ser detectada. Risco de OOM não testado. | 1 dia |
| **P0.28** | Testes de segurança ausentes | Testes | Sem autenticação nem rate limiting implementados, logo sem testes para estes cenários. | Ausência de rede de proteção para a funcionalidade de segurança mais crítica. |

---

## 4. Gaps Importantes (P1)

### 4.1 Observabilidade e Monitoramento

| ID | Título | Camada | Descrição | Esforço |
|----|--------|--------|-----------|---------|
| **P1.1** | Logging estruturado nos serviços | Domínio, Integrações | Nenhum `import logging` em `services/`, `validators/` ou `integrations/`. Chamadas externas não são logadas (timestamp, duração, status). | 1 dia |
| **P1.2** | Métricas de aplicação | Domínio | Sem contadores de chamadas, sucessos/erros, distribuição de classificações, tempo de execução. | 2h |
| **P1.3** | Métricas de integração | Integrações | Sem taxa de sucesso/erro, latência (p50/p95/p99), throughput ou contador de falhas por fonte externa. | 1-2 dias |
| **P1.4** | Observabilidade (APM/Sentry) | Infra | Sem Sentry, New Relic, Datadog ou qualquer sistema de monitoramento de erros em produção. | 1 dia |
| **P1.5** | Timeouts configuráveis para integrações | Integrações | Nenhum timeout definido para chamadas externas. Quando `requests`/`httpx` for adicionado, timeout padrão é `None` (espera infinita). | 0,5 dia |

### 4.2 CI/CD e Automação

| ID | Título | Camada | Descrição | Esforço |
|----|--------|--------|-----------|---------|
| **P1.6** | CI/CD inexistente | Infra, Testes | Nenhum `.github/workflows/*.yml`. Testes não rodam automaticamente. Deploy é manual. Nada bloqueia merge com testes quebrados. | 2h |
| **P1.7** | Cobertura mínima não configurada | Testes | `pytest-cov` não instalado. Sem meta de cobertura mínima (ex.: 80%). Sem arquivo `.coveragerc`. | 0,5 dia |
| **P1.8** | Script de entrypoint ausente | Infra | Sem script que execute `migrate`, valide env vars, colete static files e inicie Gunicorn. | 1h |
| **P1.9** | Gestão de dependências frágil | Infra | `requirements.txt` com range aberto, sem lock file. Dependências de produção faltando: `gunicorn`, `psycopg2-binary`, `python-dotenv`, `sentry-sdk`. | 1h |

### 4.3 Documentação e Contrato

| ID | Título | Camada | Descrição | Esforço |
|----|--------|--------|-----------|---------|
| **P1.10** | Documentação OpenAPI ausente | API | Sem `drf-spectacular` ou `drf-yasg`. Consumidores precisam ler código-fonte para entender contrato. Cronograma prevê para 28/07. | 1 dia |
| **P1.11** | Formato de resposta padronizado | API | `GET /health` → `{"status":"ok"}`, `POST /lotes/validar` → `{"valido":..., "erros":...}`. Sem envelope padrão. | 1 dia |
| **P1.12** | `.env.example` ausente | Infra | Sem arquivo documentando variáveis de ambiente necessárias. | 0,2 dia |

### 4.4 Qualidade de Código

| ID | Título | Camada | Descrição | Esforço |
|----|--------|--------|-----------|---------|
| **P1.13** | Lint e formatação não configurados | Testes | Nenhuma ferramenta (`ruff`, `black`, `mypy`) no `requirements.txt`. Sem `pre-commit` hooks. Sem `.editorconfig`. | 0,5 dia |
| **P1.14** | Tratamento de erros de domínio | Domínio | Sem hierarquia de exceções (`ErroDominioError`, `ErroLoteInvalidoError`). Erros inesperados propagam como `Exception` genérica. | 1h |
| **P1.15** | Health check melhorado (readiness) | Infra | `/health` atual só retorna `{"status":"ok"}` sem verificar conectividade com banco. | 1h |
| **P1.16** | Rate limiter para integrações | Integrações | Sem controle para respeitar limites de requisição da fonte externa. ERP pode bloquear o IP. | 1 dia |
| **P1.17** | Testes de carga | Testes | Nenhum script de carga (k6, locust) para baseline de performance. | 1 dia |

---

## 5. Melhorias Futuras (P2)

| ID | Título | Camada | Descrição |
|----|--------|--------|-----------|
| **P2.1** | Cache de classificação (Redis) | Dados, Domínio | Cache de resultados por hash do payload + data para evitar reprocessamento. TTL configurável por fonte. |
| **P2.2** | Histórico de monitoramento | Dados | Persistir cada `ResultadoMonitoramento` em tabela própria: payload original, resultado, timestamp, usuário. |
| **P2.3** | Notificações e alertas | Domínio | Disparo de e-mail/webhook/push quando lote for classificado como VENCIDO ou CRITICO. |
| **P2.4** | Modo batch (POST /lotes/validar-muitos) | API, Domínio | Validação de múltiplos lotes em uma chamada. |
| **P2.5** | Webhooks de integração (modo EVENTO) | Integrações | Receptor de webhook para notificações do ERP quando lotes forem atualizados. |
| **P2.6** | Processamento assíncrono (Celery) | Integrações | Consultas pesadas ao ERP em background via Celery + RabbitMQ/Redis. |
| **P2.7** | HATEOAS | API | Links de navegação nas respostas REST. |
| **P2.8** | Compressão GZip | API | `GZipMiddleware` para respostas grandes. |
| **P2.9** | Logging estruturado de requisições | API | Middleware para log de todas as chamadas (método, path, status, duração). |
| **P2.10** | Paginação e filtros | API | `PageNumberPagination` ou `CursorPagination` para futuros endpoints GET. |
| **P2.11** | Migrar para Pydantic | Domínio | Substituir dataclass `Lote` por `BaseModel` do Pydantic para validação automática + schema OpenAPI. |
| **P2.12** | Testes de mutação | Testes | `mutmut` ou `cosmic-ray` para medir eficácia real dos testes. |
| **P2.13** | Property-based testing | Testes | `hypothesis` para gerar payloads aleatórios e descobrir crashes não previstos. |
| **P2.14** | pre-commit hooks | Testes | Ruff + mypy como hooks de commit. |
| **P2.15** | djang-cors-headers (se frontend web) | API | Configurar CORS para origens específicas. |
| **P2.16** | Particionamento de tabela (partitioning) | Dados | `PARTITION BY RANGE (data_analise)` para tabela `AnaliseLote`. |
| **P2.17** | Infraestrutura como Código | Infra | Terraform/Pulumi para provisionamento cloud. |
| **P2.18** | Kubernetes manifests | Infra | Quando escala justificar, criar deployment, service, ingress, configmap, secret. |
| **P2.19** | Prometheus + Grafana | Infra | Métricas de aplicação e infraestrutura. |
| **P2.20** | Tox para múltiplas versões Python | Testes | Testar em Python 3.11, 3.12, 3.13. |
| **P2.21** | Modo arquivo (AdaptadorConsultaERPArquivo) | Integrações | Leitura de CSV/JSON para cenário offline/teste. |
| **P2.22** | Idempotência com cache de curta duração | Integrações | Evitar chamadas duplicadas ao ERP em intervalo curto. |

---

## 6. Riscos Transversais

| Risco | Prob. | Impacto | Camadas Afetadas | Mitigação |
|-------|-------|---------|------------------|-----------|
| **API pública sem autenticação + DEBUG=true + SECRET_KEY insegura** | Alta | **Crítico** | API, Infra | P0.1, P0.2, P0.3 — implementar antes de qualquer exposição à rede |
| **SQLite em produção com contenção de escrita** | Alta (se deployar sem PostgreSQL) | **Alto** | Dados, Infra | P0.12 — PostgreSQL obrigatório antes do go-live |
| **NaN/Inf corrompe banco de dados** | Média | **Crítico** | Domínio, Dados | P0.15 — correção de 10 minutos, sem desculpa para não fazer |
| **Timezone errado causa classificação incorreta** | Baixa | Alto | Domínio | P0.16 — definir timezone do servidor e política de fuso |
| **Sem logging, bugs invisíveis em produção** | Alta | **Alto** | Domínio, Infra, Integrações | P0.9, P1.1 — logging é condição necessária para operar |
| **Strings gigantes causam OOM** | Baixa | **Alto** | Domínio, API | P0.17 — adicionar `max_length` de 10 minutos |
| **Sem adaptador concreto, ERP inacessível** | Alta | **Crítico** (se depender de ERP) | Integrações | P0.24 — avaliar se MVP precisa de integração real |
| **Cobertura de testes ~45% no validador** | Alta | Alto | Testes, Domínio | P0.27 — completar cenários de borda antes de alterar validador |
| **Fallback inseguro de DEBUG permite vazamento em produção** | Média | **Crítico** | Infra | P0.2 — remover fallback ou validar em startup |
| **Sem CI/CD, merge quebrado passa despercebido** | Alta | Médio | Testes, Infra | P1.6 — GitHub Actions mínimo em 2h |
| **Sem certificado SSL/HSTS** | Baixa (se atrás de proxy) | Alto | Infra | P0.6 — configurar `SECURE_*` settings |

---

## 7. Roadmap Recomendado

### Fase 0 — Imediata (antes de qualquer deploy público)
**Duração estimada: 2-3 dias** | **Apenas P0s que expõem risco de segurança ou corrompem dados**

| Ordem | ID | Ação | Esforço | Depende de |
|-------|----|------|---------|------------|
| 1 | P0.2 | Remover fallback de DEBUG e validar env vars em startup | 0,1 dia | — |
| 2 | P0.3 | Remover fallback de SECRET_KEY, lançar erro se não definida | 0,1 dia | — |
| 3 | P0.15 | Rejeitar NaN/Inf em quantidade (math.isfinite) | 10 min | — |
| 4 | P0.14 | Tornar `hoje: date` obrigatório em todas as funções | 15 min | — |
| 5 | P0.16 | Definir timezone do servidor (USE_TZ=True) | 30 min | — |
| 6 | P0.17 | Adicionar max_length nos campos de texto | 10 min | — |
| 7 | P0.18 | Melhorar mensagens de erro de quantidade (4 casos específicos) | 15 min | — |
| 8 | P0.19 | Adicionar __post_init__ no Lote | 20 min | — |
| 9 | P0.20 | Configurar EXCEPTION_HANDLER no DRF para JSON sempre | 0,5 dia | — |
| 10 | P0.1 | Implementar autenticação por API Key (middleware X-API-Key) | 1 dia | — |
| 11 | P0.4 | Configurar rate limiting (DEFAULT_THROTTLE_RATES) | 0,5 dia | P0.1 |
| 12 | P0.27 | Adicionar testes para cenários de borda do validador | 1 dia | P0.15-18 |
| 13 | P0.23 | Injetar validador como dependência em monitorar_lote | 15 min | — |
| 14 | P0.22 | Melhorar validação de payload não-dict na view | 15 min | — |

### Fase 1 — Pré-go-live
**Duração estimada: 4-6 dias** | **P0s restantes + P1s de infraestrutura**

| Ordem | ID | Ação | Esforço | Depende de |
|-------|----|------|---------|------------|
| 15 | P0.7 | Criar Dockerfile + docker-compose.yml com app + PostgreSQL | 2h | — |
| 16 | P0.12 | Configurar PostgreSQL via DATABASE_URL + psycopg2-binary | 1 dia | P0.7 |
| 17 | P0.11 | Criar modelos Django (AnaliseLote, Alerta, ConfiguracaoAlerta) | 2-3 dias | P0.12 |
| 18 | P0.13 | Gerar e aplicar migrations + adicionar índices compostos | incluso | P0.11 |
| 19 | P0.8 | Separar settings em base/dev/prod com DJANGO_SETTINGS_MODULE | 1 dia | — |
| 20 | P0.9 | Configurar LOGGING no Django (console + arquivo, níveis) | 1h | — |
| 21 | P0.21 | Versionar rotas (/api/v1/) com redirecionamento das antigas | 0,5 dia | — |
| 22 | P0.5 | Avaliar e configurar CORS (ou documentar decisão) | 0,5 dia | — |
| 23 | P0.6 | Configurar SECURE_* settings para HTTPS | 0,5 dia | — |
| 24 | P0.10 | Adicionar python-dotenv + .env.example com todas as vars | 1h | — |
| 25 | P1.12 | Criar .env.example completo | 0,2 dia | P0.10 |
| 26 | P1.10 | Configurar drf-spectacular para OpenAPI | 1 dia | P0.21 |
| 27 | P1.8 | Criar entrypoint.sh (migrate + validação + Gunicorn) | 1h | P0.7 |
| 28 | P1.9 | Congelar dependências com lock file + adicionar gunicorn | 1h | P0.7 |
| 29 | P1.15 | Melhorar /health com verificação de banco | 1h | P0.12 |
| 30 | P1.4 | Adicionar Sentry para monitoramento de erros | 1 dia | — |

### Fase 2 — Pós-go-live (primeiro mês)
**Duração estimada: 5-8 dias** | **P1s restantes + P2s de alto valor**

| Ordem | ID | Ação | Esforço |
|-------|----|------|---------|
| 31 | P1.6 | Configurar GitHub Actions com testes automáticos | 2h |
| 32 | P1.7 | Adicionar pytest-cov com meta de 80% de cobertura | 0,5 dia |
| 33 | P1.1 | Adicionar logging estruturado em serviços e integrações | 1 dia |
| 34 | P1.2 | Adicionar métricas de aplicação (contadores, timers) | 2h |
| 35 | P1.13 | Configurar ruff + mypy + pre-commit hooks | 0,5 dia |
| 36 | P1.14 | Criar hierarquia de exceções de domínio | 1h |
| 37 | P1.11 | Padronizar envelope de resposta da API | 1 dia |
| 38 | P1.5 | Definir timeouts configuráveis para integrações | 0,5 dia |
| 39 | P1.16 | Implementar rate limiter no adaptador de integração | 1 dia |
| 40 | P1.17 | Criar teste de carga (k6 ou locust) | 1 dia |
| 41 | P2.1 | Implementar cache de classificação (Redis ou local) | 2-3 dias |
| 42 | P2.4 | Implementar endpoint batch de validação | 2 dias |

### Fase 3 — Próximos 3 meses
**Duração estimada: continuada** | **Demais P2s**

- P2.2, P2.3 — Histórico e notificações de monitoramento
- P2.5, P2.6 — Webhooks e processamento assíncrono (Celery)
- P2.11 — Migrar para Pydantic
- P2.12, P2.13, P2.14 — Testes de mutação, property-based, pre-commit
- P2.15 — django-cors-headers (se houver frontend)
- P2.16 — Particionamento de tabela
- P2.17, P2.18, P2.19 — IaC, Kubernetes, Prometheus
- P2.20 — Tox para compatibilidade entre versões
- P2.7, P2.8, P2.9, P2.10 — HATEOAS, compressão, logging de requisições, paginação
- P2.21, P2.22 — Adaptador de arquivo e idempotência

---

## 8. Decisões de Corte (Trade-offs)

Considerando o prazo de **31/07/2026** (12 dias da data desta análise), seguem recomendações sobre o que pode ser adiado sem comprometer a segurança e funcionalidade básica do MVP:

### 🔴 BLOQUEANTE — Não pode ser adiado
| Item | Motivo |
|------|--------|
| Autenticação por API Key (P0.1) | Sem isso, qualquer pessoa na internet pode usar a API. Risco de vazamento de dados. |
| DEBUG=false + SECRET_KEY segura (P0.2, P0.3) | Sem isso, produção expõe tracebacks e permite forjar sessões. |
| Exception handler global (P0.20) | Sem isso, erros 500 retornam HTML — clientes JSON quebram. |
| NaN/Inf rejeitado (P0.15) | Corrupção de dados é irreversível. Correção de 10 min. |
| hoje obrigatório (P0.14) | Determinismo é requisito não-negociável para previsibilidade. |
| Rate limiting (P0.4) | Sem proteção mínima, DoS simples derruba o sistema. |
| Limite de tamanho de strings (P0.17) | Sem isso, payload malicioso causa OOM. |

### 🟡 ADIÁVEL (se prazo apertar) — Pode ir para pós-MVP
| Item | Condição para adiar |
|------|---------------------|
| Modelos Django + persistência (P0.11) | **Se MVP for apenas validar+classificar sem salvar.** O sistema funciona sem banco. |
| PostgreSQL + Docker (P0.7, P0.12) | **Se MVP ficar em uma VPS single-thread com SQLite.** Risco alto de lock, mas funcional para demonstração. |
| Separação de ambientes (P0.8) | Gerenciável com disciplina manual por algumas semanas. |
| Versionamento (P0.21) | Adiável se houver apenas 1 cliente conhecido. Quebra de contrato é gerenciável. |
| Logging (P0.9) | **Doloroso mas não bloqueante.** Operação cega por algumas semanas. |
| CORS (P0.5) | Adiável se não houver frontend web. |

### 🟢 ADIADO (recomendado para pós-MVP)
| Item | Justificativa |
|------|---------------|
| Integração com ERP (P0.24-P0.26) | Se MVP for alimentado manualmente ou via script único. Complexidade alta para 12 dias. |
| Adaptador concreto + resiliência | O sistema funciona sem ERP se os dados forem enviados diretamente à API. |
| OpenAPI (P1.10) | Documentação pode ser escrita manualmente em 1 página. |
| CI/CD (P1.6) | Deploy manual com checklist é aceitável para MVP de 1 desenvolvedor. |
| Observabilidade (Sentry, métricas) (P1.4) | Console logs + verificação manual são suficientes para início. |
| Testes de carga (P1.17) | Sem base de usuários, carga é imprevisível. Testar sob demanda. |
| Cache (P2.1) | Cada validação é barata (CPU puro). Cache só necessário com alto throughput. |
| Filas e processamento assíncrono (P2.6) | Síncrono é mais simples e suficiente para MVP. |
| Kubernetes, IaC, Prometheus (P2.17-P2.19) | Over-engineering para MVP. Docker Compose é suficiente. |

### Cenário "MVP Magro" (mínino para 31/07)

Caso o prazo seja realmente inflexível e a equipe seja pequena, o seguinte escopo mínimo é viável:

1. **Segurança**: API Key + DEBUG=false + SECRET_KEY + rate limiting + exception handler
2. **Domínio**: hoje obrigatório + NaN/Inf rejeitado + max_length + timezone + mensagens específicas
3. **API**: Versionamento + formato de erro consistente
4. **Testes**: Cenários de borda do validador
5. **Infra**: .env.example + LOGGING básico + gunicorn

**Total estimado: 4-5 dias para 1 desenvolvedor.**

Isso produz um MVP que:
- Aceita requisições autenticadas via API Key
- Valida e classifica lotes corretamente (sem NaN, sem erros de timezone)
- Retorna erros em JSON mesmo em cenários de falha
- Tem proteção mínima contra abuso (rate limit)
- Pode rodar em um servidor simples com `python manage.py runserver` ou Gunicorn

**Tudo que não está nesta lista (persistência, Docker, PostgreSQL, integração ERP, OpenAPI, CI/CD) é adiável para depois de 31/07.**
