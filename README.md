# LOG_VENCIMENTOS

Backend para consultar e validar dados de lotes, calcular dias restantes para o
vencimento e classificar riscos operacionais.

O sistema funciona como uma camada preventiva sobre dados de estoque existentes.
Ele nao substitui o ERP nem se torna a fonte principal de produtos e lotes.

## Visao geral

Nesta primeira iteracao, a API recebe um lote em JSON, valida seu contrato
minimo e devolve a quantidade de dias para o vencimento e a classificacao de
risco.

Stack inicial:

- Python 3.11 ou superior;
- Django;
- Django REST Framework;
- SQLite somente para desenvolvimento local.

## Modulos

- `src/integrations`: futuros conectores de fontes externas.
- `src/validators`: validacao e normalizacao de dados de entrada.
- `src/services`: regras de negocio e classificacao de risco.
- `src/models`: entidades do dominio.
- `src/routes`: endpoints HTTP da API.
- `src/utils`: funcoes auxiliares compartilhadas.

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
