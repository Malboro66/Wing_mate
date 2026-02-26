# Checklist Obrigatório de Acessibilidade Operacional (Desktop)

## Navegação por teclado

- [ ] Fluxo principal acessível sem mouse (seleção de pasta, campanha, troca de abas, sincronização).
- [ ] Ordem de foco explícita nos elementos principais (`setTabOrder`) em telas críticas.
- [ ] Campo de busca/filtro com foco padrão em listas densas quando aplicável.
- [ ] Atalhos padronizados e documentados (ex.: `Ctrl+F`, `Ctrl+O`, `F5`).

## Foco e labels

- [ ] Controles críticos com `accessibleName` consistente.
- [ ] Componentes interativos com tooltips/labels claros.
- [ ] Tabelas/listas com foco previsível e seleção por teclado.

## Contraste e feedback

- [ ] Estados visuais usam tokens do design system (`STATE_INFO/SUCCESS/WARNING/ERROR`).
- [ ] Loading unificado via `SkeletonWidget`.
- [ ] Feedback não bloqueante unificado via `ToastWidget`/`NotificationBus`.
- [ ] Erros acionáveis via `show_actionable_error` sem expor detalhes técnicos na UI.

## Regressão automatizada

- [ ] Testes de contrato para atalhos e foco em telas críticas.
- [ ] Testes de contrato para consistência de feedback (erro/sucesso/loading).
- [ ] Pipeline CI executa esses contratos em PR.


## Telas críticas cobertas por contrato

- Janela principal (`MainWindow`): ordem de foco e atalhos `Ctrl+O`/`F5`.
- Missões e Esquadrões: contrato de `Ctrl+F` com `CtrlFFocusMixin`.
- Medalhas: labels acessíveis e foco inicial em busca.
- Feedback operacional: `ToastWidget` e `SkeletonWidget` ligados a tokens de design (`DSFeedback`).
