# Análise da Camada de API & Transport Layer

## Escopo analisado

| Componente | Arquivo |
|---|---|
| Views (endpoints) | `src/routes/views.py` |
| Rotas locais | `src/routes/urls.py` |
| Rotas globais | `config/urls.py` |
| Configuração DRF | `config/settings.py` |
| Serviço de monitoramento | `src/services/monitoramento.py` |

---

## 1. Prontidão para Produção

Aspectos já adequados:

- **Uso do DRF `@api_view`**: As views usam o decorador correto do DRF, garantindo parsing de JSON, negociação de conteúdo e métodos HTTP não permitidos (405) de forma nativa.
- **Separação de responsabilidades**: Views são finas — delegam para `src.services.monitorar_lote` que por sua vez usa `src.validators.validar_lote`. Cadeia clara e testável.
- **Códigos HTTP corretos**: `200 OK` para lote válido, `400 Bad Request` para lote inválido.
- **Testes de rota existentes**: `BackendRouteTests` em `tests/test_backend.py` cobre os dois endpoints com `APISimpleTestCase`.
- **WSGI configurado**: `config/wsgi.py` pronto para deploy em servidores WSGI (Gunicorn, uWSGI).
- **Health check funcional**: `GET /health` retorna `{"status": "ok"}` — ponto de partida para sondas de load balancer.

---

## 2. Gaps Críticos (P0) — Bloqueantes para produção

### 2.1 Autenticação/Autorização

**Problema**: Zero. A configuração do DRF desabilita explicitamente qualquer autenticação:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}
```

Não há `django-cors-headers`, não há `django-rest-framework-simplejwt`, não há API Key middleware, não há SessionMiddleware, não há `AuthenticationMiddleware`. Qualquer requisição anônima é processada sem verificação.

**Impacto**: Um atacante pode:
- Validar lotes de terceiros (enumerar produtos, códigos, datas de validade — vazamento de informação comercial)
- Consumir recursos do servidor sem restrição

O cronograma (`CRONOGRAMA.md`) menciona "API Key fixa no `.env`" como planejado para a semana de 24/07, mas **não foi implementado ainda**.

### 2.2 Validação de entrada

**Problema**: A validação existe em `src/validators/lote.py` e cobre todos os 6 campos do payload, mas há fragilidades:

1. **Payload não-JSON**: Se o cliente enviar um corpo não-JSON (ex.: `Content-Type: text/plain`), o DRF retorna `{"detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"}` com status 400. Isso é razoável, mas não segue o formato de erro padronizado da aplicação.
2. **Payload não-dict**: `validar_lote` trata `not isinstance(payload, dict)` e retorna erro em português, mas a chamada em `views.py:16` (`monitorar_lote(request.data)`) passa o dado bruto sem validação prévia no nível da view.
3. **Boolean como quantidade**: O validator explicitamente rejeita booleanos com `isinstance(quantidade, bool)`, o que é correto, mas incomum — desenvolvedores podem estranhar.
4. **Erro sem campo específico**: Se o payload não for dict, o erro é `{"payload": ["O corpo da requisicao deve ser um objeto JSON."]}` — o campo `payload` não faz parte do contrato esperado pelo cliente. Seria mais consistente retornar o erro como `{"erros": {"_body": ["..."]}}` ou similar.

**Formato de erro**: O erro é retornado via `resultado.para_resposta()`, que coloca o dicionário de erros dentro da chave `"erros"`. Isso é **aceitável**, mas **não documentado externamente** (sem OpenAPI).

### 2.3 Tratamento de erros não esperados

**Problema**: Não há handler global de exceções.

O que acontece com exceções não tratadas:

| Exceção | Resultado atual | Impacto |
|---|---|---|
| `ValidationError` no validator | Retorna 400 | OK (tratado) |
| Erro de conexão com banco | Django 500 HTML | Cliente JSON quebra |
| `AttributeError` no serviço | Django 500 HTML | Cliente JSON quebra |
| `ParseError` do DRF (JSON mal formatado) | DRF retorna 400 JSON | Parcialmente OK, mas mensagem em inglês |
| Erro inesperado qualquer | Página HTML de erro do Django | **Vazamento de informação em DEBUG=True** |

A configuração atual:

```python
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
```

O padrão é `"true"` — se a variável `DJANGO_DEBUG` não for configurada em produção, o servidor rodará em modo DEBUG, expondo tracebacks completos via HTTP.

**Recomendação crítica**: Configurar `EXCEPTION_HANDLER` no DRF e `handler500`/`handler404` no Django para retornar JSON sempre.

### 2.4 Rate limiting

**Problema**: Não há nenhum throttling configurado:

```python
REST_FRAMEWORK = {
    # ...
    # DEFAULT_THROTTLE_CLASSES ausente
    # DEFAULT_THROTTLE_RATES ausente
}
```

**Impacto**: Um atacante pode bombardear `POST /lotes/validar` sem limite, consumindo CPU com validações e, futuramente, consultas a banco e integrações externas.

### 2.5 Versionamento da API

**Problema**: As rotas não são versionadas:

```
/health
/lotes/validar
```

Não há prefixo `/api/v1/` ou qualquer mecanismo de versionamento (DRF `DEFAULT_VERSIONING_CLASS`, cabeçalho `Accept`, parâmetro de URL). O cronograma planeja migrar para `/api/v1/lotes/validar`, o que quebraria clientes que usam a rota atual.

**Impacto**: Qualquer mudança no contrato (renomear campos, adicionar campos obrigatórios, alterar semântica) quebra todos os consumidores simultaneamente. Sem versionamento, não há período de coexistência.

### 2.6 CORS

**Problema**: `django-cors-headers` não está instalado nem configurado.

- `INSTALLED_APPS` não inclui `corsheaders`
- `MIDDLEWARE` não inclui `CorsMiddleware`
- Nenhuma configuração `CORS_*` está presente

**Impacto**: Um frontend SPA hospedado em domínio diferente não conseguirá chamar a API. O navegador bloqueará a requisição por política de mesma origem. Atualmente isso pode ser intencional (se o único cliente for servidor), mas precisa ser **explícito e documentado**.

### 2.7 Métodos HTTP não permitidos

**Status**: **Adequado**. O `@api_view(["GET"])` e `@api_view(["POST"])` garantem que DRF retorne `405 Method Not Allowed` automaticamente. Testado implicitamente — qualquer método diferente retorna erro.

### 2.8 Content-Type

**Status**: **Adequado para MVP**. O DRF, por padrão, parseia `application/json`, `application/x-www-form-urlencoded` e `multipart/form-data`. Se o cliente enviar `Content-Type` não suportado, o DRF retorna `415 Unsupported Media Type`. Isso é suficiente para o cenário atual.

---

## 3. Gaps Importantes (P1) — Deveriam ser resolvidos antes do go-live

### 3.1 Documentação OpenAPI

**Problema**: Inexistente. Não há `drf-spectacular`, `drf-yasg` ou qualquer schema OpenAPI. Os consumidores da API precisam ler o código-fonte para entender o contrato.

O cronograma prevê configuração do `drf-spectacular` para 28/07 (semana do go-live), mas não foi implementado.

**Impacto**:
- Consumidores externos não têm como descobrir a API
- Impossível gerar clientes automaticamente
- Difícil validar o contrato durante code review

### 3.2 Formato de resposta padronizado

**Problema**: Dois endpoints com formatos diferentes:

- `GET /health` → `{"status": "ok"}`
- `POST /lotes/validar` → `{"valido": bool, "dias_restantes": ..., "classificacao": ..., "erros": {...}}`

Não há um envelope padrão como `{"data": ..., "meta": {...}}` ou `{"success": bool, "data": ..., "errors": [...]}`.

**Impacto**: Clientes precisam tratar cada resposta de forma específica. Futuros endpoints podem adotar formatos inconsistentes. Erros de servidor (500) retornam HTML, não JSON.

### 3.3 Headers de resposta

| Header | Status | Problema |
|---|---|---|
| `Content-Type` | ✅ Adequado | DRF retorna `application/json` |
| `X-Request-ID` | ❌ Ausente | Sem rastreabilidade de requisições |
| `Cache-Control` | ❌ Ausente | GET futuros podem ser cacheados indevidamente |
| `X-Content-Type-Options` | ✅ Parcial | `SecurityMiddleware` do Django adiciona `nosniff` |
| `Strict-Transport-Security` | ✅ Parcial | `SecurityMiddleware` adiciona se `SECURE_HSTS_SECONDS` configurado (não está) |

---

## 4. Melhorias Futuras (P2)

- **Paginação e filtros**: Para futuros endpoints `GET /api/v1/lotes` — uso de `PageNumberPagination` ou `CursorPagination` do DRF, filtros por `codigo_produto`, `lote`, `classificacao`.
- **HATEOAS**: Links de navegação nas respostas (ex.: `"self"`, `"next"`, `"prev"`, `"validar"`).
- **Webhooks**: Disparo de alertas via webhook quando lotes críticos forem identificados.
- **Bulk validation**: Endpoint `POST /api/v1/lotes/validar-muitos` para validar múltiplos lotes em uma chamada.
- **Compressão**: Habilitar `GZipMiddleware` para respostas grandes em listagens futuras.
- **Logging de requisições**: Middleware para log estruturado de todas as chamadas (método, path, status, duração).

---

## 5. Riscos

### Segurança

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Acesso não autenticado** (P0) | Alta | Médio (vazamento de dados de produtos e lotes) | Implementar API Key middleware |
| **DEBUG ativo em produção** (P0) | Média | Alto (traceback de erros expõe estrutura interna) | Garantir `DJANGO_DEBUG=false` no ambiente de produção |
| **SECRET_KEY padrão** (P0) | Alta | Alto (chave conhecida publicamente — permite forjar sessões e tokens) | Sobrescrever via `DJANGO_SECRET_KEY` no ambiente |
| **Sem rate limiting** (P0) | Média | Médio (ataque de negação de serviço simples) | Configurar throttling do DRF |
| **Erro retorna HTML** (P0) | Média | Médio (cliente JSON não consegue interpretar) | Custom exception handler |

### Performance

| Risco | Descrição |
|---|---|
| **Sem cache** | Requisições repetidas ao mesmo lote reprocessam validação. Para MVP pode ser aceitável, mas com crescimento será custoso. |
| **Payload grande** | Nenhum limite de tamanho de request configurado (`DATA_UPLOAD_MAX_MEMORY_SIZE` padrão é 2.5MB). |

### Manutenibilidade

| Risco | Descrição |
|---|---|
| **Sem OpenAPI** | Contrato não documentado — difícil onboard de novos desenvolvedores e consumidores. |
| **Sem versionamento** | Qualquer mudança no contrato quebra todos os clientes. |
| **Sem request ID** | Rastrear requisições com problema em logs é praticamente impossível. |

---

## 6. Recomendações Priorizadas

### P0 — Bloqueantes (resolver antes do go-live)

| # | Ação | Esforço | Detalhes |
|---|---|---|---|
| 1 | **Implementar autenticação por API Key** | 1 dia | Middleware simples que lê `X-API-Key` do header e compara com valor do `.env`. Apenas para `POST /lotes/validar`. Conforme planejado em `CRONOGRAMA.md`. |
| 2 | **Custom exception handler global** | 0.5 dia | Configurar `EXCEPTION_HANDLER` no DRF que retorna `{"erro": "mensagem", "codigo": "ERROR_CODE"}` para qualquer exceção. Incluir handler para 500 que loga o erro internamente e retorna JSON genérico. |
| 3 | **Garantir DEBUG=False em produção** | 0.1 dia | Documentar no `.env.example` e no playbook de deploy que `DJANGO_DEBUG=false` é obrigatório. |
| 4 | **Configurar rate limiting** | 0.5 dia | Adicionar `DEFAULT_THROTTLE_CLASSES` e `DEFAULT_THROTTLE_RATES` no `REST_FRAMEWORK`. Ex.: `100/hora` para `POST /lotes/validar`. |
| 5 | **Versionar rotas** | 0.5 dia | Mover endpoints para `/api/v1/health` e `/api/v1/lotes/validar`. Manter redirecionamento ou deprecação das rotas antigas. |

### P1 — Importantes (resolver antes do go-live)

| # | Ação | Esforço | Detalhes |
|---|---|---|---|
| 6 | **Configurar `drf-spectacular` para OpenAPI** | 1 dia | Gerar schema automático. Adicionar `SPECTACULAR_SETTINGS` com descrição, versão, servidores. |
| 7 | **Adicionar `X-Request-ID`** | 0.5 dia | Middleware que gera UUID para cada requisição e retorna no header. Incluir nos logs. |
| 8 | **Documentar variáveis de ambiente sensíveis** | 0.2 dia | Criar `.env.example` com `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `API_KEY`. |
| 9 | **Configurar `ALLOWED_HOSTS` restritivamente** | 0.1 dia | Em produção, definir apenas o domínio do servidor (ex.: `api.logvencimentos.com.br`). |
| 10 | **Adicionar `django-cors-headers` se houver frontend web** | 0.5 dia | Instalar, adicionar ao `INSTALLED_APPS` e `MIDDLEWARE`, configurar `CORS_ALLOWED_ORIGINS`. |

### P2 — Melhorias futuras

| # | Ação | Esforço |
|---|---|---|
| 11 | Padronizar envelope de resposta (`{"data": ..., "meta": {"request_id": "..."}}`) | 1 dia |
| 12 | Implementar paginação e filtros para endpoints de listagem futuros | 2 dias |
| 13 | Configurar `Cache-Control` para endpoints GET futuros | 0.2 dia |
| 14 | Implementar logging estruturado com request ID | 1 dia |
| 15 | Documentar OpenAPI com exemplos de requisição/resposta | 0.5 dia |

---

## Resumo da Matriz de Gaps

| Categoria | Status | Nota |
|---|---|---|
| Autenticação | 🔴 Crítico | Nenhuma |
| Autorização | 🔴 Crítico | Nenhuma |
| Validação de entrada | 🟡 Parcial | Cobre campos, mas sem camada de view |
| Exception handling | 🔴 Crítico | Sem handler global, 500 retorna HTML |
| Rate limiting | 🔴 Crítico | Nenhum |
| Versionamento | 🔴 Crítico | Nenhum |
| CORS | 🔴 Crítico | Não configurado (pode ser intencional) |
| Métodos HTTP | 🟢 Ok | DRF gerencia corretamente |
| Content-Type | 🟢 Ok | DRF gerencia corretamente |
| OpenAPI | 🟡 Ausente | Planejado mas não feito |
| Resposta padronizada | 🟡 Parcial | Dois endpoints com formatos distintos |
| Headers de resposta | 🟡 Ausente | Falta `X-Request-ID`, `Cache-Control` |

---

*Análise realizada em 19/07/2026 com base no código-fonte da branch atual.*
