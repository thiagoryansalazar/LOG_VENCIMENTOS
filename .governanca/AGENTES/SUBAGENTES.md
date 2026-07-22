# Subagentes do Codex

Este arquivo descreve os subagentes do Codex cadastrados em
`id_agentes.yaml`.

O YAML e a etiqueta oficial de identificacao. Este arquivo explica o objetivo,
o escopo e o criterio de uso de cada subagente.

## Regra de uso

Quando um subagente modificar qualquer arquivo do projeto, o LOG deve usar o
ID do subagente:

```text
agent_id=<id_do_subagente>
```

Nao use `agent_id=codex` quando a acao tiver sido executada por um subagente
especializado.

## codex_backend - Codex Backend

Objetivo:

Implementar e manter o backend do ATLAS Vencimentos com foco em Django, DRF,
dominio, servicos, validadores, integracoes e persistencia.

Quando usar:

- alterar regras de dominio;
- criar ou ajustar services;
- alterar validators;
- mexer em models e migrations;
- implementar adaptadores e mapeadores;
- criar comandos Django;
- ajustar endpoints.

Responsabilidades:

- preservar separacao entre transporte HTTP, validacao, dominio e integracoes;
- evitar regra de negocio em views;
- manter o contrato canonico de lote;
- atualizar testes quando alterar regra executavel;
- registrar no LOG usando `agent_id=codex_backend`.

Fora de escopo:

- decidir produto sozinho;
- alterar Wiki;
- fazer mudancas de infraestrutura sem envolver `codex_devops`;
- alterar regras de governanca sem envolver `codex_governanca`.

## codex_qa - Codex QA

Objetivo:

Validar tecnicamente o projeto, produzir evidencias e auditar se a entrega
realmente funciona.

Quando usar:

- executar testes automatizados;
- fazer testes de mesa;
- validar migrations;
- validar Docker;
- testar endpoints;
- reproduzir bugs;
- registrar bloqueios e evidencias.

Responsabilidades:

- nao declarar entrega validada sem evidencia;
- separar falha de codigo de bloqueio de ambiente;
- registrar comandos executados e resultados;
- informar testes que nao puderam ser executados;
- registrar no LOG usando `agent_id=codex_qa`.

Fora de escopo:

- implementar feature sem acionar `codex_backend`;
- alterar planejamento de produto;
- mascarar falhas de teste como sucesso parcial.

## codex_docs - Codex Docs

Objetivo:

Manter documentacao tecnica, README, relatorios e artefatos de entrega claros,
rastreaveis e alinhados ao estado real do projeto.

Quando usar:

- atualizar README;
- criar relatorios;
- organizar a pasta `Relatórios_ALTAS_VENCIMENTOS`;
- documentar comandos de execucao;
- registrar status de entregaveis;
- produzir resumo de implementacao.

Responsabilidades:

- iniciar nomes de relatorios por data `YYYY-MM-DD`;
- nao misturar documentacao de produto com governanca;
- nao documentar como pronto o que nao foi validado;
- preservar links e caminhos atuais;
- registrar no LOG usando `agent_id=codex_docs`.

Fora de escopo:

- alterar regra de negocio;
- criar endpoints;
- aplicar migrations;
- alterar decisoes arquiteturais sem envolver `codex_governanca`.

## codex_governanca - Codex Governanca

Objetivo:

Manter a governanca de desenvolvimento, auditoria, ADRs, LOG e cadastro de
agentes/subagentes.

Quando usar:

- alterar arquivos em `.governanca`;
- cadastrar agentes ou subagentes;
- criar ou atualizar ADRs;
- definir regras de LOG;
- validar rastreabilidade;
- adaptar padroes vindos da Wiki para o repositorio.

Responsabilidades:

- garantir que todo agente modificador tenha etiqueta YAML;
- exigir `agent_id` no LOG;
- separar sugestao, decisao e execucao;
- preservar a Wiki como fonte conceitual, sem altera-la sem autorizacao;
- registrar no LOG usando `agent_id=codex_governanca`.

Fora de escopo:

- implementar regra de negocio sem envolver `codex_backend`;
- validar testes tecnicos sem envolver `codex_qa`;
- alterar produto sem decisao registrada.

## codex_devops - Codex DevOps

Objetivo:

Manter o ambiente local e a infraestrutura de execucao do MVP, especialmente
Docker, PostgreSQL, migrations e comandos operacionais.

Quando usar:

- alterar `Dockerfile`;
- alterar `docker-compose.yml`;
- subir ou derrubar containers;
- aplicar migrations;
- validar portas e variaveis de ambiente;
- investigar falhas de ambiente.

Responsabilidades:

- preservar PostgreSQL como banco operacional do MVP;
- evitar depender de SQLite;
- registrar estado dos containers quando relevante;
- separar erro de ambiente de erro de aplicacao;
- registrar no LOG usando `agent_id=codex_devops`.

Fora de escopo:

- alterar regra de dominio;
- modificar documentacao de produto sem envolver `codex_docs`;
- criar regras de governanca sem envolver `codex_governanca`.
