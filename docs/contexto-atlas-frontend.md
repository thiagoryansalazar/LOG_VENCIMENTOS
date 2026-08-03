# Contexto ATLAS Frontend

Data: 2026-07-28

## Decisoes Registradas

- O frontend ativo do ATLAS esta em `C:\TECH PROJETOS\ATLAS - FRONT_END`.
- O backend ativo do ATLAS esta em `C:\TECH PROJETOS\ATLAS VENCIMENTOS`.
- Esta pasta, `C:\Users\hugok\OneDrive\Documentos\LOG_VENCIMENTOS_APP`, deve ser tratada como contexto/roteamento historico, nao como checkout ativo do ATLAS.
- O prototipo antigo do frontend serve como referencia visual e de fluxo, mas nao como fonte de verdade de negocio.
- A fonte de verdade funcional e a API Django/DRF.

## Contrato Atual

- O frontend e uma SPA em React, TypeScript, Vite e Tailwind.
- Nao deve existir servidor Node.js dedicado para a nova versao.
- A autenticacao operacional continua via `X-API-Key`.
- `VITE_ATLAS_API_KEY` nao pode ter fallback silencioso.
- A chave exposta no navegador e aceitavel apenas para MVP interno controlado, nao para uso publico multiusuario.

## Endpoints Django Relevantes

- `GET /api/v1/lotes`
- `GET /api/v1/lotes/criticos`
- `GET /api/v1/lotes/<id>`
- `POST /api/v1/alertas/disparar`
- `POST /api/v1/lotes/validar`
- `/api/docs/`
- `/api/schema/`

## Menu Lateral

- O plano aprovado adiciona funcionalidades parciais ao menu: `Cadastrar lote manualmente`, `Configuracoes` e `Login/usuario`.
- `Cadastrar lote manualmente` deve validar lote via `POST /api/v1/lotes/validar`, sem persistir no Django.
- `Configuracoes` deve salvar apenas preferencias locais de UI, como destinatario padrao de alerta e status/URL da API.
- Regras de risco continuam somente leitura porque sao controladas pelo backend.
- `Login/usuario` deve salvar identificacao local em `localStorage`; nao altera autenticacao real.
- O plano do menu lateral ainda precisa ser validado no codigo antes de assumir que esta implementado.

## Persistencia Local

- Preferencias locais: `atlas_preferences.defaultAlertRecipient`.
- Perfil local do operador: `atlas_user_profile.nome` e `atlas_user_profile.email`.
- Esses dados sao conveniencia de UI e nao substituem autenticacao, usuarios ou permissoes no backend.

## Melhorias de Framework Recomendadas

- Evoluir navegacao interna de `ActiveTab` para React Router quando o menu crescer.
- Extrair estado de API para hooks como `useAnalises` e `useAlertas`; TanStack Query e candidato natural.
- Criar tokens semanticos de design em `src/index.css` e reduzir cores literais nos componentes.
- Criar primitivos reutilizaveis: `Button`, `Input`, `BadgeRisk`, `EmptyState`, `ApiErrorState` e `PageHeader`.
- Adicionar lint de qualidade alem de `tsc --noEmit`, e cobrir fluxos principais com testes de UI.

## Figma

- A conta Figma conectada tem assento de visualizacao.
- Nenhum arquivo ou node Figma foi fornecido para comparacao direta de canvas.
- O uso recomendado no proximo corte e transformar os tokens/componentes do frontend em uma biblioteca Figma quando houver arquivo de destino.
