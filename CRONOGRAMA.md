# Cronograma MVP - ATLAS Vencimentos

## Referencia

- Data-base informada: 13/07/2026.
- Prazo final: 31/07/2026.
- Janela de entrega: 18 dias corridos.
- Decisao de escopo: nao fazer MCP agora.
- Regra de ouro: funciona > perfeito; integracao real > mock; alerta basico > alerta inteligente.

## Avaliacao do plano

O plano esta de acordo para um MVP, desde que o escopo seja protegido.

O que deve permanecer no MVP:

- backend Django/DRF;
- PostgreSQL local via Docker;
- entrada de dados por CSV ou JSON padronizado;
- adaptador ERP com fallback CSV;
- classificacao de vencimento configuravel;
- memoria operacional basica;
- alerta simples por email;
- comando sincrono de monitoramento;
- API com API Key fixa;
- documentacao de execucao e checklist final.

O que deve ficar fora do MVP:

- MCP;
- frontend dedicado;
- JWT/OAuth2;
- RabbitMQ e Celery;
- IoT, ESP32, LED, RFID, OCR e IA;
- controle por prateleira;
- generalizacao para outros setores;
- integracao real obrigatoria com ERP caso o acesso nao esteja disponivel.

## Entregaveis

### Entregavel 1 - Infraestrutura base

Prazo: dias 1 e 2.

Status inicial:

- [x] Django + DRF ja existe.
- [x] PostgreSQL via Docker configurado para o MVP.
- [x] PostgreSQL via Docker.
- [x] Variaveis de ambiente para banco e chaves de API.
- [x] Revisar estrutura final de pastas.

Simplificacao:

- usar Docker para PostgreSQL;
- nao usar RabbitMQ/Celery no MVP;
- processamento sincrono.

### Entregavel 2 - Camada de extracao e Adaptador ERP

Prazo: dias 3 a 5.

Status inicial:

- [x] Interface abstrata de adaptador ja existe.
- [x] Mapeador de campos abstrato ja existe.
- [x] Implementar leitura CSV para validar o fluxo.
- [ ] Implementar consulta SQL direta quando o acesso ao ERP estiver disponivel.
- [x] Criar mapeador concreto de campos externos para o contrato do LOG.

Simplificacao:

- comecar com CSV mockado;
- tentar conexao com banco real depois;
- se nao houver acesso ao ERP, documentar como pendente de integracao real.

### Entregavel 3 - Core

Prazo: dias 1 e 2.

Status inicial:

- [x] Validacao e normalizacao de lote.
- [x] Modelo de dominio `Lote`.
- [x] Servico de vencimento.
- [x] Servico de monitoramento.
- [x] Tornar regras de classificacao configuraveis por variaveis de ambiente.

Regra atual:

```text
0 dias ou menos -> VENCIDO
1 a DIAS_CRITICO dias -> CRITICO
DIAS_CRITICO+1 a DIAS_ATENCAO dias -> ATENCAO
acima de DIAS_ATENCAO dias -> NORMAL
```

Simplificacao:

- nao reescrever o core que ja funciona;
- apenas parametrizar limites como `DIAS_CRITICO` e `DIAS_ATENCAO`.

### Entregavel 4 - Memoria operacional

Prazo: dias 6 a 8.

Criar models Django:

- [x] `AnaliseLote`;
- [x] `Alerta`;
- [x] `ConfiguracaoAlerta`.

Campos minimos sugeridos:

- `AnaliseLote`: codigo_produto, lote, data_validade, dias_restantes, classificacao, data_analise, origem.
- `Alerta`: lote_id, classificacao, mensagem, enviado_em, destinatario.
- `ConfiguracaoAlerta`: classificacao, canal, destinatario, ativo.

Tarefas:

- [x] Rodar `python manage.py makemigrations`.
- [x] Rodar `python manage.py migrate`.
- [x] Habilitar modelos no Django Admin, se for util para operacao local.
- [x] Criar consultas basicas usando Django ORM.

Simplificacao:

- usar Django ORM diretamente;
- nao criar camada de repositorio complexa antes da necessidade real.

### Entregavel 5 - Central de alertas

Prazo: dias 9 a 11.

Tarefas:

- [x] Criar `services/alerta.py`.
- [x] Implementar `disparar_alerta(lote, classificacao)`.
- [x] Evitar spam verificando alerta enviado para o mesmo lote nas ultimas 24h.
- [x] Implementar envio de email por SMTP Gmail ou SendGrid.
- [x] Criar `enviar_email(destino, assunto, corpo)`.

Simplificacao:

- usar texto puro no email;
- usar SMTP Gmail com conta de teste se for mais rapido;
- trocar provider depois, se necessario.

### Entregavel 6 - Orquestracao do fluxo completo

Prazo: dias 12 a 14.

Criar comando Django:

```bash
python manage.py executar_monitoramento
```

Fluxo esperado:

```text
Adaptador ERP ou CSV
  -> mapeador de campos
  -> core de monitoramento
  -> salva AnaliseLote
  -> dispara alerta quando aplicavel
  -> registra logs
```

Tarefas:

- [x] Buscar lotes pelo adaptador.
- [x] Processar cada lote individualmente.
- [x] Salvar analise no PostgreSQL.
- [x] Disparar alerta para classificacoes configuradas.
- [x] Continuar processamento quando um lote falhar.
- [x] Registrar logs claros do resultado.

Simplificacao:

- comando sincrono;
- sem Celery no MVP.

### Entregavel 7 - API publica

Prazo: dias 15 a 17.

Status: concluido e validado em 24/07/2026.

Autenticacao:

- [x] API Key fixa no `.env`.
- [x] Header: `X-API-Key`.
- [x] Middleware simples para proteger endpoints sensiveis.

Endpoints:

- [x] `GET /health`.
- [x] `POST /lotes/validar`.
- [x] `POST /api/v1/lotes/validar`.
- [x] `GET /api/v1/lotes?codigo_produto=XXX&lote=YYY`.
- [x] `GET /api/v1/lotes/criticos`.
- [x] `POST /api/v1/alertas/disparar`.
- [x] `GET /api/v1/lotes/<id>`.
- [x] `/api/docs/` com `drf-spectacular`.

Erros:

- [x] Padronizar JSON para `400`.
- [x] Padronizar JSON para `401`.
- [x] Padronizar JSON para `404`.
- [x] Padronizar JSON para `500`.

Simplificacao:

- nao implementar JWT;
- nao implementar OAuth2;
- manter API Key fixa para MVP.

### Entregavel 8 - Testes e documentacao

Prazo: dia 18.

Status: validado em 24/07/2026.

Tarefas:

- [x] Testar fluxo completo localmente: CSV -> core -> PostgreSQL -> alerta -> API.
- [x] Atualizar `README.md` com execucao do MVP.
- [x] Revisar documentacao gerada pelo `drf-spectacular`.
- [x] Criar `MVP_CHECKLIST.md`.
- [x] Documentar pendencias, riscos e decisoes de corte.

Simplificacao:

- nao buscar cobertura automatizada completa neste prazo;
- manter testes automatizados existentes;
- documentar testes manuais executados.

## Cronograma detalhado

| Data | Dia | Atividade | Entregavel |
|---|---|---|---|
| 13/07/2026 | Segunda | Configurar PostgreSQL via Docker, `.env` e API Key | Entregavel 1 - concluido |
| 14/07/2026 | Terca | Criar app `core`, models `AnaliseLote`, `Alerta`, `ConfiguracaoAlerta`, Admin e migrations | Entregavel 4 - concluido |
| 15/07/2026 | Quarta | Validar migrations, Django Admin e registros de teste no PostgreSQL | Entregavel 4 - concluido |
| 16/07/2026 | Quinta | Implementar adaptador ERP mock CSV e mapeador | Entregavel 2 - concluido |
| 17/07/2026 | Sexta | Testar adaptador com dados mockados | Entregavel 2 - concluido |
| 18/07/2026 | Sabado | Reserva | - |
| 19/07/2026 | Domingo | Reserva | - |
| 20/07/2026 | Segunda | Implementar servico de alerta por email | Entregavel 5 - concluido |
| 21/07/2026 | Terca | Integrar alerta ao core | Entregavel 5 - concluido |
| 22/07/2026 | Quarta | Criar comando `executar_monitoramento` | Entregavel 6 - concluido |
| 23/07/2026 | Quinta | Testar fluxo completo com dados mockados | Entregavel 6 - antecipado em 22/07 e concluido |
| 24/07/2026 | Sexta | Concluir API v1, OpenAPI, parametrizacao de regras e checklist backend MVP | Entregavel 7 - concluido / Entregavel 8 - validado |
| 25/07/2026 | Sabado | Reserva | - |
| 26/07/2026 | Domingo | Reserva | - |
| 27/07/2026 | Segunda | Reserva para ajustes residuais e preparacao do frontend | Pos-MVP backend |
| 28/07/2026 | Terca | Preparar contrato de tela e consumo dos endpoints | Frontend |
| 29/07/2026 | Quarta | Validacao integrada frontend/backend, se o frontend ja estiver iniciado | Frontend |
| 30/07/2026 | Quinta | Revisao final de documentacao e roteiro de demonstracao | Entregavel 8 |
| 31/07/2026 | Sexta | Revisao final e demonstracao do MVP funcionando | Entrega final |

## Kanban semanal

Atualizar este quadro a cada commit relevante.

### Backlog

- [x] Parametrizar regras de vencimento por variaveis de ambiente.
- [x] Criar endpoints `/api/v1`.
- [x] Configurar `drf-spectacular`.
- [x] Atualizar README.
- [x] Criar `MVP_CHECKLIST.md`.

### Esta semana

- [x] Models `AnaliseLote`, `Alerta`, `ConfiguracaoAlerta`.
- [x] Migrations.
- [x] Django Admin validado com registros manuais.
- [x] Adaptador CSV.
- [x] Mapeador CSV.
- [x] Teste manual do adaptador.
- [x] Comando `executar_monitoramento`.
- [x] Fluxo completo com dados mockados validado.
- [x] API v1 inicial implementada.
- [x] OpenAPI em `/api/docs/` e `/api/schema/`.
- [x] Parametrizacao `DIAS_CRITICO` e `DIAS_ATENCAO`.
- [x] Checklist final do MVP criado.

### Em andamento

- [ ] Nenhum item iniciado neste quadro.

### Em revisao

- [ ] Nenhum item em revisao.

### Concluido

- [x] Backend Django/DRF criado.
- [x] Projeto renomeado para `ATLAS Vencimentos`.
- [x] PostgreSQL via Docker configurado.
- [x] Variaveis de ambiente configuradas em `.env`.
- [x] `.env.example` criado.
- [x] API Key fixa configurada por `X-API-Key`.
- [x] `/health` publico sem API Key.
- [x] `GET /health`.
- [x] `POST /lotes/validar`.
- [x] Validacao e normalizacao de lote.
- [x] Modelo de dominio `Lote`.
- [x] Servico de vencimento.
- [x] Servico de monitoramento.
- [x] Regra `0 dias ou menos -> VENCIDO`.
- [x] Contratos de integracao externa.
- [x] Modos `EVENTO`, `CONSULTA_AGENDADA`, `ARQUIVO`.
- [x] Contrato abstrato de mapeamento.
- [x] App `core` criado.
- [x] Models `AnaliseLote`, `Alerta`, `ConfiguracaoAlerta` criados.
- [x] Models registrados no Django Admin.
- [x] Superusuario criado para validacao local.
- [x] Registros de teste criados no Admin e persistidos no PostgreSQL.
- [x] Adaptador CSV criado.
- [x] Mapeador CSV criado.
- [x] Servico de alerta criado.
- [x] Envio de email desacoplado por `EmailSenderInterface`.
- [x] Supressao de alerta duplicado em 24h.
- [x] Rate limiting simples de email.
- [x] Comando `executar_monitoramento` criado.
- [x] Fluxo completo CSV -> core -> PostgreSQL -> alerta validado com dados mockados.
- [x] `POST /api/v1/lotes/validar`.
- [x] `GET /api/v1/lotes`.
- [x] `GET /api/v1/lotes/criticos`.
- [x] `GET /api/v1/lotes/<id>`.
- [x] `POST /api/v1/alertas/disparar`.
- [x] Documentacao OpenAPI com `drf-spectacular`.
- [x] README revisado com execucao, autenticacao, endpoints e testes.
- [x] `MVP_CHECKLIST.md` criado.

### Bloqueios

- [ ] Acesso real ao banco do ERP ainda nao confirmado.
- [ ] Credenciais de SMTP/SendGrid ainda nao definidas.
- [ ] Decisao final sobre campo `status` ainda pendente.
- [ ] Decisao final sobre `empresa/unidade` no contrato do MVP ainda pendente.

## Criterio de MVP pronto

O MVP sera considerado pronto quando uma empresa conseguir:

- carregar lotes por CSV ou entrada padronizada;
- validar e normalizar os dados;
- armazenar analises no PostgreSQL;
- calcular risco de vencimento;
- gerar alerta basico;
- consultar historico e lotes criticos via API;
- demonstrar o fluxo completo localmente.
