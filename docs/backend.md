# Backend inicial

## Arquitetura

O backend usa Django e Django REST Framework, com separacao entre:

1. rotas HTTP;
2. validacao e normalizacao;
3. regras de negocio;
4. entidades de dominio;
5. futuras integracoes.

SQLite e usado apenas no desenvolvimento inicial. A arquitetura de referencia
preve PostgreSQL para memoria operacional, sem replicar o estoque completo do
ERP.

## Contrato inicial

Campos obrigatorios:

- `codigo_produto`;
- `nome_produto`;
- `lote`;
- `quantidade`, maior que zero;
- `data_validade`, no formato `YYYY-MM-DD`;
- `local`.

## Classificacao

| Condicao | Classificacao |
|---|---|
| Menos de 0 dias | `VENCIDO` |
| De 0 a 7 dias | `CRITICO` |
| De 8 a 30 dias | `ATENCAO` |
| Acima de 30 dias | `NORMAL` |

## PDCA 001 - Backend inicial

### Plan

Criar a base Django/DRF, validar o contrato de lote, calcular dias restantes,
classificar risco e expor as rotas `/health` e `/lotes/validar`.

### Do

Foram separados modulos de modelos, validadores, servicos e rotas. Nenhuma
integracao externa, frontend ou autenticacao avancada foi adicionada.

### Check

Testes de mesa definidos:

| Entrada relativa a hoje | Resultado esperado |
|---|---|
| Ontem | `VENCIDO` |
| Daqui a 5 dias | `CRITICO` |
| Daqui a 20 dias | `ATENCAO` |
| Daqui a 60 dias | `NORMAL` |

Os testes automatizados tambem cobrem os limites 0, 7, 8, 30 e 31 dias, dados
invalidos e as duas rotas HTTP.

### Act

O ciclo foi validado com:

- `python manage.py check`: nenhuma falha identificada;
- `python manage.py test -v 2`: 7 testes executados com sucesso;
- compilacao dos modulos Python: concluida sem erros.

Nenhuma correcao adicional foi necessaria. A separacao entre rota, validacao,
entidade e regra de negocio passa a ser a base para as proximas iteracoes.
