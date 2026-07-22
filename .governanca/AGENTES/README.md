# Agentes do Projeto

Esta pasta registra os identificadores formais de agentes e auxiliares usados
no desenvolvimento do ATLAS Vencimentos.

Ela adapta a ideia da pasta `05_AGENTES` da CEREBRO_ENGINEER_WIKI para o
contexto deste repositorio de software.

## Arquivos

- `id_agentes.yaml`: etiquetas YAML oficiais dos agentes autorizados a atuar no
  projeto.
- `id_auxiliares.yaml`: etiquetas YAML de fontes auxiliares de construcao
  teorica ou apoio.
- `regras_de_identificacao.md`: regras de uso dos IDs, origem e status.

## Principio

Nem todo conteudo gerado por IA vira decisao automaticamente.

Agentes executam, registram e auditam. Auxiliares ajudam a construir contexto,
mas suas sugestoes precisam ser validadas antes de virar arquitetura, codigo ou
decisao de produto.

## Etiqueta YAML

A etiqueta oficial de identificacao e o campo `id` cadastrado nos arquivos
YAML.

Exemplo:

```yaml
id: codex
```

No LOG, essa etiqueta deve aparecer como:

```text
agent_id=codex
```
