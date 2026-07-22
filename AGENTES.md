# Instrucoes para Agentes

Este e o ponto de entrada rapido para qualquer agente que acessar o projeto
ATLAS Vencimentos.

As regras formais ficam em `.governanca/`.

## Entrada obrigatoria

Antes de alterar qualquer arquivo:

1. leia `.governanca/README.md`;
2. leia `.governanca/AGENTS.md`;
3. confirme sua etiqueta YAML em `.governanca/AGENTES/id_agentes.yaml`;
4. leia `.governanca/AGENTES/regras_de_identificacao.md`;
5. leia `.governanca/DECISOES.md`;
6. leia `.governanca/PROCEDIMENTOS.md`;
7. execute `git status --short --branch`.

## Identificacao

Todo agente que modificar o projeto precisa ter uma etiqueta YAML cadastrada.

Exemplo:

```yaml
id: codex
```

Todo registro no LOG deve usar:

```text
agent_id=codex
```

Agente sem etiqueta YAML cadastrada nao pode alterar codigo, documentacao,
configuracao, scripts, migracoes, relatorios ou governanca.

## Fonte de verdade

- A Wiki `CEREBRO_ENGINEER_WIKI` pode ser consultada como fonte conceitual.
- A Wiki nao deve ser alterada sem autorizacao explicita.
- Mudancas executaveis devem acontecer neste repositorio.

## Comportamento esperado

- Respeite o escopo solicitado.
- Leia o codigo antes de editar.
- Preserve mudancas que voce nao fez.
- Nao invente validacoes.
- Registre bloqueios de forma objetiva.
- Execute testes compativeis com a mudanca.
- Registre a acao em `.governanca/LOG.md`.

## Agentes e auxiliares

Agentes executam e registram.

Auxiliares ajudam a pensar, revisar e sintetizar, mas nao viram decisao
automaticamente.

Use:

- `.governanca/AGENTES/id_agentes.yaml` para agentes;
- `.governanca/AGENTES/id_auxiliares.yaml` para auxiliares.

## Subagentes

Subagentes do Codex tambem usam etiqueta YAML propria.

Quando um subagente modificar algo, ele deve registrar o LOG com o proprio ID:

- `agent_id=codex_backend`
- `agent_id=codex_qa`
- `agent_id=codex_docs`
- `agent_id=codex_governanca`
- `agent_id=codex_devops`

Nao use `agent_id=codex` para esconder qual subagente executou a acao.

## Padrao de codigo

- Use Python com tipagem, nomes claros e funcoes pequenas.
- Separe transporte HTTP, validacao, dominio e integracoes.
- Nao coloque regra de negocio em views.
- Preserve o contrato canonico de lotes.
- Nunca inclua segredos em arquivos versionados.

## PDCA obrigatorio

Em cada iteracao:

1. Plan: declare objetivo, arquivos afetados e resultado esperado.
2. Do: implemente a menor mudanca coerente.
3. Check: execute validacoes automatizadas e testes de mesa quando aplicavel.
4. Act: corrija falhas e documente a decisao validada.
