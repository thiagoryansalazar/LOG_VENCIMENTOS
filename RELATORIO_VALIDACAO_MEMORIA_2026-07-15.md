# Relatorio de validacao da memoria operacional - 15/07/2026

## Objetivo

Validar que a memoria operacional do ATLAS Vencimentos esta pronta para receber
dados vindos futuramente do adaptador ERP ou CSV.

Esta validacao nao implementou endpoints novos, adaptadores ou regras de alerta.
O foco foi confirmar persistencia, Admin e relacionamento entre os models.

## Ambiente validado

- Projeto local: `C:\TECH PROJETOS\LOG_VENCIMENTOS`
- Banco: PostgreSQL via Docker Compose
- App validado: `core`
- Models validados:
  - `AnaliseLote`
  - `Alerta`
  - `ConfiguracaoAlerta`

## Superusuario

Foi criado/validado um superusuario local para acesso ao Django Admin.

Dados usados no ambiente local:

```text
username: admin
email: admin@atlas.local
```

## Migrations

Comando executado:

```bash
python manage.py showmigrations core
```

Resultado confirmado:

```text
core
 [X] 0001_initial
```

## Registros de teste criados/validados

### AnaliseLote

```text
codigo_produto: PROD-001
lote: L2026-01
data_validade: 2026-07-20
dias_restantes: 5
classificacao: CRITICO
origem: CSV
```

Resultado:

```text
analise_id: 1
```

### Alerta

```text
analise_lote: AnaliseLote id 1
classificacao: CRITICO
mensagem: Lote proximo ao vencimento
destinatario: teste@empresa.com
```

Resultado:

```text
alerta_id: 1
relacionamento_ok: True
```

### ConfiguracaoAlerta

```text
classificacao: CRITICO
canal: EMAIL
destinatario: gestor@empresa.com
ativo: True
```

Resultado:

```text
configuracao_id: 1
```

## Validacao do Django Admin

Foi validado que os tres models estao registrados no Django Admin.

Resultado:

```text
admin_models_registrados: True
```

As paginas do Admin responderam com sucesso usando login de superusuario:

```text
/admin/                             -> 200
/admin/core/analiselote/            -> 200
/admin/core/alerta/                 -> 200
/admin/core/configuracaoalerta/     -> 200
```

## Validacao no banco

Totais confirmados apos a validacao:

```text
AnaliseLote: 1
Alerta: 1
ConfiguracaoAlerta: 1
```

O relacionamento `Alerta -> AnaliseLote` foi confirmado pelo campo
`analise_lote_id`.

## Erros encontrados

### Docker Desktop inativo

No inicio da validacao, o Docker Desktop nao estava rodando. Por isso, o
PostgreSQL nao respondia em `localhost:5432`.

Acao tomada:

- Docker Desktop iniciado.
- `docker compose up -d` executado.
- Container `log_vencimentos-db-1` confirmado em execucao.

### Host `testserver` nao permitido no Admin

Ao validar o Admin com o cliente de testes do Django, o host padrao `testserver`
gerou erro `400` por nao estar em `ALLOWED_HOSTS`.

Acao tomada:

- Validacao repetida com host permitido `localhost`.
- Resultado final: todas as telas do Admin retornaram `200`.

## Status final

Validacao concluida com sucesso.

A memoria operacional esta funcional para receber dados persistidos pelo fluxo
de integracao que sera implementado nas proximas etapas.

## Proximos passos

- Base validada, pronta para adaptador CSV.
- Implementar leitura CSV mockada.
- Implementar mapeador CSV para o contrato interno.
- Conectar adaptador CSV ao core de monitoramento.
- Persistir novas analises usando `AnaliseLote`.
- Gerar alertas a partir das analises persistidas em etapa posterior.

