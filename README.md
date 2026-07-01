# LOG_VENCIMENTOS

Backend para consultar e validar dados de lotes, calcular dias restantes para o
vencimento e classificar riscos operacionais.

O sistema funciona como uma camada preventiva sobre dados de estoque existentes.
Ele nao substitui o ERP nem se torna a fonte principal de produtos e lotes.

## Visao geral

Nesta primeira iteracao, a API recebe um lote em JSON, valida seu contrato
minimo e devolve a quantidade de dias para o vencimento e a classificacao de
risco.

O ERP da empresa permanece como fonte de verdade. O LOG_VENCIMENTOS consulta,
normaliza, monitora e alerta; ele nao grava correcoes diretamente no ERP. A
conferencia fisica cabe ao repositor e a decisao operacional cabe ao gestor,
que atualiza o ERP quando necessario.

Stack inicial:

- Python 3.11 ou superior;
- Django;
- Django REST Framework;
- SQLite somente para desenvolvimento local.

## Modulos

- `src/integrations`: contrato do Adaptador de Consulta ERP e futuros
  conectores.
- `src/validators`: validacao e normalizacao de dados de entrada.
- `src/services`: monitoramento, calculo de vencimento e classificacao de risco.
- `src/models`: entidades do dominio.
- `src/routes`: endpoints HTTP da API.
- `src/utils`: funcoes auxiliares compartilhadas.

## Fluxo arquitetural

```text
Adaptador de Consulta ERP
  -> consulta a fonte autorizada
  -> mapeia os dados externos
  -> valida e normaliza
  -> Monitoramento de Vencimentos
  -> futura Central de Alertas
  -> Gestor e operacao fisica
```

O adaptador e o elemento ativo da consulta:

```text
Adaptador de Consulta ERP -> Repositorio de Lotes do ERP
```

Sua interface inicial oferece apenas leitura. A forma concreta de acesso ainda
sera definida entre API, banco somente leitura ou arquivo CSV/XLSX exportado.

O contrato canonico planejado contem `codigo_produto`, `nome_produto`, `lote`,
`quantidade`, `data_validade`, `local` e `status`. O endpoint atual ainda nao
recebe `status`, pois sua origem, semantica e obrigatoriedade precisam ser
validadas antes da implementacao.

## Estado atual

Implementado:

- API Django/DRF;
- validacao e normalizacao do lote;
- servico inicial de Monitoramento de Vencimentos por lote;
- calculo de dias restantes e classificacao de risco;
- contrato abstrato e somente leitura para consulta ao ERP.

Ainda nao implementado:

- conector real com ERP;
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
