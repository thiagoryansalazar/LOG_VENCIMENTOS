# Regras de Identificacao

## Regras gerais

1. Todo agente que modificar qualquer arquivo do projeto deve ter uma etiqueta
   YAML cadastrada em `id_agentes.yaml` antes da alteracao.
2. Nenhum agente sem cadastro pode alterar codigo, documentacao, configuracao,
   migracoes, scripts ou arquivos de governanca.
3. Toda acao relevante deve informar data, `agent_id`, acao, arquivos e
   resultado.
4. Use exclusivamente a etiqueta YAML definida no campo `id` em
   `id_agentes.yaml`.
5. Sugestoes vindas de auxiliares devem preservar origem e status.
6. Conteudo gerado por agente ou auxiliar nao vira decisao automaticamente.
7. Decisoes exigem contexto, justificativa, consequencias e status em
   `.governanca/DECISOES.md`.
8. A Wiki pode ser fonte de verdade conceitual, mas alteracoes executaveis
   devem ser feitas neste repositorio.

## Regra de bloqueio

Se um agente precisar modificar o projeto e sua etiqueta YAML nao existir em
`id_agentes.yaml`, ele deve parar e solicitar cadastro antes de agir.

O cadastro minimo exige:

- `id` como etiqueta YAML oficial;
- `nome`;
- `papel`;
- `status`;
- `responsabilidades`.

## Agente versus auxiliar

Agente:

- executa alteracoes no repositorio;
- registra logs;
- valida resultado;
- responde por rastreabilidade tecnica.

Auxiliar:

- apoia construcao teorica;
- gera ideias, contexto ou analises;
- nao altera o projeto diretamente;
- precisa de validacao antes de virar decisao.

## Subagentes

Subagentes do Codex tambem sao agentes para fins de auditoria.

Cada subagente deve:

- estar cadastrado em `id_agentes.yaml`;
- possuir `id` proprio;
- informar seu proprio `agent_id` no LOG quando modificar arquivos;
- informar `agente_pai: codex` no cadastro YAML;
- respeitar as mesmas regras de bloqueio de agentes formais.

Quando uma acao for feita por um subagente, o LOG nao deve usar apenas
`agent_id=codex`. Deve usar a etiqueta especifica, por exemplo:

```text
agent_id=codex_backend
agent_id=codex_qa
agent_id=codex_docs
agent_id=codex_governanca
agent_id=codex_devops
```

## Formato compacto recomendado para LOG

```text
[AAAA-MM-DD] tipo | arquivo/area | descricao | agent_id=<id_cadastrado>
```

Exemplo:

```text
[2026-07-21] governanca | .governanca/AGENTES | criada estrutura de IDs de agentes e auxiliares | agent_id=codex
```
