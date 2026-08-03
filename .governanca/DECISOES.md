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
