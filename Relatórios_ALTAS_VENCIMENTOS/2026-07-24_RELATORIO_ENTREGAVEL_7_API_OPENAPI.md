# Relatorio do Entregavel 7 - API v1 e OpenAPI

Data: 2026-07-24

Projeto: ATLAS Vencimentos

Agente responsavel: Codex

agent_id: codex_docs

## Objetivo

Implementar os endpoints de consulta da API v1 e a documentacao OpenAPI do
ATLAS Vencimentos.

## Subagentes Acionados

- `codex_explorer`: mapeamento read-only da API atual.
- `codex_designer`: desenho tecnico read-only da solucao.
- `codex_implementer`: implementacao da API v1.
- `codex_tester`: testes e validacoes.
- `codex_reviewer`: revisao final read-only.
- `codex_github`: versionamento e publicacao no GitHub.

## Endpoints Entregues

- `POST /api/v1/lotes/validar`
- `GET /api/v1/lotes`
- `GET /api/v1/lotes?codigo_produto=XXX&lote=YYY`
- `GET /api/v1/lotes/criticos`
- `POST /api/v1/alertas/disparar`
- `GET /api/schema/`
- `GET /api/docs/`

## Autenticacao

Continuam publicos:

- `GET /health`
- `GET /api/schema/`
- `GET /api/docs/`

Os demais endpoints seguem protegidos pelo header:

```http
X-API-Key: <chave>
```

## Decisao MVP

Foi registrada a ADR-0005:

No MVP, lotes criticos nao resolvidos sao interpretados como analises com
classificacao `CRITICO` ou `VENCIDO`, porque ainda nao existe campo ou processo
formal de resolucao operacional.

## Arquivos Alterados

- `requirements.txt`
- `config/settings.py`
- `src/config/middleware.py`
- `src/routes/serializers.py`
- `src/routes/views.py`
- `src/routes/urls.py`
- `tests/test_api_v1.py`
- `README.md`
- `.governanca/DECISOES.md`
- `.governanca/LOG.md`

## Validacoes Executadas

```bash
docker compose up -d --build
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py test tests.test_api_v1 -v 2
docker compose exec -T web python manage.py test -v 2
docker compose exec -T web python manage.py spectacular --validate --file /tmp/schema.yaml
```

Resultado:

- Django check: OK.
- Testes API v1: 9 testes OK.
- Suite completa: 40 testes OK.
- OpenAPI schema: gerado e validado.
- `/api/schema/`: publico e retornando OpenAPI.
- `/api/v1/lotes`: validado com `X-API-Key` e dados reais do banco local.

## Riscos Residuais

- `GET /api/v1/lotes/criticos` ainda nao representa baixa operacional real;
  isso depende de um campo ou processo futuro de resolucao.
- `POST /api/v1/alertas/disparar` pode enviar email real em ambiente com
  credenciais SMTP validas. Em testes, o servico foi mockado.

## Status Final

Entregavel 7 concluido.

API v1 e documentacao OpenAPI estao implementadas, protegidas por API Key nos
endpoints privados e cobertas por testes automatizados.

## Fechamento do Backend MVP - 2026-07-24

Foram executadas correcoes finais para alinhar o backend do MVP ao cronograma
real:

- regras de vencimento parametrizadas por `DIAS_CRITICO` e `DIAS_ATENCAO`;
- `README.md` revisado com variaveis de ambiente, Docker, endpoints,
  autenticacao e testes;
- `CRONOGRAMA.md` corrigido para refletir Entregavel 7 concluido em
  24/07/2026;
- `MVP_CHECKLIST.md` criado na raiz do projeto;
- registrada ADR-0006 sobre limites de classificacao configuraveis.

Validacoes finais executadas para fechamento:

```bash
docker compose config
docker compose up -d --build
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py test -v 2
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv --dry-run
docker compose exec -T web python manage.py executar_monitoramento --fonte csv --arquivo data/lotes_mockados.csv
docker compose exec -T web python manage.py spectacular --validate --file /tmp/schema.yaml
```

Resultado:

- Docker compose config: aprovado.
- Docker build: aprovado.
- Migrations: aprovado, sem migrations pendentes.
- Django check: aprovado, sem issues.
- Suite completa: 44 testes aprovados.
- Monitoramento CSV dry-run: 6 lotes lidos, 6 processados, 0 erros.
- Monitoramento CSV persistido: 6 lotes processados, 6 registros atualizados,
  0 erros.
- Alertas: 4 alertas elegiveis foram pulados por ausencia de credenciais de
  email, comportamento esperado em ambiente sem SMTP configurado.
- `/api/docs/`: status 200.
- `/api/schema/`: status 200.
- `/health`: status 200.
- `/api/v1/lotes` com `X-API-Key`: status operacional, 6 registros retornados.
- `/api/v1/lotes` sem `X-API-Key`: status 401.
- `/api/v1/lotes/criticos` com `X-API-Key`: status operacional, 4 registros
  retornados.
- `/api/v1/lotes/<id>` com `X-API-Key`: status 200.
- `/api/v1/lotes/<id>` inexistente com `X-API-Key`: status 404.

Observacao: em 24/07/2026, parte dos lotes mockados esta classificada como
`VENCIDO` porque as datas do CSV foram definidas para validacoes anteriores.
Isso confirma que a classificacao acompanha a data corrente usada pelo backend.

Status desta secao: backend MVP validado para proxima etapa de frontend.
