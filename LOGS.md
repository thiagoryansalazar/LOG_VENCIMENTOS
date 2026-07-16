# Logs de mudancas

## 2026-07-15 - Correcoes criticas antes do MVP

- Removido SQLite como dependencia de execucao do projeto.
- Confirmado PostgreSQL via `DATABASE_URL` com `django-environ`.
- Adicionado `Dockerfile` para executar o Django em container.
- Atualizado `docker-compose.yml` com os servicos `db` e `web`.
- Mapeada a porta local `8001` para a porta `8000` do container `web`, pois a
  porta local `8000` estava ocupada por outro container.
- Adicionado `.dockerignore` para evitar copiar `.env`, logs e artefatos locais
  para a imagem Docker.
- Convertido `src.models.Lote` de dataclass para modelo Django ORM.
- Criada migration do app `src` para a tabela `Lote`.
- Removida configuracao insegura `UNAUTHENTICATED_USER = None`.
- Mantido middleware de autenticacao por API Key usando `ATLAS_API_KEY`.
- Atualizado `.gitignore` para manter `.env`, logs e artefatos locais fora do Git.
