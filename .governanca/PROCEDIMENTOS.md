# Procedimentos Operacionais Padrao

## Antes de qualquer acao

1. Ler `.governanca/README.md`.
2. Ler `.governanca/AGENTS.md`.
3. Ler `.governanca/AGENTES/regras_de_identificacao.md`.
4. Ler `.governanca/AGENTES/id_agentes.yaml`.
5. Ler `.governanca/DECISOES.md`.
6. Ler `.governanca/PROCEDIMENTOS.md`.
7. Verificar estado do repositorio:

```bash
git status --short --branch
```

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
