# Relatorio do entregavel - 14/07/2026

## Projeto

ATLAS Vencimentos.

## Objetivo do dia

Criar a memoria operacional inicial do MVP com app `core`, models persistentes,
registro no Django Admin, migrations e aplicacao no banco PostgreSQL.

## Implementado

- Criado o app Django `core`.
- Criado o model `AnaliseLote`.
- Criado o model `Alerta`.
- Criado o model `ConfiguracaoAlerta`.
- Criado `ClassificacaoVencimento` com as classificacoes `VENCIDO`, `CRITICO`,
  `ATENCAO` e `NORMAL`.
- Adicionado `__str__` em todos os models.
- Adicionado `Meta` com `ordering`, `verbose_name` e `verbose_name_plural`.
- Registrados os tres models no Django Admin.
- Habilitado Django Admin no projeto.
- Criada a migration inicial do app `core`.
- Aplicadas as migrations no PostgreSQL.
- Confirmado via `python manage.py showmigrations core` que a migration do
  app `core` foi aplicada.
- Atualizado o nome visual/documental do projeto para `ATLAS Vencimentos`.
- Atualizado o `CRONOGRAMA.md` com o entregavel de 14/07 concluido.

## Models criados

### AnaliseLote

Campos:

- `codigo_produto`;
- `lote`;
- `data_validade`;
- `dias_restantes`;
- `classificacao`;
- `data_analise`;
- `origem`.

### Alerta

Campos:

- `analise_lote`;
- `classificacao`;
- `mensagem`;
- `enviado_em`;
- `destinatario`.

### ConfiguracaoAlerta

Campos:

- `classificacao`;
- `canal`;
- `destinatario`;
- `ativo`.

## Validacoes executadas

```bash
python manage.py makemigrations core
python manage.py migrate
python manage.py showmigrations core
python manage.py showmigrations admin auth contenttypes sessions core
python manage.py test -v 2
python manage.py check
```

Resultado esperado confirmado:

```text
core
 [X] 0001_initial
```

## Observacoes

- O banco usado foi o PostgreSQL local via Docker.
- O Admin foi liberado do middleware de API Key porque o Django Admin usa
  autenticacao propria do Django.
- As rotas da API continuam protegidas por `X-API-Key`, exceto `/health`.

