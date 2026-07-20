# Relatorio do entregavel - 17/07/2026

## Projeto

ATLAS Vencimentos.

## Objetivo do dia

Implementar o fluxo inicial de ingestao CSV para validar que uma fonte externa
simples consegue alimentar o core de monitoramento do ATLAS Vencimentos.

O objetivo nao foi persistir dados no banco, criar endpoints ou integrar ERP
real. O foco foi leitura, mapeamento e classificacao pelo core existente.

## Contexto

O arquivo `data/lotes_mockados.csv` ja havia sido criado com dados ficticios de
lotes alimenticios. O proximo passo era permitir que o sistema lesse esse CSV,
convertesse os campos para o contrato interno e executasse `monitorar_lote`.

## Arquivos criados

### `src/integrations/adaptador_csv.py`

Criado `AdaptadorCSV`, implementando `AdaptadorFonteExterna`.

Responsabilidades:

- ler arquivos CSV em UTF-8;
- aceitar caminho absoluto;
- aceitar caminho relativo ao projeto;
- aceitar apenas o nome do arquivo e buscar em `data/`;
- retornar registros como dicionarios.

### `src/integrations/mapeador_csv.py`

Criado `MapeadorCSV`, implementando `MapeadorCampos`.

Responsabilidades:

- validar campos obrigatorios;
- converter `quantidade` para `int` ou `float`;
- converter `data_validade` para `date`;
- devolver payload compativel com o core.

Campos obrigatorios:

```text
codigo_produto
nome_produto
lote
quantidade
data_validade
local
```

### `scripts/importar_csv.py`

Criado script operacional para executar o fluxo completo:

```text
CSV
  -> AdaptadorCSV
  -> MapeadorCSV
  -> monitorar_lote
  -> resumo no terminal
```

O script aceita caminho opcional do CSV. Quando nenhum caminho e informado, usa
`data/lotes_mockados.csv`.

## Arquivos alterados

- `src/integrations/__init__.py`: exporta `AdaptadorCSV` e `MapeadorCSV`.
- `tests/test_backend.py`: adiciona testes para adaptador, mapeador e fluxo CSV.
- `.governanca/LOG.md`: registra a acao do Codex.

## Validacao executada

Comando:

```bash
python scripts/importar_csv.py
```

Resultado:

```text
Linha 1: PROD-001 / L2026-001 -> VENCIDO (-7 dias)
Linha 2: PROD-002 / IG2026-014 -> VENCIDO (0 dias)
Linha 3: PROD-003 / QM2026-022 -> CRITICO (5 dias)
Linha 4: PROD-004 / SL2026-031 -> CRITICO (7 dias)
Linha 5: PROD-005 / PI2026-018 -> ATENCAO (24 dias)
Linha 6: PROD-006 / AB2026-045 -> NORMAL (39 dias)
Total de lotes processados: 6
Classificacoes encontradas:
- ATENCAO: 1
- CRITICO: 2
- NORMAL: 1
- VENCIDO: 2
```

## Testes automatizados

Comando:

```bash
python manage.py test -v 2
```

Resultado:

```text
18 tests passed
```

Cobertura adicionada:

- leitura do CSV mockado;
- conversao de campos pelo mapeador CSV;
- fluxo CSV passando pelo core de monitoramento;
- classificacoes esperadas para a data de referencia `17/07/2026`.

## Check Django

Comando:

```bash
python manage.py check
```

Resultado:

```text
System check identified no issues
```

## Observacoes tecnicas

Como a data de referencia do ambiente e `17/07/2026`, o lote com
`data_validade = 2026-07-17` foi classificado como `VENCIDO`.

Isso esta correto e respeita a regra de negocio definida no projeto:

```text
0 dias ou menos -> VENCIDO
```

## Status final

Concluido.

O ATLAS Vencimentos agora possui um fluxo funcional para:

- ler CSV mockado;
- mapear dados externos para o contrato interno;
- executar o core de monitoramento;
- exibir classificacoes no terminal;
- validar o comportamento por testes automatizados.

## Proximos passos

- Persistir as analises geradas em `AnaliseLote`.
- Evoluir o script para comando Django `executar_monitoramento`.
- Integrar a geracao de alertas em etapa posterior.
- Manter ERP real fora do escopo ate a base CSV estar validada.

