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
| 0 dias ou menos | `VENCIDO` |
| De 1 a 7 dias | `CRITICO` |
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

## PDCA 002 - Alinhamento com a Arquitetura Geral

### Plan

Ler a Wiki sem altera-la e refletir no backend a direcao de consulta ao ERP e a
separacao entre transporte HTTP, monitoramento e integracao.

### Do

- criado o contrato abstrato `AdaptadorConsultaERP`, exclusivamente de leitura;
- criado o servico inicial `monitorar_lote`;
- removida da view a orquestracao direta de validacao e classificacao;
- atualizado o `README.md` com responsabilidades, limites e estado atual.

### Check

- `python manage.py check`: nenhuma falha;
- `python manage.py test -v 2`: 10 testes aprovados;
- compilacao dos modulos Python: concluida sem erros.

### Act

O backend agora representa explicitamente que o adaptador consulta o ERP e que
o monitoramento calcula risco. Nenhum conector real, escrita no ERP, alerta,
PostgreSQL ou processamento assincrono foi introduzido prematuramente.

## PDCA 003 - Vencimento no dia da validade

### Plan

Alterar o limite para considerar vencido o lote cuja data de validade seja
igual a data atual.

### Do

A classificacao `VENCIDO` passou a aceitar zero ou menos dias restantes.
`CRITICO` passou a representar o intervalo de 1 a 7 dias.

### Check

Teste de mesa:

```text
hoje = 01/07/2026
data_validade = 01/07/2026
dias_restantes = 0
classificacao = VENCIDO
```

Os testes automatizados cobrem tambem a transicao de 0 para 1 dia.

### Act

A regra foi alinhada ao criterio operacional definido pelo responsavel do
produto.

## PDCA 004 - Camada de Integracao Externa

### Plan

Aplicar a arquitetura orientada a eventos sem antecipar o contrato do evento,
autenticacao, fila ou conectores reais ainda nao definidos.

### Do

- criado o contrato generico `AdaptadorFonteExterna`;
- preservado `AdaptadorConsultaERP` como especializacao de leitura;
- registrados os modos `EVENTO`, `CONSULTA_AGENDADA` e `ARQUIVO`;
- criado o contrato `MapeadorCampos`;
- atualizado o `README.md` com escopo atual, visao futura e pendencias.

### Check

- `python manage.py test -v 2`: 14 testes aprovados;
- adaptador ERP delega para a porta generica;
- nenhum metodo de escrita foi introduzido;
- os tres modos de integracao e o mapeador possuem testes de contrato.

### Act

O backend agora admite diferentes sistemas e formas de acionamento sem depender
da linguagem da fonte. Receptor de webhook, contrato de evento, idempotencia,
replay, PostgreSQL e fila permanecem bloqueados ate definicao especifica.

## PDCA 005 - API como produto e hub de inteligencia

### Plan

Registrar a visao futura do Atlas como hub de inteligencia de estoque, sem
alterar prematuramente o escopo executavel do MVP.

A decisao de arquitetura e tratar a API como produto. Ela nao deve servir apenas
ao frontend; deve permitir que outros sistemas consumam a inteligencia gerada
pelo monitoramento.

### Do

Foi documentada a arquitetura de dois fluxos:

```text
Fluxo interno:
ERP de estoque -> Atlas -> valida, classifica e enriquece

Fluxo externo:
Atlas -> API versionada -> ERP de precos, CRM, BI e agentes de IA
```

Tambem foi registrada a expectativa de respostas enriquecidas, contendo lote,
produto, validade, dias restantes, classificacao e recomendacao quando aplicavel.

### Check

A visao preserva as decisoes anteriores:

- o ERP continua sendo fonte de verdade dos dados de estoque;
- o LOG_VENCIMENTOS/Atlas nao vira ERP;
- o core de classificacao deve continuar puro e reutilizavel;
- integracoes avancadas permanecem fora do MVP ate validacao real.

### Act

Para as proximas iteracoes, avaliar:

- versionamento da API em `/api/v1/`;
- documentacao OpenAPI;
- autenticacao por API Key no MVP;
- desenho preparado para migracao futura para JWT/OAuth2;
- endpoints futuros como listagem de lotes criticos, risco por produto,
  configuracao de alertas e sugestao de decisoes;
- cache, Celery e MCP somente quando houver necessidade validada.
