# Análise de Arquitetura — Camada de Integrações Externas

**Data:** 2026-07-19
**Escopo:** `src/integrations/`, contratos, testes e documentação associada
**Classificação:** ⚠️ PRÉ-PRODUÇÃO — MÚLTIPLOS GAPS CRÍTICOS

---

## 1. Prontidão para Produção

### O que já está adequado

| Item | Status | Evidência |
|------|--------|-----------|
| Contrato de leitura (porta) | ✅ Adequado | `AdaptadorFonteExterna` define `obter_registros()` — sem métodos de escrita |
| Especialização por domínio | ✅ Adequado | `AdaptadorConsultaERP` herda da porta genérica e restringe escopo a lotes |
| Modos de integração | ✅ Adequado | `ModoIntegracao` (`EVENTO`, `CONSULTA_AGENDADA`, `ARQUIVO`) cobre os cenários esperados |
| Contrato de mapeamento | ✅ Adequado | `MapeadorCampos` define `mapear()` sem acoplar a regras de negócio |
| Testes de contrato | ✅ Adequado | `test_backend.py:146-161` garante que os 3 modos existem, `obter_registros` é abstrato e `mapear` é abstrato |
| Testes de adaptador fake | ✅ Adequado | `test_backend.py:124-143` valida delegação e ausência de métodos de escrita |
| Documentação da visão futura | ✅ Adequado | `docs/atlas_api_futura.md` e `docs/backend.md` registram direção sem antecipar implementação |

**Resumo:** A camada segue corretamente o padrão **Ports & Adapters** (Arquitetura Hexagonal). Os contratos estão limpos, sem vazamento de tecnologia, e os testes provam que os contratos funcionam. O design está pronto. A **implementação** não começou.

---

## 2. Gaps Críticos (P0) — Bloqueantes para Produção

### 2.1 Ausência de Adaptador Concreto

**Problema:** `AdaptadorConsultaERP` e `AdaptadorFonteExterna` são classes abstratas (`ABC`). Não existe uma única classe concreta que realize uma chamada HTTP, leia um arquivo ou consuma uma fila.

**Arquivos afetados:**
- `src/integrations/erp.py` — Apenas contrato
- `src/integrations/base.py` — Apenas contrato

**Impacto:** Em produção, o sistema **não consegue obter nenhum dado real**. A função `monitorar_lote` em `src/services/monitoramento.py` recebe dados por parâmetro — não há pipeline que alimente dados do ERP no sistema.

**Evidência:**
```python
# erp.py — Único método é abstrato
@abstractmethod
def consultar_lotes(self) -> Iterable[Mapping[str, Any]]:
    raise NotImplementedError
```

**Recomendação P0:** Implementar ao menos um adaptador concreto. Por exemplo:
- `AdaptadorConsultaERPHTTP` — faz requisição REST ao ERP
- `AdaptadorConsultaERPArquivo` — lê arquivo CSV/JSON para cenário offline/teste

### 2.2 Resiliência Zero

**Problema:** Não existe qualquer mecanismo de resiliência:

| Mecanismo | Presente? | Local |
|-----------|-----------|-------|
| Retry (exponencial ou fixo) | ❌ | Inexistente |
| Circuit Breaker | ❌ | Inexistente |
| Timeout por chamada | ❌ | Inexistente |
| Fallback (dados offline/cache) | ❌ | Inexistente |
| Graceful degradation | ❌ | Inexistente |

**Evidência:** Busca por `retry`, `circuit_breaker`, `timeout`, `fallback` na árvore `src/` — zero resultados.

**Impacto:** Se o ERP externo estiver fora do ar:
1. A chamada `consultar_lotes()` simplesmente lança exceção ou trava indefinidamente
2. O sistema não tem fallback para dados previamente obtidos
3. Não há degradação graciosa — o sistema inteiro pode falhar se o ERP falhar

**Recomendação P0:**
```python
# Exemplo mínimo de adaptador resiliente
class AdaptadorConsultaERPHTTP(AdaptadorConsultaERP):
    def __init__(self, base_url: str, timeout: int = 10):
        self._session = requests.Session()
        self._session.timeout = timeout
        self._retries = Retry(total=3, backoff_factor=0.5)

    def consultar_lotes(self) -> Iterable[Mapping[str, Any]]:
        resp = self._session.get(f"{self._base_url}/lotes")
        resp.raise_for_status()
        return resp.json()
```

### 2.3 Gerenciamento de Credenciais

**Problema:** Não existe qualquer mecanismo para gerenciar credenciais de sistemas externos.

**Evidências:**
- `grep os.environ` em `src/` — zero resultados
- Nenhum arquivo `.env` no repositório
- Nenhuma variável de configuração para `API_KEY`, `ERP_URL`, `ERP_USER`, etc.
- `requirements.txt` não inclui `python-dotenv` ou biblioteca similar

**Risco:** Quando um adaptador concreto for implementado, as credenciais provavelmente serão hardcoded ou pedidas em runtime — ambas abordagens inseguras para produção.

**Recomendação P0:**
- Adotar variáveis de ambiente via Django Settings (`django.conf.settings`) ou `python-dotenv`
- Criar um arquivo `.env.example` com as variáveis necessárias (sem valores reais)
- Adicionar `.env` ao `.gitignore`

### 2.4 Mapeador de Campos Sem Implementação

**Problema:** `MapeadorCampos` define apenas o contrato `mapear()`. Não há implementação concreta que traduza campos de nenhuma fonte externa para o payload canônico do sistema.

**Evidência:**
```python
class MapeadorCampos(ABC):
    @abstractmethod
    def mapear(self, registro: Mapping[str, Any]) -> dict[str, Any]:
        """Mapeia campos sem validar regras de negocio."""
```

**Impacto:** Mesmo que um adaptador concreto exista, os dados brutos do ERP não seriam traduzidos para o formato esperado pelo `validar_lote` e `monitorar_lote`.

**Recomendação P0:** Implementar `MapeadorCamposERP` com base no contrato documentado em `docs/backend.md` (campos: `codigo_produto`, `nome_produto`, `lote`, `quantidade`, `data_validade`, `local`).

---

## 3. Gaps Importantes (P1) — Pré-Go-Live

### 3.1 Logging de Integrações

**Problema:** Nenhuma chamada a sistema externo é logada.

**O que falta:**
- Log com timestamp de início e fim da chamada
- Duração da chamada (latência)
- Status code HTTP retornado
- Payload sanitizado (sem dados sensíveis como senhas)

**Recomendação P1:** Implementar logging estruturado no adaptador base ou via decorator/middleware.

```python
import logging
import time

logger = logging.getLogger(__name__)

class AdaptadorComLogging(AdaptadorConsultaERP):
    def consultar_lotes(self) -> Iterable[Mapping[str, Any]]:
        inicio = time.monotonic()
        try:
            resultado = super().consultar_lotes()
            logger.info("ERP consultado", extra={
                "duration_ms": (time.monotonic() - inicio) * 1000,
                "status": "sucesso",
                "registros": len(list(resultado)),
            })
            return resultado
        except Exception as exc:
            logger.error("Falha ao consultar ERP", extra={
                "duration_ms": (time.monotonic() - inicio) * 1000,
                "status": "erro",
                "erro": str(exc),
            })
            raise
```

### 3.2 Métricas de Integração

**Problema:** Sem métricas, não é possível monitorar a saúde da integração em produção.

**O que falta:**
- Taxa de sucesso/erro por chamada
- Latência (p50, p95, p99)
- Throughput (chamadas/minuto)
- Contador de falhas por fonte externa

**Recomendação P1:** Expor métricas via Django middleware customizado ou integração com Prometheus (`django-prometheus`). Mínimo viável: contadores incrementados antes/depois de cada chamada externa.

### 3.3 Timeouts Não Configurados

**Problema:** Nenhum timeout está definido para chamadas externas. O Django não inclui biblioteca HTTP, mas quando uma for adicionada (`requests`, `httpx`), o timeout padrão é `None` (espera infinita).

**Recomendação P1:** Definir timeouts por fonte externa na configuração:

```python
# settings.py (futuro)
ERP_TIMEOUT_SECONDS = 10
ERP_RETRY_MAX = 3
ERP_CIRCUIT_BREAKER_THRESHOLD = 5
```

### 3.4 Rate Limiting

**Problema:** Não há controle para respeitar limites de requisição da fonte externa.

**Risco:** Se o ERP impuser limite de 100 requisições/minuto e o sistema fizer 1000 chamadas em um pico, o ERP pode bloquear o IP do Atlas.

**Recomendação P1:** Implementar rate limiter no adaptador usando `time.sleep()` ou biblioteca como `ratelimit` ou `pyrate-limiter`.

### 3.5 Idempotência

**Problema:** Consultas repetidas ao ERP podem trazer resultados diferentes (dados atualizados), mas **não há mecanismo para garantir consistência** se a mesma consulta for repetida dentro de uma mesma janela de tempo.

**Recomendação P1:** Implementar cache de curta duração (ver P2) ou hash de parâmetros de consulta para evitar chamadas duplicadas em intervalo curto.

---

## 4. Melhorias Futuras (P2)

### 4.1 Cache de Consultas

**Problema:** Atualmente, cada chamada a `obter_registros()` consulta a fonte externa.

**Recomendação P2:** Implementar cache com TTL configurável por fonte:
- Cache local (`cachetools.TTLCache`) para dados de baixa volatilidade
- Cache distribuído (Redis/Django Cache) em versão futura
- Estratégia: `Cache-Aside` — consulta cache primeiro, fallback para fonte externa

### 4.2 Webhooks

**Problema:** O sistema só suporta modo `CONSULTA_AGENDADA` e `ARQUIVO`. O modo `EVENTO` não tem implementação.

**Recomendação P2:** Criar um receptor de webhook no Django que aceite notificações do ERP quando lotes forem atualizados.

### 4.3 Filas (RabbitMQ / Celery)

**Problema:** Consultas pesadas ao ERP podem bloquear a thread do Django.

**Recomendação P2:** Para consultas de grande volume:
- Celery para tarefas assíncronas de sincronização
- RabbitMQ/Redis como broker
- Polling periódico para detectar lotes próximos ao vencimento

### 4.4 Health Check da Integração

**Problema:** A rota `/health` atual só retorna `{"status": "ok"}`, sem verificar conectividade com o ERP.

**Recomendação P2:**
```python
# GET /health → {"status": "ok", "erp": "conectado", "ultima_sincronizacao": "2026-07-19T10:00:00Z"}
```

---

## 5. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:------------:|:-------:|-----------|
| ERP externo fora do ar | Média | Alto (sistema sem dados) | Fallback com cache, circuit breaker, timeout |
| Mudança de schema do ERP | Média | Alto (mapeamento quebra) | Testes de integração com contrato versionado |
| Latência do ERP degrada API | Alta | Médio (timeout nas requisições) | Timeout configurado, métricas de latência |
| Credenciais vazadas | Baixa | Crítico | Variáveis de ambiente, secrets manager |
| Rate limit excedido | Média | Médio (bloqueio temporário) | Rate limiter no adaptador |
| Dados inconsistentes entre ERP e Atlas | Alta | Médio | Sincronização periódica, logs de divergência |
| Adaptador concreto nunca implementado | Alta | Crítico | **P0 — Bloqueante** |

---

## 6. Recomendações Priorizadas

### P0 — Bloqueantes (resolver antes de qualquer deploy)

| # | Ação | Arquivos envolvidos | Esforço estimado |
|---|------|---------------------|:----------------:|
| 1 | Implementar adaptador concreto `AdaptadorConsultaERPHTTP` com `requests` ou `httpx` | `src/integrations/erp.py`, `requirements.txt` | 2-3 dias |
| 2 | Adicionar timeouts, retry com backoff exponencial e circuit breaker | `src/integrations/base.py` (ou novo módulo `resilience.py`) | 1-2 dias |
| 3 | Implementar gerenciamento de credenciais via variáveis de ambiente + `.env.example` | `settings.py`, `.env.example`, `.gitignore` | ½ dia |
| 4 | Implementar `MapeadorCamposERP` concreto | `src/integrations/mapeamento.py` | ½ dia |
| 5 | Adicionar fallback com dados mock/offline para desenvolvimento e emergência | `src/integrations/` (novo adaptador `Arquivo`) | 1 dia |

### P1 — Pré-Go-Live (resolver antes do go-live)

| # | Ação | Esforço estimado |
|---|------|:----------------:|
| 6 | Logging estruturado de chamadas externas (duration, status, payload sanitizado) | 1 dia |
| 7 | Métricas de integração (contadores de sucesso/erro, latência) | 1-2 dias |
| 8 | Timeouts configuráveis por fonte externa em `settings.py` | ½ dia |
| 9 | Rate limiter no adaptador para respeitar limites do ERP | 1 dia |
| 10 | Idempotência com cache de curta duração (TTL de segundos) | 1 dia |

### P2 — Melhorias Futuras

| # | Ação | Esforço estimado |
|---|------|:----------------:|
| 11 | Cache distribuído (Redis) com TTL configurável | 2-3 dias |
| 12 | Receptor de webhook para modo `EVENTO` | 2-3 dias |
| 13 | Processamento assíncrono com Celery para consultas pesadas | 3-5 dias |
| 14 | Health check de integração (`/health` com status do ERP) | ½ dia |
| 15 | Documentação OpenAPI para endpoints públicos | 1 dia |

---

## Status Final

```
Camada de Integrações (src/integrations/)
├── Design (Ports & Adapters)    ✅ Pronto para produção
├── Contratos abstratos          ✅ Pronto para produção
├── Testes de contrato           ✅ Pronto para produção
├── Adaptador concreto (HTTP)    ❌ P0 — BLOQUEANTE
├── Resiliência (retry/CB/timeout) ❌ P0 — BLOQUEANTE
├── Credenciais (env vars)       ❌ P0 — BLOQUEANTE
├── Mapeador concreto            ❌ P0 — BLOQUEANTE
├── Logging de integrações       ❌ P1
├── Métricas                     ❌ P1
├── Rate limiting                ❌ P1
├── Idempotência                 ❌ P1
├── Cache                        ❌ P2
├── Webhooks                     ❌ P2
└── Filas (Celery)               ❌ P2
```

A arquitetura da camada de integrações está **conceitualmente madura**, mas **não implementada**. O sistema não consegue se conectar a nenhum sistema externo no estado atual. O esforço estimado para atingir um mínimo viável em produção é de **5 a 8 dias úteis** considerando P0s, e de **10 a 15 dias úteis** considerando P0s + P1s.
