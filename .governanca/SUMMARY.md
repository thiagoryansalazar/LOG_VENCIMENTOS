# Indice de Governanca

## Arquivos

- `README.md`: visao geral do sistema de governanca.
- `AGENTS.md`: regras operacionais para agentes de IA.
- `AGENTES/`: identificadores formais de agentes, auxiliares e regras de
  identificacao.
- `AGENTES/SUBAGENTES.md`: objetivos, escopo e responsabilidades dos subagentes
  do Codex.
- `DECISOES.md`: registro de decisoes arquiteturais.
- `PROCEDIMENTOS.md`: procedimentos operacionais padrao.
- `LOG.md`: log de atividades do Codex.
- `SUMMARY.md`: indice desta estrutura.

## Fluxo recomendado

```text
Ler governanca
  -> identificar agente
  -> executar acao
  -> validar
  -> registrar no LOG.md
  -> commitar
```

## Lembrete

Esta estrutura governa o desenvolvimento.

Ela nao substitui:

- README do produto;
- documentacao da API;
- documentacao DRF/OpenAPI;
- relatorios de entrega;
- backlog e cronograma.
