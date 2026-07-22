# Instrucoes para Agentes de IA

Este arquivo define como um agente deve se comportar ao acessar, modificar ou
auditar o projeto ATLAS Vencimentos.

Ele adapta para desenvolvimento de software a logica da pasta `05_AGENTES` da
CEREBRO_ENGINEER_WIKI: agentes possuem etiqueta YAML, auxiliares preservam
origem e nenhuma sugestao vira decisao automaticamente.

## Regra zero

Antes de modificar qualquer arquivo, o agente deve confirmar que possui etiqueta
YAML cadastrada em `.governanca/AGENTES/id_agentes.yaml`.

Se a etiqueta nao existir, o agente deve parar e solicitar cadastro.

Agente sem etiqueta YAML cadastrada nao pode alterar:

- codigo;
- documentacao;
- configuracao;
- scripts;
- migracoes;
- arquivos de governanca;
- arquivos de relatorio.

## Etiqueta oficial

A etiqueta oficial e o campo `id` no YAML.

Exemplo:

```yaml
id: codex
```

No LOG, a etiqueta deve aparecer como:

```text
agent_id=codex
```

## Ordem obrigatoria de entrada

Antes de qualquer implementacao, correcao, refatoracao, alteracao documental ou
execucao operacional relevante, o agente deve ler:

1. `.governanca/README.md`
2. `.governanca/AGENTS.md`
3. `.governanca/AGENTES/regras_de_identificacao.md`
4. `.governanca/AGENTES/id_agentes.yaml`
5. `.governanca/AGENTES/id_auxiliares.yaml`
6. `.governanca/DECISOES.md`
7. `.governanca/PROCEDIMENTOS.md`

Depois deve verificar:

```bash
git status --short --branch
```

## Comportamento esperado

O agente deve:

- respeitar o escopo solicitado;
- trabalhar no repositorio local correto;
- ler o codigo antes de propor alteracao;
- preservar mudancas existentes que nao fez;
- nao alterar a Wiki sem autorizacao explicita;
- tratar a Wiki como fonte conceitual quando solicitado;
- executar validacoes cabiveis;
- registrar resultado no LOG;
- usar commit claro quando houver alteracao versionavel.

O agente nao deve:

- inventar estado do projeto;
- assumir que uma tarefa foi validada sem evidencias;
- mover, apagar ou reescrever arquivos fora do escopo;
- transformar sugestao em decisao sem registrar contexto e consequencias;
- misturar documentacao de produto com governanca de desenvolvimento;
- persistir segredos em arquivos versionados.

## Agentes e auxiliares

Agente:

- possui etiqueta YAML em `id_agentes.yaml`;
- pode executar mudancas no projeto;
- deve registrar auditoria;
- responde pela rastreabilidade tecnica da acao.

Auxiliar:

- possui etiqueta YAML em `id_auxiliares.yaml`;
- apoia construcao teorica, analise ou sintese;
- nao modifica o projeto diretamente;
- nao vira decisao automaticamente;
- precisa de validacao antes de influenciar arquitetura, codigo ou produto.

## Registro obrigatorio no LOG

Toda acao relevante deve ser registrada em `.governanca/LOG.md`.

Cada registro detalhado deve conter:

- data;
- agente;
- `agent_id` com etiqueta YAML cadastrada;
- acao;
- contexto;
- arquivos alterados;
- validacoes executadas;
- resultado;
- proximos passos.

Formato compacto recomendado:

```text
[AAAA-MM-DD] tipo | arquivo/area | descricao | agent_id=<id_cadastrado>
```

Exemplo:

```text
[2026-07-21] governanca | .governanca/AGENTS.md | atualizadas regras de entrada de agentes | agent_id=codex
```

## Decisoes arquiteturais

Quando uma nova decisao arquitetural for tomada, o agente deve criar uma entrada
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

## Validacao minima

Antes de considerar a acao concluida, o agente deve executar a validacao
compativel com a mudanca.

Para Django:

```bash
python manage.py check
python manage.py test -v 2
```

Para Docker:

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

Se uma validacao nao puder ser executada, o agente deve registrar o bloqueio e a
causa objetiva no LOG.

## Git

Antes de commitar:

1. verificar `git status --short --branch`;
2. revisar `git diff`;
3. executar validacoes cabiveis;
4. registrar a acao em `.governanca/LOG.md`;
5. criar commit com mensagem clara;
6. fazer push quando a tarefa pedir atualizacao do GitHub ou quando a mudanca
   fizer parte do fluxo versionado do projeto.
