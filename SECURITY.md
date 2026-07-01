# Seguranca

## Diretrizes iniciais

- Nunca grave credenciais, tokens ou senhas no repositorio.
- Use variaveis de ambiente para segredos e configuracoes por ambiente.
- Nao exponha dados pessoais, comerciais ou operacionais nas respostas da API.
- Acesso a bancos de terceiros deve ser autorizado e preferencialmente somente
  leitura.
- Logs nao devem conter credenciais, payloads completos nem dados criticos.
- Arquivos CSV/XLSX e respostas de APIs externas devem ser tratados como dados
  nao confiaveis e validados antes do processamento.
- Credenciais de integracao devem possuir o menor privilegio possivel e rotacao
  definida.

## Relato de vulnerabilidade

Nao abra uma issue publica com detalhes exploraveis. Comunique o mantenedor do
repositorio por um canal privado e inclua impacto, forma de reproducao e versao
afetada.
