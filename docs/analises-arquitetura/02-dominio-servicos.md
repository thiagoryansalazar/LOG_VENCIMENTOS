# Análise de Domínio & Serviços — Prontidão para Produção

**Data:** 2026-07-19
**Escopo:** `src/services/`, `src/validators/`, `src/models/lote.py`, `src/routes/views.py`, `tests/test_backend.py`

---

## 1. Prontidão para Produção — O que já está adequado

| Aspecto | Status | Detalhes |
|---|---|---|
| **Imutabilidade dos modelos** | ✅ Adequado | `Lote` e `ResultadoMonitoramento` usam `dataclass(frozen=True, slots=True)` — sem mutação acidental, sem dicionário `__dict__`, menor consumo de memória. |
| **Tipagem forte de classificação** | ✅ Adequado | `ClassificacaoRisco` é `StrEnum` — valores restritos, serializáveis como string nativamente. |
| **Separação de responsabilidades** | ✅ Adequado | Validação → Serviço → View, cada camada com responsabilidade única e bem definida. |
| **Padrão Result-Type (sem exceções)** | ✅ Adequado | `validar_lote` retorna `(Lote \| None, dict[str, list[str]])` em vez de lançar exceções — o fluxo de erro é explícito e previsível. |
| **Normalização de entrada** | ✅ Adequado | Campos de texto sofrem `.strip()` no validador (ex.: `" PROD-001 " → "PROD-001"`). |
| **Testes unitários rápidos** | ✅ Adequado | `SimpleTestCase` do Django (sem banco) — execução em milissegundos, sem dependências externas. |
| **Injeção de `hoje` para determinismo** | ✅ Adequado (parcial) | Quando `hoje` é passado, as funções são **puras e determinísticas**. O gap está no default (ver P0). |
| **Serialização explícita via `para_resposta()`** | ✅ Adequado | `ResultadoMonitoramento.para_resposta()` mapeia o enum `.value` para string, garantindo que a API retorne JSON válido. |
| **Uso de `date.fromisoformat`** | ✅ Adequado | Padrão ISO 8601 — portável, sem ambiguidade localizada. |

---

## 2. Gaps Críticos (P0) — Bloqueantes para Produção

### 2.1 Pureza das funções — dependência de estado global

**Arquivo:** `src/services/vencimento.py:12-17`, `src/services/monitoramento.py:32-35`

```python
def calcular_dias_restantes(data_validade: date, hoje: date | None = None) -> int:
    data_referencia = hoje or date.today()  # <-- Efeito colateral: I/O de relógio
    return (data_validade - data_referencia).days
```

**Problema:** Quando `hoje=None`, a função chama `date.today()` — uma operação de I/O que depende do relógio do sistema. Isso quebra a **pureza**:
- A mesma chamada com os mesmos argumentos pode retornar resultados diferentes em dias diferentes.
- Testes que não passam `hoje` são **frágeis e não-determinísticos**.
- Se dois componentes chamarem `monitorar_lote` no mesmo request sem `hoje`, o valor pode diferir se a execução cruzar a meia-noite.

**Prova no código:** O teste `test_interrompe_monitoramento_quando_lote_e_invalido` (`test_backend.py:115-121`) não passa `hoje` e funciona apenas porque o lote é inválido e o fluxo para antes de chamar `calcular_dias_restantes`. Se o payload fosse válido, o teste seria data-dependente.

**Teste de rota:** `test_valida_lote` (`test_backend.py:170-193`) usa `date.today()` diretamente — se rodar exatamente à meia-noite, o resultado pode variar entre execuções.

**Recomendação P0:** Remover o default `None` e tornar `hoje: date` **obrigatório** em todas as funções. A view (ou o entry-point) injeta `date.today()` em um único ponto.

---

### 2.2 Edge cases no cálculo de vencimento

#### 2.2.1 Valores especiais em `quantidade`

**Arquivo:** `src/validators/lote.py:41-47`

```python
quantidade = payload.get("quantidade")
if (
    isinstance(quantidade, bool)
    or not isinstance(quantidade, (int, float, Decimal))
    or quantidade <= 0
):
    errors["quantidade"] = ["Deve ser um numero maior que zero."]
```

**Problemas:**

| Input | `isinstance` check | `quantidade <= 0` | Resultado | Risco |
|---|---|---|---|---|
| `float('nan')` | `True` (é float) | `False` (NaN não é <= 0) | **Aceito** 🚫 | NaN propaga para o banco — corrompe dados e quebra comparações |
| `float('inf')` | `True` (é float) | `False` (inf não é <= 0) | **Aceito** 🚫 | Infinity pode quebrar serialização JSON ou causar overflow |
| `float('-inf')` | `True` (é float) | `True` | **Rejeitado** ✅ | — |
| `True` / `False` | `isinstance(..., bool)` pega primeiro | — | **Rejeitado** ✅ | — |
| `"10"` (string numérica) | `False` (não é int/float/Decimal) | — | **Rejeitado** ✅ | Mensagem de erro genérica — usuário não sabe que deveria enviar número |

**Recomendação P0:** Adicionar verificação `math.isfinite(quantidade)` ou `isinstance(quantidade, (int, Decimal))` rejeitando `float` completamente (a menos que float seja um requisito de negócio). Se float for necessário, usar `math.isfinite()`.

#### 2.2.2 Timezone — data sem fuso horário

**Problema:** `date.today()` retorna a data local do servidor **sem timezone**. Se o servidor estiver configurado em UTC e um cliente enviar no fuso -03:00, às 23:00 do cliente são 02:00 do dia seguinte no servidor. Uma data de validade "2026-07-19" pode ser interpretada como "2026-07-18" ou "2026-07-20" dependendo do momento.

**Prova:** Não há nenhuma importação de `pytz`, `zoneinfo`, ou manipulação de `datetime` com timezone em todo o código analisado.

**Recomendação P0:** Definir o timezone do servidor explicitamente (`USE_TZ = True` no `settings.py` com `TIME_ZONE` fixo). Para o cálculo de vencimento, considerar usar `datetime` com timezone-aware.

#### 2.2.3 Ano bissexto

**Status:** ✅ OK. `date.fromisoformat("2024-02-29")` funciona. `timedelta` lida com qualquer diferença de dias.

#### 2.2.4 Data exatamente hoje

**Código:** `dias_restantes <= 0 → VENCIDO`. Se a validade é hoje, o lote já é considerado vencido. Isso é uma **decisão de negócio** que deve ser validada com o domínio:
- Alguns negócios consideram o dia da validade como o último dia útil.
- Outros consideram que vence apenas no dia seguinte.
- A regra atual é **restritiva** (vence no próprio dia). Documentar e validar com stakeholders.

---

### 2.3 Validação — cobertura de tipos e valores extremos

#### 2.3.1 Comprimento de campos de texto

**Arquivo:** `src/validators/lote.py:34-39`

```python
if not isinstance(value, str) or not value.strip():
    errors[field] = ["Este campo e obrigatorio e deve ser um texto."]
```

**Problema:** Qualquer string é aceita — inclusive strings de 1MB que podem causar:
- Exaustão de memória no servidor
- Estouro de limite de coluna no banco de dados
- Lentidão na serialização da resposta

**Recomendação P0:** Adicionar validação de comprimento máximo (ex.: `len(value) > 255`).

#### 2.3.2 Mensagens de erro genéricas

**Arquivo:** `src/validators/lote.py:47`

```
"Deve ser um numero maior que zero."
```

Esta mensagem cobre 4 situações distintas:
1. O campo não foi enviado (`payload.get` retorna `None`)
2. O campo é booleano (`True`/`False`)
3. O campo não é numérico (string, lista, objeto)
4. O campo é numérico mas <= 0

O cliente não consegue distinguir qual foi o erro exato para se recuperar adequadamente — especialmente o caso 3 (string numérica como `"10"`) vs. caso 4 (número negativo).

**Recomendação P0:** Retornar mensagens de erro específicas:
- `"Campo obrigatório."` (ausente)
- `"Deve ser um número, não um booleano."` (bool)
- `"Deve ser um número."` (não-numérico)
- `"Deve ser maior que zero."` (<=0)

#### 2.3.3 Payload não-dict: erro genérico

**Arquivo:** `src/validators/lote.py:30-31`

```python
if not isinstance(payload, dict):
    return None, {"payload": ["O corpo da requisicao deve ser um objeto JSON."]}
```

Se `payload` for `None` ou uma lista vazia, a mensagem é precisa. Mas se for `None` (enviado como corpo vazio), a mensagem não orienta o cliente sobre o formato esperado. **Aceitável para P0**, mas idealmente documentar no OpenAPI/Swagger.

---

### 2.4 Modelo Lote — falta de autoproteção

**Arquivo:** `src/models/lote.py:6-13`

```python
@dataclass(frozen=True, slots=True)
class Lote:
    codigo_produto: str
    nome_produto: str
    lote: str
    quantidade: int | float | Decimal
    data_validade: date
    local: str
```

**Problemas:**

1. **Sem invariantes no construtor:** Pode-se criar `Lote(codigo_produto="", data_validade=date(2020,1,1))` sem validação. A proteção existe apenas no validador, mas se algum código novo esquecer de validar, o modelo aceita qualquer coisa.
2. **`quantidade: int | float | Decimal`** é excessivamente permissiva — `float` não é adequado para quantidades discretas. O ideal seria apenas `int` ou `Decimal` (com precisão definida).
3. **Sem validação de `data_validade`** — data no passado extremo ou ano 9999 seria aceita.
4. **Sem `__post_init__`** — não há validação executada automaticamente.

**Recomendação P0.5 (pré-P0):**
- Adicionar `__post_init__` com validações básicas (campos obrigatórios não vazios, quantidade positiva, data válida).
- Ou migrar para **Pydantic** (`BaseModel`), que fornece validação automática, coerção, serialização e geração de schema OpenAPI.
- Ou usar **DRF Serializers** para integrar validação diretamente com a view.

---

### 2.5 Injeção de dependência — acoplamento concreto

**Arquivo:** `src/services/monitoramento.py`

```python
from src.validators import validar_lote       # dependência concreta
from .vencimento import classificar_risco     # dependência concreta
```

**Problema:** `monitorar_lote` chama `validar_lote` por importação direta. Para testar com mock:
```python
with patch("src.services.monitoramento.validar_lote") as mock_val:
    ...
```
Isso é **frágil** — se o caminho de importação mudar (`from src.validators.lote import validar_lote` vs `from src.validators import validar_lote`), o mock quebra silenciosamente.

**Recomendação P0:** Injeta dependências via parâmetro:
```python
def monitorar_lote(
    payload: Any,
    hoje: date,
    validador: Callable[[Any], tuple[Lote | None, dict]] = validar_lote,
) -> ResultadoMonitoramento:
```
Isso torna a dependência explícita, testável sem `patch`, e facilita a substituição futura.

---

## 3. Gaps Importantes (P1) — Devem ser resolvidos antes do go-live

### 3.1 Logging — zero rastreabilidade

**Status:** Nenhum `import logging` ou `loguru` em `services/`, `validators/`, ou `models/`.

**Consequências:**
- Uma validação rejeitada não deixa rastro — impossível auditá-la depois.
- Um erro inesperado (ex.: `KeyError` no `payload.get`) gera traceback no console sem contexto do payload.
- Sem correlação entre chamadas da API e execução dos serviços.

**Recomendação P1:**
```python
import logging
logger = logging.getLogger(__name__)

def monitorar_lote(...):
    logger.info("monitorando_lote", extra={"codigo": payload.get("codigo_produto")})
```
Estruturar logs como JSON estruturado para ingestão por ELK/Datadog.

### 3.2 Métricas — zero observabilidade

**Status:** Nenhum contador, timer, ou gauge em toda a camada.

**Recomendação P1:**
- Contar total de chamadas a `monitorar_lote`
- Contar sucessos vs. erros de validação
- Contar distribuição de classificações (`NORMAL`, `ATENCAO`, `CRITICO`, `VENCIDO`)
- Medir tempo de execução (percentis p50, p95, p99)
- Integrar com `django-prometheus` ou `opentelemetry`

### 3.3 Tratamento de erros — sem diferenciação entre domínio e infraestrutura

**Status:** Apenas erros de validação são tratados (retorno de `dict`). Erros inesperados propagam como exceção genérica.

**Recomendação P1:**
- Criar hierarquia de exceções de domínio:
  ```python
  class ErroDominioError(Exception): ...
  class ErroLoteInvalidoError(ErroDominioError): ...
  class ErroMonitoramentoError(ErroDominioError): ...
  ```
- Diferenciar no middleware de erro da API:
  - `ErroDominioError` → retorna 400/422 com payload descritivo
  - `Exception` genérica → retorna 500, loga stacktrace, não expõe detalhes internos

### 3.4 Tratamento de payload inválido na view

**Arquivo:** `src/routes/views.py:16`

```python
resultado = monitorar_lote(request.data)
```

Se `request.data` não for serializável ou `monitorar_lote` levantar uma exceção inesperada (ex.: `AttributeError` se `payload` for um objeto inesperado), a view retorna 500 sem tratamento.

**Recomendação P1:** Envolver em try/except ou adicionar um exception handler global que transforme exceções não tratadas em respostas JSON.

---

## 4. Melhorias Futuras (P2)

### 4.1 Notificações e Alertas
- Quando um lote é classificado como `VENCIDO` ou `CRITICO`, disparar notificação (e-mail, webhook, push).
- Quando o total de lotes `VENCIDO` ultrapassar um threshold, alertar a gerência.

### 4.2 Histórico de Monitoramento
- Persistir cada `ResultadoMonitoramento` em uma tabela (`MonitoramentoHistorico`) com:
  - Payload original (ou hash)
  - Resultado
  - Timestamp
  - Usuário (se autenticado)
- Permitir consulta histórica de análises.

### 4.3 Modo Batch
- Criar `monitorar_lotes(payloads: list[Any]) -> list[ResultadoMonitoramento]` para processamento em lote.
- Útil para importação de arquivos ou integração com filas.

### 4.4 Cache de classificação
- Se o mesmo lote for consultado múltiplas vezes no mesmo dia, o resultado pode ser cacheado (chave: hash do payload + data).
- Benefício marginal (cálculo é barato), mas útil em cenários de alta frequência.

---

## 5. Riscos

| # | Risco | Prob. | Impacto | Descrição | Mitigação |
|---|---|---|---|---|---|
| R1 | **NaN/Inf aceito em `quantidade`** | Média | **Crítico** | `float('nan')` corrompe banco de dados, propagando silenciosamente | Validar com `math.isfinite()` (P0) |
| R2 | **Timezone naive causa erro de 1 dia** | Baixa | **Alto** | Classificação errada perto da meia-noite entre fusos diferentes | Usar `datetime` com timezone-aware (P0) |
| R3 | **`date.today()` sem fuso entre containers** | Média | Médio | Containers em fusos diferentes classificam o mesmo lote de forma diferente | Tornar `hoje` obrigatório (P0) |
| R4 | **Sem logging, bugs são invisíveis** | Alta | **Alto** | Erros em produção passam despercebidos sem rastreabilidade | Implementar logging estruturado (P1) |
| R5 | **Modelo sem autoproteção** | Média | Médio | Novo código pode pular validação e criar `Lote` inválido | `__post_init__` ou Pydantic (P0) |
| R6 | **Sem limite de tamanho de texto** | Baixa | Médio | DoS via strings longas ou estouro de coluna no banco | Validar `len()` máximo (P0) |
| R7 | **Mock frágil em testes** | Média | Baixo | `patch` em módulo concreto quebra com refatoração de imports | Injeção de dependência (P0) |
| R8 | **Sem autenticação na API** | Alta | **Crítico** | Qualquer um pode validar lotes sem restrição | Adicionar auth (fora do escopo desta camada) |

---

## 6. Recomendações Priorizadas

### 🔴 P0 — Bloqueantes (resolver antes de qualquer deploy)

| # | Ação | Arquivo(s) | Esforço |
|---|---|---|---|
| P0.1 | **Tornar `hoje: date` obrigatório** em `calcular_dias_restantes`, `classificar_risco`, `monitorar_lote`. Remover default `None`. | `vencimento.py`, `monitoramento.py` | 15 min |
| P0.2 | **Rejeitar `float('nan')` e `float('inf')`** em `quantidade`. Usar `math.isfinite()`. | `validators/lote.py` | 10 min |
| P0.3 | **Adicionar limite de comprimento** para campos de texto (sugestão: 255 chars). | `validators/lote.py` | 10 min |
| P0.4 | **Tornar erros de `quantidade` específicos** (ausente, bool, não-numérico, <=0). | `validators/lote.py` | 15 min |
| P0.5 | **Adicionar `__post_init__` no `Lote`** com validações básicas (strings não vazias, quantidade positiva, data válida). | `models/lote.py` | 20 min |
| P0.6 | **Injetar validador como dependência** em `monitorar_lote` para testabilidade. | `monitoramento.py` | 15 min |
| P0.7 | **Definir timezone do servidor** (`USE_TZ=True`) e decidir política de fuso para datas. | `settings.py` | 30 min |

### 🟡 P1 — Pré-go-live (resolver antes do lançamento oficial)

| # | Ação | Arquivo(s) | Esforço |
|---|---|---|---|
| P1.1 | **Adicionar logging estruturado** em `monitorar_lote` e `validar_lote`. | `services/`, `validators/` | 1h |
| P1.2 | **Adicionar métricas** (contadores de validação, classificação, erros). | `services/monitoramento.py` | 2h |
| P1.3 | **Criar exceções de domínio** e middleware de erro para diferenciar 400/422/500. | novo arquivo `exceptions.py` | 1h |
| P1.4 | **Adicionar try/except** na view para capturar erros inesperados. | `routes/views.py` | 10 min |
| P1.5 | **Atualizar testes** para usar `hoje` obrigatório e testar edge cases NaN/Inf. | `tests/test_backend.py` | 30 min |

### 🟢 P2 — Pós-go-live (melhorias futuras)

| # | Ação | Esforço |
|---|---|---|
| P2.1 | Persistir histórico de monitoramento em banco de dados. | 4h |
| P2.2 | Implementar notificações para classificações VENCIDO/CRITICO. | 4h |
| P2.3 | Criar endpoint batch `POST /lotes/validar-lote`. | 2h |
| P2.4 | Migrar `Lote` para Pydantic `BaseModel`. | 3h |

---

## Resumo dos Principais Problemas Encontrados

A camada de domínio e serviços está bem estruturada em termos de arquitetura (separação de responsabilidades, imutabilidade, padrão Result-Type), mas **não está pronta para produção** devido a gaps críticos de segurança e determinismo.

O problema mais urgente (P0) é que as funções do serviço são **não-determinísticas** por padrão (`date.today()` como fallback), o que quebra a previsibilidade do sistema e torna testes frágeis — a correção é simples (tornar `hoje` obrigatório). Em segundo lugar, o validador aceita `float('nan')` e `float('inf')` em `quantidade`, um risco de corrupção de dados que precisa ser fechado imediatamente.

Antes do go-live (P1), é obrigatório implementar logging e métricas — sem isso, a equipe estará cega para problemas em produção. A hierarquia de erros de domínio também precisa ser introduzida para que a API retorne respostas semanticamente corretas (400 vs 500).
