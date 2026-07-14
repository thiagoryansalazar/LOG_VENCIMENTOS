# Atlas como hub de inteligência de estoque

## Contexto

Esta nota registra uma visão futura do LOG_VENCIMENTOS/Atlas: o sistema não deve
ser entendido apenas como um monitor de validade, mas como um hub de inteligência
de estoque.

O ponto central é que o Atlas consome dados de estoque de uma fonte autorizada,
processa esses dados, classifica riscos, enriquece a informação e expõe essa
inteligência por API para outros sistemas.

## Arquitetura de dois mundos

O Atlas opera conceitualmente em dois fluxos.

### 1. Fluxo interno de entrada

O Atlas consome dados do ERP de estoque ou de outra fonte autorizada.

Essa fonte continua sendo a origem primária dos dados de produtos, lotes,
quantidades, validade e localização.

```text
ERP de estoque
  -> Atlas
  -> valida, normaliza, classifica e enriquece
```

### 2. Fluxo externo de saída

Depois de processar os dados, o Atlas expõe a inteligência gerada por meio de
API para outros sistemas.

```text
ERP de estoque
  -> Atlas
  -> API pública/versionada
  -> ERP de preços
  -> CRM
  -> BI
  -> agentes de IA
```

## Decisão conceitual

A API não deve ser tratada apenas como um entrypoint para o frontend.

A API é parte do produto.

Ela deve permitir que outros sistemas consumam a inteligência do Atlas sem
precisar conhecer os detalhes internos de cálculo de risco.

Exemplo de consumo esperado:

```json
{
  "classificacao": "CRITICO",
  "dias_restantes": 3
}
```

O sistema consumidor não precisa saber como o risco foi calculado. Ele precisa
apenas receber uma resposta estável, documentada e confiável.

## Por que isso é relevante

### Desacoplamento

Outros sistemas não precisam copiar a regra de risco do Atlas.

O ERP de preços, por exemplo, pode apenas consultar a API e decidir uma política
de desconto com base na classificação retornada.

### Reuso da inteligência

A mesma classificação que gera alerta para o gestor pode ser usada por:

- ERP de preços;
- CRM;
- BI;
- agentes de IA;
- dashboards;
- automações operacionais.

### Preparação para agentes

No futuro, um agente de IA pode consumir a API do Atlas por meio de uma camada
MCP ou outra integração.

Exemplo de regra futura:

```text
Se classificacao = CRITICO
e estoque > 100
entao sugerir desconto de 20%
```

Essa regra não precisa estar no MVP, mas a API deve ser desenhada para permitir
esse tipo de uso no futuro.

## Dados enriquecidos

A API futura não deve retornar apenas a classificação.

Ela deve retornar contexto suficiente para que outro sistema possa agir.

Campos relevantes:

- `dias_restantes`;
- `data_validade`;
- `classificacao`;
- `produto`;
- `codigo_produto`;
- `lote`;
- `quantidade`;
- `local`;
- `motivo`, quando existir;
- `recomendacao`, quando existir.

Exemplo de resposta enriquecida:

```json
{
  "lote": "L2026-01",
  "produto": {
    "codigo": "PROD-001",
    "nome": "Leite integral"
  },
  "validade": "2026-07-15",
  "dias_restantes": 3,
  "classificacao": "CRITICO",
  "recomendacao": "Vender com urgência. Desconto sugerido: 15%"
}
```

## Endpoints futuros possíveis

O MVP atual não precisa implementar todos os endpoints. Ainda assim, a arquitetura
deve manter espaço para evolução.

Exemplos de endpoints futuros:

```text
GET /api/v1/lotes?status=CRITICO
GET /api/v1/produtos/{codigo}/risco
POST /api/v1/alertas/configurar
POST /api/v1/decisoes/sugerir
```

Esses endpoints representam a API como produto e não apenas como apoio ao
frontend.

## Implicações para o MVP

O MVP não deve implementar ERP de preços, CRM, BI, MCP, Redis ou Celery apenas
por causa dessa visão.

O MVP deve apenas deixar a porta aberta.

Diretrizes para o MVP:

- manter a API versionada, preferencialmente sob `/api/v1/`;
- documentar o contrato com OpenAPI;
- retornar dados enriquecidos quando isso não aumentar complexidade
  desnecessária;
- manter o core de classificação puro e reutilizável;
- não acoplar regra de negócio ao transporte HTTP;
- tratar erros de forma consistente;
- planejar autenticação desde o início.

## Core puro e reutilizável

A lógica de classificação não deve depender de Django, de models ou de request
HTTP.

Ela deve ser chamável por:

- endpoint HTTP;
- script interno;
- job assíncrono futuro;
- integração;
- teste automatizado.

O serviço `src/services/monitoramento.py` já segue essa direção por isolar o
monitoramento da camada HTTP.

## Autenticação para sistemas externos

Para o MVP, a recomendação é começar com API Key.

```text
Sistema consumidor -> envia API Key -> Atlas valida -> retorna dados
```

Vantagens:

- implementação mais simples;
- adequada para o MVP;
- suficiente para validar consumo por sistemas externos.

Limitações:

- menor granularidade de permissões;
- revogação e escopo exigem cuidado;
- menos robusta que OAuth2/JWT.

Para uma versão futura, a arquitetura deve permitir migração para JWT/OAuth2 com
escopos.

```text
Versão 1: API Key
Versão 2: JWT/OAuth2 com escopos
```

## Escalabilidade futura

Se outros sistemas consultarem o Atlas em alto volume, a API precisará responder
rápido e com previsibilidade.

Recursos futuros possíveis:

- cache com Redis;
- processamento assíncrono com Celery;
- fila para tarefas pesadas;
- métricas de latência e erro;
- rate limit;
- observabilidade.

Esses itens não fazem parte do MVP por padrão. Eles entram quando houver volume,
integração real ou necessidade operacional validada.

## Limite importante

Essa visão não autoriza transformar o LOG_VENCIMENTOS em ERP.

O Atlas continua sendo uma camada de inteligência sobre dados de estoque. Ele
consome dados da fonte autorizada, gera inteligência e expõe essa inteligência.

Ele não deve se tornar o dono principal do cadastro de produtos, lotes e estoque.

