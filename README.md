# LOG_VENCIMENTOS

Backend para consultar e validar dados de lotes, calcular dias restantes para o
vencimento e classificar riscos operacionais.

O sistema funciona como uma camada preventiva sobre dados operacionais mantidos
por sistemas externos. Ele nao substitui ERP, WMS ou outra fonte oficial e nao
se torna o proprietario principal dos dados monitorados.

## Visao geral

Nesta primeira iteracao, a API recebe um lote em JSON, valida seu contrato
minimo e devolve a quantidade de dias para o vencimento e a classificacao de
risco.

O sistema de origem permanece como fonte de verdade. Na arquitetura-alvo, o
LOG_VENCIMENTOS sera acionado por evento ou por uma alternativa configurada,
consultara os dados necessarios, normalizara, monitorara e alertara. Ele nao
gravara correcoes diretamente na fonte. A conferencia fisica cabe a operacao e
a decisao cabe ao gestor, que atualiza o sistema oficial quando necessario.

Stack inicial:

- Python 3.11 ou superior;
- Django;
- Django REST Framework;
- SQLite somente para desenvolvimento local.

## Modulos

- `src/integrations`: contratos da Camada de Integracao Externa, modos de
  acionamento, mapeamento e adaptadores por fonte.
- `src/validators`: validacao e normalizacao de dados de entrada.
- `src/services`: monitoramento, calculo de vencimento e classificacao de risco.
- `src/models`: entidades do dominio.
- `src/routes`: endpoints HTTP da API.
- `src/utils`: funcoes auxiliares compartilhadas.

## Fluxo arquitetural

```text
Sistema de origem
  -> evento ou webhook, preferencialmente
  -> consulta agendada, quando nao ha evento
  -> importacao de arquivo, como alternativa
  -> Camada de Integracao Externa
  -> adaptador da fonte
  -> mapeador de campos
  -> valida e normaliza
  -> Monitoramento de Vencimentos
  -> futura Central de Alertas
  -> Gestor e operacao fisica
```

Os tres modos convergem para o mesmo contrato interno:

```text
EVENTO
CONSULTA_AGENDADA
ARQUIVO
```

Quando um evento carregar apenas identificador e dados minimos, o adaptador sera
o elemento ativo que consulta o registro completo na fonte autorizada. O
contrato definitivo do evento, autenticacao, idempotencia, replay e tratamento
de ordem ainda precisam ser definidos antes de criar um receptor HTTP.

A capacidade de integracao depende da porta oferecida pela fonte - webhook,
API, banco somente leitura, arquivo ou fila - e nao da linguagem usada pelo
sistema externo.

O contrato canonico planejado contem `codigo_produto`, `nome_produto`, `lote`,
`quantidade`, `data_validade`, `local` e `status`. O endpoint atual ainda nao
recebe `status`, pois sua origem, semantica e obrigatoriedade precisam ser
validadas antes da implementacao.

O setor alimenticio permanece como MVP. A futura generalizacao para outros
tipos de prazo, conformidade e risco nao altera automaticamente o modelo
executavel de `Lote`.

## Estado atual

Implementado:

- API Django/DRF;
- validacao e normalizacao do lote;
- servico inicial de Monitoramento de Vencimentos por lote;
- calculo de dias restantes e classificacao de risco;
- contrato abstrato e somente leitura para fontes externas;
- especializacao do adaptador para consulta ao ERP;
- modos de integracao por evento, consulta agendada ou arquivo;
- contrato de mapeamento entre registro externo e payload canonico.

Ainda nao implementado:

- conector real com ERP;
- receptor de webhook e contrato canonico do evento;
- autenticacao, idempotencia, repeticao, replay e ordenacao de eventos;
- memoria operacional em PostgreSQL;
- monitoramento continuo e persistente;
- RabbitMQ, Celery Worker e Celery Beat;
- Central de Alertas;
- frontend, autenticacao e isolamento por empresa.

SQLite e usado somente no desenvolvimento inicial. Ele nao representa o
repositorio principal dos lotes.

Classificacao atual:

- `VENCIDO`: 0 dias ou menos;
- `CRITICO`: entre 1 e 7 dias;
- `ATENCAO`: entre 8 e 30 dias;
- `NORMAL`: acima de 30 dias.

## Execucao local

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Endpoints

- `GET /health`
- `POST /lotes/validar`

Exemplo:

```json
{
  "codigo_produto": "PROD-001",
  "nome_produto": "Leite integral",
  "lote": "L2026-01",
  "quantidade": 12,
  "data_validade": "2026-07-15",
  "local": "Deposito A"
}
```

## Testes

```bash
python manage.py test
```

As decisoes e o primeiro ciclo PDCA estao documentados em
`docs/backend.md`.
