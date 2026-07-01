# Execucao em ambiente cloud

1. Execute somente artefatos pertencentes a este repositorio.
2. Use o mesmo padrao Python, separacao de camadas e qualidade adotados
   localmente.
3. Nao leia nem grave arquivos fora do diretorio da aplicacao, exceto volumes
   explicitamente configurados.
4. Registre decisoes de infraestrutura e operacao em `docs/backend.md`.
5. Execute verificacoes e testes antes de publicar uma nova versao.
6. Aplique PDCA em cada iteracao de infraestrutura.

Configuracoes devem entrar por variaveis de ambiente. Segredos nao devem ser
gravados em imagem, codigo, log ou arquivo versionado. Em producao, substitua o
SQLite por PostgreSQL e configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e
`DJANGO_ALLOWED_HOSTS`.
