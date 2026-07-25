# Procedimentos Operacionais Padrao

## Antes de qualquer acao

1. Ler `.governanca/README.md`.
2. Ler `.governanca/AGENTS.md`.
3. Ler `.governanca/AGENTES/regras_de_identificacao.md`.
4. Ler `.governanca/AGENTES/id_agentes.yaml`.
5. Ler `.governanca/AGENTES/id_auxiliares.yaml`.
6. Ler `.governanca/DECISOES.md`.
7. Ler `.governanca/PROCEDIMENTOS.md`.
8. Verificar estado do repositorio:

```bash
git status --short --branch
```

## Procedimento de execucao com subagentes

1. Ler a governanca obrigatoria:
   - `.governanca/README.md`;
   - `.governanca/AGENTS.md`;
   - `.governanca/AGENTES/regras_de_identificacao.md`;
   - `.governanca/AGENTES/id_agentes.yaml`;
   - `.governanca/AGENTES/id_auxiliares.yaml`;
   - `.governanca/DECISOES.md`;
   - `.governanca/PROCEDIMENTOS.md`.
2. Registrar entendimento da tarefa:
   - objetivo;
   - escopo;
   - restricoes;
   - criterios de aceite;
   - arquivos citados;
   - entregaveis esperados.
3. Separar em tasks:
   - exploracao;
   - desenho tecnico;
   - implementacao;
   - banco ou infraestrutura, se aplicavel;
   - testes;
   - documentacao;
   - governanca;
   - Git/GitHub.
4. Delegar para subagentes:
   - `codex_explorer` para leitura estrutural;
   - `codex_designer` para desenho tecnico;
   - `codex_backend` ou `codex_implementer` para codigo;
   - `codex_devops` para Docker, banco e migrations;
   - `codex_tester` ou `codex_qa` para testes;
   - `codex_docs` para relatorios e README;
   - `codex_governanca` para LOG, ADRs e regras;
   - `codex_reviewer` para revisao final;
   - `codex_github` para stage, commit, push e estado remoto.
5. Integrar resultados:
   - revisar arquivos alterados;
   - resolver conflitos;
   - conferir aderencia ao escopo.
6. Validar:
   - executar comandos exigidos;
   - registrar evidencias;
   - nao declarar sucesso sem validacao.
7. Finalizar:
   - atualizar `.governanca/LOG.md`;
   - criar relatorio quando solicitado ou quando houver entrega relevante;
   - executar `git status --short --branch`;
   - commitar com mensagem clara;
   - fazer push quando a tarefa exigir atualizacao do GitHub.

Se uma tarefa for simples e nao justificar subagente, registrar no LOG o motivo
da execucao direta.

## Validar Django

```bash
python manage.py check
python manage.py test -v 2
```

Quando houver alteracao de models:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

## Validar Docker

```bash
docker compose up -d --build
docker compose ps
docker compose exec -T web python manage.py check
```

## Criar novo model Django

1. Criar ou alterar o model.
2. Criar migration.
3. Aplicar migration.
4. Confirmar com `showmigrations`.
5. Registrar a acao em `.governanca/LOG.md`.

## Registrar decisao arquitetural

Adicionar entrada em `.governanca/DECISOES.md` com:

- titulo;
- data;
- contexto;
- decisao;
- consequencias;
- status.

## Registrar atividade do Codex

Adicionar entrada em `.governanca/LOG.md` contendo:

- data;
- agente: `Codex`;
- `agent_id`: `codex`;
- acao;
- arquivos alterados;
- validacoes;
- resultado;
- proximos passos.

Quando a acao fizer parte de uma tarefa orquestrada, registrar tambem os
subagentes envolvidos e se a atuacao foi de execucao, validacao, revisao ou
somente leitura.
