# Registro de Decisoes Arquiteturais

Este arquivo registra decisoes arquiteturais do desenvolvimento do ATLAS
Vencimentos.

## ADR-0001 - Governanca de desenvolvimento no repositorio

Data: 2026-07-16

Status: Implementada

### Contexto

O projeto precisa de rastreabilidade, auditoria e controle sobre a atuacao de
agentes de IA e sobre decisoes tecnicas relevantes.

O objetivo nao e criar uma wiki de produto, mas aplicar principios de
governanca ao desenvolvimento de software.

### Decisao

Criar a pasta `.governanca/` na raiz do projeto com arquivos dedicados a:

- visao geral da governanca;
- instrucoes para agentes;
- registro de decisoes arquiteturais;
- procedimentos operacionais;
- log de atividades;
- indice de navegacao.

### Consequencias

- Toda acao relevante passa a exigir registro em `.governanca/LOG.md`.
- Novas decisoes arquiteturais devem ser registradas neste arquivo.
- O Codex deve consultar a governanca antes de agir no projeto.
- A documentacao de produto continua fora desta estrutura.

## ADR-0002 - Provedor de email configuravel para alertas

Data: 2026-07-19

Status: Implementada

### Contexto

O MVP precisa enviar alertas de lotes `CRITICO` e `VENCIDO` por email, mas o
provedor pode mudar entre Gmail, SendGrid ou outro SMTP sem alterar a regra de
negocio.

Tambem e necessario evitar duplicidade de alertas e limitar envios para reduzir
risco de bloqueio pelo provedor.

### Decisao

Criar uma interface `EmailSenderInterface` e carregar a implementacao concreta
pela configuracao `EMAIL_SENDER_CLASS`.

Implementar `GmailSender` como primeiro provedor SMTP e centralizar o fluxo de
alertas em um servico desacoplado, com supressao de duplicidade em 24 horas e
rate limit simples de 5 emails por minuto.

### Consequencias

- A troca de provedor de email passa a ser feita por configuracao.
- A regra de negocio nao depende diretamente do Gmail.
- Alertas duplicados para a mesma analise e classificacao sao suprimidos.
- O rate limit atual e em memoria e deve ser substituido por cache distribuido
  quando houver multiplas instancias.

## ADR-0003 - Data de referencia obrigatoria no dominio

Data: 2026-07-20

Status: Implementada

### Contexto

O calculo de vencimento nao deve depender implicitamente do relogio da maquina
em funcoes de dominio, porque isso torna testes, simulacoes e auditoria menos
deterministicos.

### Decisao

Tornar `hoje` obrigatorio em `calcular_dias_restantes`, `classificar_risco` e
`monitorar_lote`.

As bordas do sistema, como API e scripts, continuam podendo usar `date.today()`,
mas precisam passar essa data explicitamente para o core.

### Consequencias

- O core fica deterministico e testavel por data de referencia.
- Chamadas internas precisam informar `hoje`.
- A API preserva o comportamento atual ao passar `date.today()` na camada de
  entrada.

## ADR-0004 - Orquestracao obrigatoria por subagentes especializados

Data: 2026-07-22

Status: Implementada

### Contexto

O projeto ATLAS Vencimentos adotou governanca de desenvolvimento com agentes
identificados por etiquetas YAML. Porem, apenas registrar IDs no LOG nao garante
separacao real de responsabilidades nem auditoria suficiente sobre quem
analisou, implementou, testou, documentou ou publicou uma mudanca.

O usuario definiu que o fluxo correto deve simular uma equipe de engenharia de
software: uma tarefa recebida deve ser quebrada, delegada a subagentes
especializados, executada por area, integrada pelo Codex orquestrador,
validada, registrada em LOG, commitada e enviada ao GitHub.

### Decisao

Adotar o fluxo obrigatorio de orquestracao por subagentes especializados.

O Codex passa a atuar como orquestrador principal. Ele deve preservar
integralmente a solicitacao original, separar a tarefa em blocos, delegar para
subagentes cadastrados, integrar os resultados, executar validacao final,
registrar logs, commitar e fazer push quando aplicavel.

Cada subagente deve usar seu proprio `agent_id` cadastrado em YAML. A autoria
no LOG deve refletir quem executou a acao, e nao apenas o agente orquestrador.

Foi criado o agente `codex_github` para operacoes de Git e GitHub.

### Consequencias

- A rastreabilidade das entregas aumenta.
- O LOG passa a representar melhor a cadeia de responsabilidade.
- Mudancas complexas exigem decomposicao antes da implementacao.
- O Codex precisa diferenciar execucao direta de execucao delegada.
- Subagentes read-only podem revisar e propor, mas nao devem aparecer como
  autores de alteracoes.
- Git, commit e push devem ser registrados por `agent_id=codex_github`.

## ADR-0005 - Interpretacao MVP para lotes criticos nao resolvidos

Data: 2026-07-24

Status: Implementada

### Contexto

O Entregavel 7 exige o endpoint `GET /api/v1/lotes/criticos` para listar lotes
com classificacao `CRITICO` ou `VENCIDO` nao resolvidos.

O modelo `AnaliseLote` ainda nao possui campos como `resolvido`, `status`,
`tratado_em` ou ciclo operacional de baixa.

### Decisao

No MVP, "nao resolvido" sera interpretado como toda analise com classificacao
`CRITICO` ou `VENCIDO`.

Nao sera criado novo campo no modelo neste entregavel para evitar ampliar o
escopo e introduzir uma regra operacional ainda nao definida.

### Consequencias

- O endpoint de criticos fica simples e aderente ao modelo atual.
- A API nao representa ainda um fluxo de resolucao ou baixa operacional.
- Quando o processo de conferencia/baixa for definido, o modelo deve evoluir
  com um campo ou entidade propria para resolucao.

## ADR-0006 - Limites de classificacao configuraveis por ambiente

Data: 2026-07-24

Status: Implementada

### Contexto

O MVP classifica lotes em `VENCIDO`, `CRITICO`, `ATENCAO` e `NORMAL`.
Inicialmente, os limites de `CRITICO` e `ATENCAO` estavam fixos no codigo como
7 e 30 dias.

Esses limites podem variar por operacao, setor ou decisao de gestao. Alterar
codigo para cada ajuste de faixa reduziria auditabilidade e dificultaria
implantacoes em ambientes diferentes.

### Decisao

Ler os limites pelas variaveis de ambiente `DIAS_CRITICO` e `DIAS_ATENCAO`,
com padroes de MVP iguais a 7 e 30.

A regra preservada e:

- `dias_restantes <= 0`: `VENCIDO`;
- `1..DIAS_CRITICO`: `CRITICO`;
- `DIAS_CRITICO+1..DIAS_ATENCAO`: `ATENCAO`;
- acima de `DIAS_ATENCAO`: `NORMAL`.

`DIAS_CRITICO` deve ser menor que `DIAS_ATENCAO`.

### Consequencias

- A classificacao pode ser ajustada por ambiente sem refatorar o core.
- Testes passam a cobrir limites configuraveis.
- Configuracoes inconsistentes podem gerar comportamento operacional ambiguo;
  por isso, a relacao entre os limites deve ser validada antes de ambientes
  produtivos.

## ADR-0007 - Lote convertido de ORM para dataclass

Data: 2026-07-24

Status: Implementada

### Contexto

O modelo `Lote` em `src/models/lote.py` era uma subclasse de `models.Model` do
Django, com migration `0001_initial` que criava a tabela `src_lote`. Apesar
disso, `Lote` nunca era salvo no banco — era usado exclusivamente como DTO
(data transfer object) dentro do validador `src/validators/lote.py`, que criava
instancias e as retornava para o servico de monitoramento.

A tabela `src_lote` existia no banco mas estava sempre vazia, gerando falso
positivo de que `Lote` era uma entidade persistida.

### Decisao

Converter `Lote` de `models.Model` para `@dataclass` puro, eliminando:

- heranca de `models.Model`;
- campos `CharField`, `DecimalField`, `DateField`;
- classe `Meta` com `ordering`, `verbose_name`, `verbose_name_plural`;
- metodo `clean()` com `ValidationError`.

A validacao de campos continua sendo feita exclusivamente em
`src/validators/lote.py`, que ja aplicava todas as regras antes de instanciar
`Lote`.

A migration `0002_remove_lote_orm` foi gerada e aplicada para remover a tabela
`src_lote` do banco. A migration `0001_initial` foi preservada para manter a
cadeia de migracoes consistente.

### Consequencias

- A API e os testes continuam funcionando sem alteracoes: `Lote` ainda e
  exportado de `src.models` e usado como tipo de retorno.
- A tabela `src_lote` foi removida do banco de dados, eliminando o ORM fantasma.
- A migration `0002_remove_lote_orm` deve constar em qualquer deploy que ja
  tenha aplicado `0001_initial`.
- Nenhuma regra de negocio foi alterada; `Lote` permanece imutavel apos
  criacao (dataclass frozen seria via `@dataclass(frozen=True)`, mas optou-se
  por manter padrao para compatibilidade com codigo existente).

## ADR-0008 - Frontend ATLAS como SPA estatica conectada ao Django

Data: 2026-07-25
Status: Implementada

### Contexto

O prototipo visual do frontend ATLAS foi criado como uma aplicacao autonoma em
React/Vite com servidor Node.js/Express, dados em memoria, regras locais de
risco, endpoints proprios e integracao Gemini.

O backend oficial do ATLAS Vencimentos ja existe em Django/DRF, com API REST,
PostgreSQL, OpenAPI e autenticacao por `X-API-Key`. Manter o servidor Express
do prototipo criaria uma segunda fonte de verdade e duplicaria regras de
negocio.

### Decisao

Reconstruir o frontend como SPA estatica React/TypeScript/Vite/Tailwind,
consumindo exclusivamente a API Django para dados e comandos do MVP.

O prototipo fica como referencia visual e de experiencia operacional, nao como
modelo de backend ou regra de negocio.

O primeiro corte do frontend inclui:

- dashboard com metricas calculadas a partir de `GET /api/v1/lotes`;
- tabela de analises de lote;
- busca, filtro por risco e ordenacao locais;
- disparo individual de alerta por `POST /api/v1/alertas/disparar`;
- cliente HTTP tipado com `X-API-Key`;
- mapeador `AnaliseLote` Django para contrato visual.

Ficam fora do MVP frontend:

- CRUD de lotes;
- resolucao de lotes;
- historico de alertas e resolucoes;
- dados financeiros;
- simulacao de data;
- Gemini/IA no frontend.

### Consequencias

- O Django permanece fonte da verdade.
- O frontend nao recalcula classificacao de risco.
- Funcionalidades sem contrato backend deixam de aparecer na UI.
- A API Key no navegador e aceitavel apenas para MVP local/controlado; para
  producao publica, sera necessario modelo de autenticacao mais adequado.
- `server.ts` permanece somente como referencia historica do prototipo e fica
  fora do build/typecheck da SPA.

## ADR-0009 - Cadastro manual, importacao de arquivos e configuracao

Data: 2026-08-08

Status: Implementada

### Contexto

A SPA precisava de telas reais de cadastro e configuracao no lugar dos
placeholders. Para o cadastro, o usuario pediu cadastro manual individual e
importacao de arquivos comuns de dados (Excel, CSV, JSON, TXT). Para
configuracao, a tela deveria permitir configurar o sistema sem inventar
persistencia no frontend.

O backend nao possuia endpoint de persistencia de lotes nem de importacao:
existiam apenas consulta, validacao (sem persistir) e disparo de alerta. As
regras de classificacao sao definidas por ambiente (`DIAS_CRITICO`/`DIAS_ATENCAO`,
ADR-0006) e nao existe modelo de configuracoes exposto por API.

### Decisao

1. Criar `POST /api/v1/lotes/cadastrar`: cadastra uma analise manual (codigo,
   lote, data de validade, origem). A classificacao e sempre calculada no
   servidor (o frontend nunca recalcula risco, ADR-0008) e a persistencia usa
   `update_or_create` respeitando a unicidade `(lote, codigo_produto)`.
2. Criar `POST /api/v1/lotes/importar`: recebe um arquivo via multipart
   (`.csv`, `.xlsx`, `.json`, `.txt`), valida no servidor por extensao e tamanho
   (5MB), normaliza colunas com aliases comuns de exportacao e processa linha a
   linha. Erros de linha sao coletados e devolvidos num resumo
   `{total, importados, atualizados, invalidos, erros, tipo_arquivo}`. Arquivos
   `.xls` (Excel legado) sao rejeitados com mensagem orientando a conversao
   para `.xlsx` (openpyxl nao le o formato binario antigo).
3. Criar `GET /api/v1/config`: expoe, em modo somente leitura, os limites
   `DIAS_CRITICO`/`DIAS_ATENCAO`, fuso, status de e-mail de alertas e descricao
   das faixas. Nao permite alterar regras do servidor por API.
4. Preferencias exclusivas do operador (e-mail padrao de alertas, override de
   API base URL) ficam em `localStorage` no frontend, rotuladas como
   "configuracao local do navegador", pois nao sao estado do sistema.

Os limites de risco nao ficam editaveis nesta rodada: muda-los em runtime
exigiria um modelo persistido de configuracao, migration e ADR propria, o que
amplia escopo e risco no core de classificacao. A tela os exibe como informacao
somente leitura vinda do servidor.

### Consequencias

- O cadastro manual e a importacao passam a persistir analises com a
  classificacao calculada pelo servidor, mantendo o Django como fonte da
  verdade.
- A importacao tolera colunas comuns de exportacao, mas a validacao real e
  sempre server-side (nao confia no `accept` do navegador).
- Alterar faixas de risco continua sendo feito no `.env` do backend, sem
  expor mutacao por API neste momento.
- A API Key no navegador permanece como no MVP; o agente de login deve
  avaliar modelo de autenticacao mais robusto.

## ADR-0010 - Autenticacao de operador com JWT e convivencia com X-API-Key

Data: 2026-08-08

Status: Aceita

### Contexto

O MVP autenticava toda a API por `X-API-Key` (ADR-0008), credencial de servico
pensada para scripts e integracoes. A SPA precisava de autenticacao real de
operador (usuario/senha) com sessao, guard de rota no frontend e encerramento
de sessao, sem quebrar os scripts/consumidores que usam a API Key.

### Decisao

Adotar JWT (Bearer) via `djangorestframework-simplejwt` como mecanismo de
sessao de operador, com convivencia dual no middleware:

- O middleware aceita **OU** uma `X-API-Key` valida (credencial de servico)
  **OU** um Bearer JWT valido (sessao da SPA). Rotas publicas de auth
  (`/api/v1/auth/login|refresh|logout|me`), health e docs continuam
  acessiveis sem credencial.
- Endpoints novos: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`,
  `POST /api/v1/auth/logout` (com blacklist do refresh token) e
  `GET /api/v1/auth/me`.
- Access token expira em 30 minutos (`JWT_ACCESS_MINUTES`, default) e refresh
  em 7 dias (`JWT_REFRESH_DAYS`, default), configuráveis por ambiente.
- Throttle DRF dedicado ao login: `10/min` por IP (escopo `login`), alem do
  limite anonimo geral `100/hour`.
- Hash de senha: PBKDF2-SHA256 (padrao Django), sem armazenamento de senha em
  claro.
- Flags `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e
  `SECURE_HSTS_*` configuraveis por ambiente (desligadas em dev), para exigir
  HTTPS em producao.
- Logs do fluxo de auth em logger dedicado `atlas.auth` (login ok, falha e
  logout, com IP via X-Forwarded-For quando presente).
- Comando `criar_operador` para provisionar operador via env
  (`OPERADOR_USERNAME/PASSWORD/EMAIL`) com flag `--staff`.
- No frontend, os tokens ficam em `localStorage` (trade-off XSS documentado no
  codigo) e o cliente HTTP anexa `Authorization: Bearer` junto de `X-API-Key`,
  garantindo compatibilidade com os dois modelos.

### Consequencias

- A SPA ganha login/logout com guard de rota sem quebrar scripts com API Key.
- A revogacao de refresh token usa a blacklist do simplejwt; access tokens
  continuam validos ate expirar (30min).
- O logout no frontend e best-effort: mesmo se a API falhar, a sessao local e
  encerrada.
- Para producao publica, tokens em `localStorage` devem ser reavaliados
  (ex.: httpOnly cookies) conforme ampliado no contexto de RNFs de seguranca.
- API Key e JWT convivem; novos endpoints exigem uma das duas credenciais.

## ADR-0011 - Django serve a SPA buildada em origem unica

Data: 2026-08-09

Status: Implementada

### Contexto

O MVP precisava deixar de depender de dois servidores para teste operacional. O
frontend Vite rodava em `localhost:5173` e a API Django em `localhost:8001`, o
que mantinha CORS no fluxo local e impedia validar a experiencia final em uma
origem unica.

### Decisao

Unificar a entrega operacional com o Django servindo o build do frontend:

- O Vite gera assets com `base: '/static/'`, mantendo o dev server em 5173.
- Em build de producao, a API base padrao da SPA fica relativa (`''`), usando a
  mesma origem do navegador; em desenvolvimento continua `http://localhost:8001`.
- O backend adiciona WhiteNoise, `STATIC_ROOT`, `FRONTEND_DIST_DIR` e
  `STATICFILES_DIRS` apontando para o `dist` quando ele existe.
- Um catch-all em `config/urls.py` serve `index.html` para rotas nao-API, dando
  suporte a deep links do React Router (`/`, `/lotes`, `/dashboard`, etc.).
- O middleware de API Key/JWT passa a proteger somente `/api/*` e
  `/lotes/validar`, liberando HTML, JS, CSS e assets estaticos.
- O Docker usa multi-stage build: Node compila `ATLAS - FRONT_END` e a imagem
  Python copia o `dist` para `/app/frontend_dist`; o compose expoe tudo pela
  porta 8001.

### Consequencias

- `http://localhost:8001/` passa a servir a SPA e `/api/v1/*` segue na mesma
  origem.
- Deep links da SPA funcionam sem Nginx.
- A API continua protegida por `X-API-Key` ou Bearer JWT; assets publicos nao
  exigem credencial.
- O build Docker agora depende das duas pastas irmas no contexto
  `ATLAS_VENCIMENTO_MVP`; `.dockerignore` reduz o contexto para evitar copiar
  `node_modules`, `dist`, `.venv` e caches.

## ADR-0012 - Estoque manual por lote e historico de alteracoes

Data: 2026-08-09

Status: Implementada

### Contexto

O MVP precisa funcionar mesmo sem integracao com ERP. Para isso, o gestor deve
cadastrar lotes manualmente, informar quantidade inicial e ajustar a quantidade
disponivel quando houver vendas/baixas manuais. Os alertas precisam refletir a
quantidade atual, nao a quantidade original cadastrada.

### Decisao

- Estender `AnaliseLote` como tabela operacional de lotes do MVP, adicionando
  `nome_produto`, `quantidade_inicial`, `quantidade_atual`, `local` e `unidade`.
- Manter unicidade por `(codigo_produto, lote)`.
- Criar `HistoricoLote` para auditar alteracoes manuais de quantidade e local,
  registrando usuario, data/hora, valores anteriores e novos.
- Permitir reducao manual de `quantidade_atual`; aumentos manuais sao rejeitados
  para evitar mascarar baixa/venda com correcao indevida.
- Permitir quantidade zero, mas suprimir alerta para lote zerado.
- Usar `ATLAS_GESTOR_NOME` e `ATLAS_EMPRESA_NOME` como configuracao global do
  MVP para mensagem de alerta.
- No frontend, a edicao de quantidade/local fica na tabela de lotes, enquanto o
  "Historico de alteracoes" fica na tela de Configuracoes.

### Consequencias

- A tela de cadastro passa a capturar dados suficientes para alertas mais uteis.
- A auditoria de alteracoes fica centralizada em Configuracoes, como registro
  operacional para o gestor.
- Integracao ERP futura podera preencher os mesmos campos; se houver nome do
  produto do ERP, ele prevalece. Se nao houver, o alerta usa codigo + unidade.
- Ajustes que aumentem estoque exigirao decisao posterior (ex.: recebimento,
  inventario ou integracao ERP), pois esta rodada cobre baixa manual.
