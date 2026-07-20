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
