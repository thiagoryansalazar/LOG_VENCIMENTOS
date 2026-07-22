# Governanca do Desenvolvimento - ATLAS Vencimentos

## Objetivo

Esta pasta define a governanca do desenvolvimento do ATLAS Vencimentos.

Ela aplica os principios de rastreabilidade, auditoria e controle inspirados na
filosofia do CEREBRO_ENGINEER_WIKI, mas adaptados para desenvolvimento de
software.

## Escopo

Esta estrutura controla como o projeto evolui.

Ela cobre:

- regras de operacao para agentes de IA;
- identificacao formal de agentes e auxiliares;
- decisoes arquiteturais;
- procedimentos operacionais;
- log de atividades;
- indice de navegacao.

Ela nao e uma wiki de produto.

Documentacao de produto, API e uso do sistema continuam no `README.md`, nos
relatorios de entrega e na documentacao tecnica propria.

## Principios

- Rastreabilidade: toda acao relevante deve deixar registro.
- Auditoria: mudancas devem informar contexto, arquivos alterados e resultado.
- Controle: decisoes arquiteturais devem ser registradas com consequencias.
- Identificacao: todo agente modificador deve ter etiqueta YAML cadastrada e
  informar `agent_id` no LOG.
- Simplicidade: a governanca deve ajudar o MVP, nao criar burocracia inutil.

## Ordem de leitura obrigatoria

Antes de qualquer acao relevante no projeto, o Codex deve consultar:

1. `.governanca/README.md`
2. `.governanca/AGENTS.md`
3. `.governanca/AGENTES/regras_de_identificacao.md`
4. `.governanca/AGENTES/id_agentes.yaml`
5. `.governanca/DECISOES.md`
6. `.governanca/PROCEDIMENTOS.md`

Depois da acao, o Codex deve registrar a atividade em `.governanca/LOG.md`.
