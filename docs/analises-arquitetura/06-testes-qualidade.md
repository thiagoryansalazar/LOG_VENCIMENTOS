# Análise da Camada de Testes & Qualidade

**Projeto:** LOG_VENCIMENTOS_APP  
**Data:** 2026-07-19  
**Responsável:** Arquitetura de Software — Testes & Qualidade  

---

## 1. Prontidão para Produção — O que já está adequado

### 1.1 Estrutura de classes de teste bem organizada

O arquivo `tests/test_backend.py` (205 linhas) contém **6 classes de teste** claramente separadas por responsabilidade:

| Classe | Responsabilidade | Tecnologia |
|---|---|---|
| `VencimentoServiceTests` | Cálculo de dias e classificação de risco | `SimpleTestCase` |
| `LoteValidatorTests` | Validação e normalização de payloads | `SimpleTestCase` |
| `MonitoramentoServiceTests` | Orquestração validação + classificação | `SimpleTestCase` |
| `AdaptadorConsultaERPTests` | Contrato da porta de integração ERP | `SimpleTestCase` |
| `IntegracaoExternaTests` | Contrato dos adaptadores externos | `SimpleTestCase` |
| `BackendRouteTests` | Endpoints HTTP (health + validar lote) | `APISimpleTestCase` |

### 1.2 Testes de contrato (port & adapter)

As classes `AdaptadorConsultaERPTests` e `IntegracaoExternaTests` verificam que:

- `AdaptadorConsultaERP` expõe `obter_registros` e delega para `consultar_lotes` corretamente
- Não há métodos de escrita públicos (`salvar`, `atualizar`) na interface
- `AdaptadorFonteExterna` declara `obter_registros` como abstrato
- `MapeadorCampos` declara `mapear` como abstrato
- `ModoIntegracao` contém exatamente os 3 modos esperados

Isso segue o padrão **Port-Adapter** e protege contra regressões no contrato das abstrações.

### 1.3 Testes de fronteira nas faixas de risco

`VencimentoServiceTests` cobre todos os limites das faixas:

- `dias_restantes <= 0` → VENCIDO (testa -1 e 0)
- `1 <= dias_restantes <= 7` → CRITICO (testa 1, 5, 7)
- `8 <= dias_restantes <= 30` → ATENCAO (testa 8, 20, 30)
- `dias_restantes >= 31` → NORMAL (testa 31, 60)

### 1.4 Isolamento dos testes

Todos os testes usam `SimpleTestCase` ou `APISimpleTestCase` do Django, que **não tocam no banco de dados**. Isso garante:

- Execução rápida (segundos)
- Sem estado compartilhado entre testes
- Sem necessidade de fixture de banco

### 1.5 Testes da API REST

`BackendRouteTests` verifica:

- `GET /health` retorna `200` com `{"status": "ok"}`
- `POST /lotes/validar` com payload válido retorna `200` com classificação correta
- `POST /lotes/validar` com payload inválido retorna `400` com erros

### 1.6 Stub/Fake em vez de mock genérico

`AdaptadorConsultaERPTests` usa uma inner class `AdaptadorFake` que implementa `consultar_lotes`. Essa abordagem é superior a mocks rasos pois valida o comportamento real da herança.

---

## 2. Gaps Críticos (P0) — Bloqueantes para Produção

### 2.1 Cobertura de testes insuficiente

**O que está coberto (aproximadamente 40% do código):**

- `vencimento.py` (32 linhas) — 100% das funções
- `monitoramento.py` (51 linhas) — 100% das funções (fluxo feliz e invariante)
- `validators/lote.py` (66 linhas) — validacao com dict valido e invalido
- `routes/views.py` (24 linhas) — ambos os endpoints
- `integrations/base.py`, `erp.py`, `mapeamento.py` — apenas contratos abstratos

**O que NÃO está coberto:**

#### 2.1.1 `validators/lote.py` — cenários de borda não testados

| Cenário | Linhas | Risco |
|---|---|---|
| `payload` não é um `dict` (ex.: string, lista, None) | 30-31 | `TypeError` não tratado → `500` |
| `quantidade` é booleano `True` ou `False` | 43 | Python trata `bool` como `int`; `True` passaria como 1 |
| `quantidade` é zero | 44-46 | Testado indiretamente |
| `quantidade` é negativa | 44-46 | **Não testado** |
| `quantidade` é string numérica ("10") | 44 | Passaria despercebido |
| `data_validade` já é um `date` (não string) | 17-18 | **Não testado** |
| `data_validade` em formato ISO com fuso horário | 22 | `date.fromisoformat` pode aceitar |
| `codigo_produto` com espaços internos | 39 | Strip só remove pontas |
| Campos extras no payload (ex.: `corrupt` ou `__proto__`) | — | **Mass assignment / prototype pollution** |
| Payload com encoding não-UTF8 ou caracteres especiais | — | Potencial `UnicodeDecodeError` |

#### 2.1.2 Nenhum teste de integração com banco de dados

O projeto usa `DATABASES = { "default": { "ENGINE": "django.db.backends.sqlite3" } }` em `config/settings.py`, mas:

- A model `Lote` em `src/models/lote.py` é uma **dataclass**, não um `django.db.models.Model`
- Nenhum teste valida leitura/escrita em banco
- Nenhuma migration Django foi gerada
- O fluxo de salvar lotes no banco (se existir) não é testado

> **Risco:** Se no futuro o `Lote` for migrado para um Django Model, não há testes de integração com banco para pegar regressões de query, transação ou concorrência.

#### 2.1.3 Nenhum teste de integração com sistemas externos

- `AdaptadorConsultaERP` e `AdaptadorFonteExterna` são classes abstratas
- Não há implementações concretas no código
- Não há testes que validem: timeout de rede, retry, fallback, autenticação, parsing de resposta HTTP, serialização SOAP/JSON/XML, etc.

> **Risco:** No momento da integração real com ERP, cada adaptador concreto será implementado sem rede de proteção de testes.

#### 2.1.4 Nenhum teste para `ResultadoMonitoramento.para_resposta()`

O método `para_resposta()` tem um branch condicional (`classificacao.value if classificacao is not None else None`) que não é testado isoladamente. Ele é exercitado apenas indiretamente pelo teste de rota.

### 2.2 Qualidade dos testes

#### 2.2.1 Testes atômicos e isolados — PONTO POSITIVO

Os testes são **independentes** (sem shared state), **determinísticos** (datas fixas) e **isolados** (sem banco). Isso é adequado.

#### 2.2.2 Testam comportamento, não implementação — PONTO POSITIVO

Os testes validam resultados (retornos, status codes, erros), não chamadas de métodos internos ou mocks de dependências. Isso é correto.

#### 2.2.3 Uso de mocks — AUSENTE

Nenhum mock do `unittest.mock` é usado. Isso é **adequado para o código atual** pois:

- As funções são puras (sem I/O, sem estado externo)
- Os adaptadores são abstratos

Porém, **quando implementações concretas de ERP forem criadas**, será necessário mockar chamadas HTTP/SOAP. A falta de experiência com mocks no projeto é um risco.

#### 2.2.4 Validação frágil em `BackendRouteTests`

```python
def test_retorna_erros_para_lote_invalido(self) -> None:
    response = self.client.post(
        "/lotes/validar",
        {"codigo_produto": "PROD-001"},
        format="json",
    )
```

Este teste envia um payload **parcial** (apenas `codigo_produto`) e espera que `"data_validade"` esteja em `response.json()["erros"]`. Porém:

- O validador exige **6 campos obrigatórios**; o teste só verifica 1 erro
- Se a implementação mudar para retornar apenas o primeiro erro, o teste ainda passa (falso positivo)
- Não verifica que **todos** os erros esperados estão presentes (`codigo_produto`, `nome_produto`, `lote`, `quantidade`, `data_validade`, `local`)

### 2.3 Ambiente de teste

#### 2.3.1 Sem configuração de banco de teste

`APISimpleTestCase` usa `settings.DATABASES` diretamente. Como `SimpleTestCase` não toca no banco, isso é seguro. Porém, se testes de integração forem adicionados, não há:

- Um `settings_test.py` com banco separado
- Um `conftest.py` para fixtures
- Um banco em memória exclusivo para testes

#### 2.3.2 Dependência de singleton Django

Os testes rodam com `DJANGO_SETTINGS_MODULE=config.settings`. A chave `SECRET_KEY` tem fallback para `"unsafe-development-key"` e `DEBUG=True` — valores inadequados para produção mas aceitáveis para teste.

#### 2.3.3 Como os testes rodam atualmente

```
python manage.py test tests
```

Isso significa que os testes dependem do Django estar instalado e configurado. Não há script de setup automatizado, nem `tox` para testar em múltiplas versões do Python.

### 2.4 Testes de segurança — AUSENTES

A API **não possui** qualquer mecanismo de autenticação ou autorização:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}
```

Não há testes para:

| Requisito | Status |
|---|---|
| Autenticação em endpoints | ❌ Não há testes porque não há autenticação |
| Rate limiting / throttling | ❌ Não configurado nem testado |
| SQL injection | ❌ Não há ORM queries expostas, mas sem testes |
| Command injection (payload malicioso) | ❌ Não testado |
| Mass assignment / extra fields no JSON | ❌ Validator ignora campos extras |
| XSS em respostas | ❌ Respostas são JSON, risco baixo |
| CSRF | ❌ CSRF desabilitado (API REST sem sessão) |

> **Conclusão P0:** A API é **publicamente acessível e sem autenticação**. Isso é aceitável para MVP interno, mas precisa ser endereçado antes de expor à internet.

---

## 3. Gaps Importantes (P1) — Antes do Go-Live

### 3.1 Pipeline de CI — INEXISTENTE

- Não há diretório `.github/workflows/`
- Não há `.gitlab-ci.yml`
- Não há `tox.ini`
- Não há `Makefile` ou `tasks.py`

**Risco:** Nada bloqueia um merge com testes quebrados. Não há garantia de que `main` esteja sempre verde.

### 3.2 Cobertura mínima — NÃO CONFIGURADA

- `.coverage` e `htmlcov/` estão no `.gitignore`, mas `pytest-cov` não está em `requirements.txt`
- Não há arquivo `.coveragerc` ou `pyproject.toml` com configuração de coverage
- Não há meta de cobertura mínima (ex.: 80%)

**Cobertura estimada manualmente:**

| Módulo | Linhas | Cobertas | % |
|---|---|---|---|
| `vencimento.py` | 32 | 32 | 100% |
| `monitoramento.py` | 51 | 51 | 100% |
| `validators/lote.py` | 66 | ~30 | ~45% |
| `routes/views.py` | 24 | 24 | 100% |
| `integrations/*.py` | 57 | ~15 | ~26% |
| **Total** | **230** | **~152** | **~66%** |

### 3.3 Testes de carga/performance — INEXISTENTES

- Nenhum script de carga (k6, locust, JMeter, vegeta)
- Nenhuma estimativa de throughput
- O endpoint `POST /lotes/validar` é puramente computacional (sem I/O), mas o `GET /health` é trivially rápido
- Sem limites configurados de conexões simultâneas

### 3.4 Lint e formatação — NÃO CONFIGURADOS

- Nenhuma ferramenta de lint no `requirements.txt`
- Nenhum `pre-commit` hook
- Nenhum `.editorconfig`
- Nenhum `ruff`, `black`, `flake8`, `isort`, `mypy` ou `pyright` configurado

O código atual está bem formatado (type hints, convenções), mas sem automação, a qualidade depende exclusivamente da disciplina manual.

---

## 4. Melhorias Futuras (P2)

| Prática | Descrição | Prioridade |
|---|---|---|
| **Testes de mutação** | Usar `mutmut` ou `cosmic-ray` para medir a eficácia dos testes | P2 |
| **Fuzzing** | Usar `hypothesis` para gerar payloads aleatórios e descobrir crashes | P2 |
| **Testes de contrato (Pact)** | Se houver comunicação com serviços externos, usar Pact para garantir compatibilidade | P2 |
| **BDD / testes aceitação** | Se o produto crescer, `behave` ou `pytest-bdd` para cenários legíveis por negócio | P2 |
| **Property-based testing** | Especialmente para `validar_lote` com entradas arbitrárias | P2 |

---

## 5. Riscos

### 5.1 Risco de regressão — ALTO

A cobertura estimada de **~66%** com **0% de cobertura nos cenários de borda** do validador significa que:

- Qualquer mudança no `validators/lote.py` tem ~55% de chance de quebrar sem ser detectada
- Qualquer mudança na classe `ResultadoMonitoramento` não é detectada por testes unitários

### 5.2 Falsos positivos — BAIXO

Os testes existentes são determinísticos e específicos. Não há mocks complexos que possam dar falsos positivos.

### 5.3 Testes frágeis — MÉDIO

- `BackendRouteTests` faz asserções parciais (só verifica 1 erro em vez dos 6 esperados)
- `IntegracaoExternaTests` verifica `__abstractmethods__` que é um detalhe de implementação do Python/ABC — vulnerável a mudanças de versão do CPython

### 5.4 Baixa cobertura de integração — CRÍTICO

O maior risco é a **ausência de testes de integração** para:

- Fluxo completo HTTP → validação → classificação (já coberto)
- Fluxo com dados reais de ERP
- Cenários de rede: timeout, retry, fallback
- Concorrência: duas requisições simultâneas para o mesmo lote

### 5.5 Risco de segurança — CRÍTICO

API pública sem autenticação, sem rate limiting, sem validação de payload profunda. Um payload malicioso como:

```json
{
  "codigo_produto": "PROD-001",
  "nome_produto": "A" * 100000,
  "lote": "L-01",
  "quantidade": 10,
  "data_validade": "2026-07-15",
  "local": "Deposito A"
}
```

Pode causar **OOM** (Out of Memory) no servidor, pois o validador não limita tamanho de strings.

---

## 6. Recomendações Priorizadas

### P0 — Bloqueantes (resolver antes de qualquer deploy)

| # | Ação | Justificativa |
|---|---|---|
| P0.1 | **Adicionar autenticação na API** (`TokenAuthentication` ou `SessionAuthentication`) e testes para endpoints não autenticados retornarem `401` | API pública sem auth |
| P0.2 | **Adicionar rate limiting** (`django-rest-framework` throttling) e testar que bursts de requisições são rejeitados | Proteção contra abuso |
| P0.3 | **Testar todos os cenários de borda do validador** (`payload` não-dict, `quantidade` booleano/negativo/zero, `data_validade` date object, strings gigantes) | Cobertura do validador é ~45% |
| P0.4 | **Testar que o endpoint inválido retorna TODOS os erros**, não apenas um | Falso positivo no teste atual |
| P0.5 | **Limitar tamanho de campos string no validador** (ex.: `max_length=255`) e testar rejeição | Risco de OOM |

### P1 — Pré-Go-Live (resolver antes de abrir para usuários reais)

| # | Ação | Justificativa |
|---|---|---|
| P1.1 | **Configurar GitHub Actions (ou similar)** com job de `python manage.py test tests` | Sem CI, nada bloqueia merge quebrado |
| P1.2 | **Adicionar `pytest` + `pytest-cov` + `pytest-django`** ao `requirements.txt` | Framework moderno + coverage |
| P1.3 | **Configurar meta de cobertura mínima (80%)** no `pyproject.toml` | Garantia de qualidade |
| P1.4 | **Configurar lint (`ruff`)** e rodar em CI | Padronização automática |
| P1.5 | **Criar `SettingsForTests`** que sobreponha `SECRET_KEY` e `DEBUG` | Higiene de configuração |
| P1.6 | **Criar teste de carga simples** (k6 ou locust) para `/lotes/validar` e `/health` | Baseline de performance |
| P1.7 | **Reforçar `BackendRouteTests`** para verificar todos os erros retornados | Eliminar falso positivo |

### P2 — Pós-Go-Live (melhorias contínuas)

| # | Ação | Justificativa |
|---|---|---|
| P2.1 | Adicionar testes de mutação (`mutmut`) | Medir eficácia real dos testes |
| P2.2 | Adicionar property-based tests (`hypothesis`) para `validar_lote` | Descobrir crashes não previstos |
| P2.3 | Adicionar `pre-commit` hooks com ruff e mypy | Qualidade no commit |
| P2.4 | Criar testes de integração para adaptadores ERP concretos (quando existirem) | Rede de proteção para IO |
| P2.5 | Adicionar testes de concorrência (duas requisições simultâneas) | Garantir ausência de race conditions |
| P2.6 | Configurar `tox` para testar em Python 3.11, 3.12, 3.13 | Compatibilidade entre versões |

---

## Anexo A — Comandos atuais do projeto

```bash
# Rodar testes
python manage.py test tests

# Rodar servidor de desenvolvimento
python manage.py runserver
```

## Anexo B — Referência de arquivos analisados

| Arquivo | Linhas | Papel |
|---|---|---|
| `tests/test_backend.py` | 205 | Único arquivo de testes (6 classes) |
| `tests/__init__.py` | 1 | Apenas marca pacote |
| `src/validators/lote.py` | 66 | Validador de payload (gap de cobertura) |
| `src/services/vencimento.py` | 32 | Cálculo de dias e classificação (100% coberto) |
| `src/services/monitoramento.py` | 51 | Orquestração validação + risco (100% coberto) |
| `src/routes/views.py` | 24 | Endpoints HTTP (coberto) |
| `src/integrations/base.py` | 25 | Porta abstrata de integração |
| `src/integrations/erp.py` | 21 | Porta específica ERP |
| `src/integrations/mapeamento.py` | 11 | Mapeador abstrato de campos |
| `src/models/lote.py` | 13 | Dataclass Lote (sem ORM) |
| `config/settings.py` | 47 | Config Django (sem auth) |
| `requirements.txt` | 2 | Apenas Django + DRF |
