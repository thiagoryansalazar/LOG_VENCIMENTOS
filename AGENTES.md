# Instrucoes para agentes

## Regras de execucao

1. Trabalhe somente dentro deste repositorio.
2. Consulte a Wiki `CEREBRO_ENGINEER_WIKI` como referencia; nao a altere durante
   tarefas deste projeto sem autorizacao explicita.
3. Leia o estado atual do codigo e do Git antes de editar.
4. Nao implemente funcionalidades fora do escopo solicitado.

## Padrao de codigo

- Use Python com tipagem, nomes claros e funcoes pequenas.
- Separe transporte HTTP, validacao, dominio e integracoes.
- Nao coloque regras de negocio em views.
- Preserve o contrato canonico de lotes e documente mudancas.
- Nunca inclua segredos ou caminhos locais fixos.

## Decisoes e testes

- Registre decisoes relevantes em `docs/backend.md`.
- Escreva ou atualize testes para toda regra alterada.
- Execute os testes antes de considerar uma iteracao concluida.
- Faca teste de mesa para cada nova regra de negocio.

## PDCA obrigatorio

Em cada iteracao:

1. **Plan:** declare objetivo, arquivos afetados e resultado esperado.
2. **Do:** implemente a menor mudanca coerente.
3. **Check:** execute testes automatizados e testes de mesa.
4. **Act:** corrija falhas e documente a decisao validada.
