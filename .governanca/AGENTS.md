# Instrucoes para Agentes de IA

## Identificacao

Todo registro feito por agente deve identificar o agente como `Codex`.

## Ordem obrigatoria de consulta

Antes de qualquer implementacao, correcao, refatoracao, alteracao documental ou
execucao operacional relevante, o Codex deve ler:

1. `.governanca/README.md`
2. `.governanca/AGENTS.md`
3. `.governanca/DECISOES.md`
4. `.governanca/PROCEDIMENTOS.md`

## Registro obrigatorio

Toda acao relevante deve ser registrada em `.governanca/LOG.md`.

Cada registro deve conter:

- data;
- agente;
- acao;
- contexto;
- arquivos alterados;
- validacoes executadas;
- resultado;
- proximos passos.

## Decisoes arquiteturais

Quando uma nova decisao arquitetural for tomada, o Codex deve criar uma entrada
em `.governanca/DECISOES.md`.

Cada decisao deve conter:

- titulo;
- data;
- contexto;
- decisao;
- consequencias;
- status.

Status permitidos:

- Proposta;
- Aceita;
- Implementada;
- Obsoleta.

## Limites

O Codex nao deve transformar esta estrutura em wiki de produto.

Documentacao de produto, API e uso do sistema deve continuar nos arquivos
apropriados do projeto, como `README.md`, documentacao DRF/OpenAPI e relatorios
de entrega.

## Git

Antes de commitar:

- verificar `git status`;
- revisar arquivos alterados;
- executar validacoes cabiveis;
- registrar a acao no `LOG.md`.

