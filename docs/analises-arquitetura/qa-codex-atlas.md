# QA Report — Solicitação ao Codex (Atlas como hub de inteligência)

## Escopo da solicitação
Registrar a visão futura do Atlas como hub de inteligência de estoque, com arquitetura de dois fluxos, sem alterar o escopo executável do MVP.

## Artefatos alterados

| Arquivo | Ação | Linhas |
|---------|------|--------|
| `README.md` | Modificado (+38) | Seção "Visão futura da API" |
| `SUGESTOES.md` | Modificado (+17) | Subseção "API como produto" |
| `docs/atlas_api_futura.md` | **Criado** (+241) | Documento completo da visão Atlas |
| `docs/backend.md` | Modificado (+47) | PDCA 005 |

## Análise de Qualidade

### ✅ Acertos

| Item | Justificativa |
|------|---------------|
| Estrutura PDCA completa | Plan/Do/Check/Act bem definidos, consistentes com os PDCA anteriores |
| Dois fluxos bem definidos | Fluxo interno (entrada) e externo (saída) claramente separados |
| Alinhamento conceitual | Preserva decisões anteriores: ERP como fonte de verdade, Atlas não vira ERP, core puro |
| Limitação de escopo correta | Diz explicitamente que Redis, Celery, MCP não são para o MVP |
| Estratégia de auth pragmática | API Key no MVP → JWT/OAuth2 no futuro, sem overengineering |
| Referências corretas ao código | `src/services/monitoramento.py` citado corretamente |

### ⚠ Não Conformidades

| ID | Severidade | Arquivo | Problema |
|----|------------|---------|----------|
| NC01 | **Média** | `README.md` | A seção "Visão futura da API" (34 linhas) é pesada para um README — duplica conteúdo do `atlas_api_futura.md`. README deveria apenas referenciar o doc detalhado, não reproduzi-lo. |
| NC02 | **Média** | `README.md` / `atlas_api_futura.md` | O exemplo de resposta usa `produto: { codigo, nome }` aninhado, mas o modelo `Lote` atual tem `codigo_produto` e `nome_produto` como campos planos. Isso gera ruído: não deixa claro se é um formato futuro ou um erro. |
| NC03 | **Baixa** | `SUGESTOES.md` | A subseção "API como produto" duplica informação que já está em `atlas_api_futura.md`. Gera risco de divergência futura entre os dois documentos. |
| NC04 | **Baixa** | `README.md` | A lista "Ainda não implementado" não foi atualizada para incluir OpenAPI, API Key, versionamento `/api/v1/` — itens que o próprio PDCA 005 lista como "para avaliar". |
| NC05 | **Alta** | Todos | **Apenas documentação, zero código.** Se a expectativa era implementação concreta (ex.: adicionar versionamento de rota, middleware de API Key, serializers DRF), o Codex não entregou. |

### 🔴 Riscos Identificados

| Risco | Descrição |
|-------|-----------|
| **Divergência documentação × código** | O documento diz "manter API versionada" e "autenticação por API Key", mas a análise arquitetural mostrou que rotas NÃO são versionadas e autenticação NÃO existe. O documento registra a intenção mas não reduz o gap. |
| **Falso senso de progresso** | 341 linhas de documentação adicionadas sem uma linha de código. Para um observador externo, parece que "a funcionalidade foi implementada" — mas não foi. |
| **Peso do README** | O README saltou de 149 para 187 linhas com conteúdo de visão futura. README deve ser enxuto; docs detalhados pertencem a `docs/`. |

### 📊 Métricas da Entrega

| Métrica | Valor |
|---------|-------|
| Arquivos modificados | 4 |
| Linhas adicionadas | 343 |
| Linhas de código | 0 |
| Linhas de documentação | 343 |
| Testes alterados | 0 |
| Funções/classes implementadas | 0 |
| Complexidade ciclomática adicionada | 0 |

### Recomendações

1. **Acurar inconsistências (NC02)**: Ajustar o exemplo de resposta para usar `codigo_produto` e `nome_produto` planos, ou marcar explicitamente como "formato futuro pretendido".
2. **Reduzir duplicação (NC01, NC03)**: Manter `README.md` conciso com apenas um link para `docs/atlas_api_futura.md`; idem para `SUGESTOES.md`.
3. **Atualizar "Ainda não implementado" (NC04)**: Refletir no README os itens do PDCA 005 que ainda não foram feitos (OpenAPI, API Key, `/api/v1/`).
4. **Avaliar NC05**: Se a solicitação incluía implementação, o Codex não atendeu. Reabrir com escopo focado em código.

## Conclusão

Documentação conceitualmente correta e alinhada, porém com 343 linhas de markdown e zero de implementação. Risco principal: divergência entre o que o documento promete e o que o código entrega.
