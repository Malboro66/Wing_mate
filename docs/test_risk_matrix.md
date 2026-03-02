# Shift-left: Matriz de testes por risco

## Matriz risco × tipo de teste

| Fluxo crítico | Risco | Unitário | Contrato | Integração UI | Regressão/Smoke |
|---|---|---:|---:|---:|---:|
| 1. Startup da aplicação + splash + áudio | Alto | ✅ | ✅ | ✅ | ✅ |
| 2. Seleção de pasta/campanha + sincronização | Alto | ✅ | ✅ | ✅ | ✅ |
| 3. Parse de Campaign/Mission/CombatReports | Alto | ✅ | ✅ | ⚪ | ✅ |
| 4. Navegação por teclado e foco em telas críticas | Médio | ⚪ | ✅ | ✅ | ✅ |
| 5. Atalhos operacionais (`Ctrl+F`, `Ctrl+O`, `F5`) | Médio | ⚪ | ✅ | ✅ | ✅ |
| 6. Feedback operacional (erro/sucesso/loading/toast) | Médio | ✅ | ✅ | ✅ | ✅ |
| 7. Resolução de país/medalhas (Personnel) | Alto | ✅ | ✅ | ⚪ | ✅ |
| 8. Repositório batch anti N+1 (`load_many/resolve_many`) | Médio | ✅ | ✅ | ⚪ | ✅ |
| 9. Observabilidade e orçamento de UX | Médio | ✅ | ✅ | ⚪ | ✅ |
| 10. Registro de conteúdo e plugins | Médio | ✅ | ✅ | ⚪ | ✅ |

> Legenda: ✅ obrigatório no pipeline; ⚪ opcional/futuro.

## Top 10 fluxos priorizados para release

1. Startup + splash + áudio.
2. Seleção de diretório PWCG e campanhas.
3. Sincronização de dados de campanha.
4. Parsing de relatórios e missão.
5. Abertura/uso das abas Missões/Esquadrão/Perfil/Medalhas.
6. Atalhos de teclado críticos.
7. Ordem de foco e labels acessíveis.
8. Feedback de erro acionável e toast.
9. Resolução de Personnel com batch I/O.
10. Emissão de métricas de observabilidade/UX budget.

## Smoke de release (rápido)

Comandos mínimos para gate de release (execução < 2 min em ambiente padrão):

```bash
pytest -q \
  tests/test_startup_splash_contract.py \
  tests/test_sync_ui_contract.py \
  tests/test_accessibility_contract.py \
  tests/test_ctrl_f_shortcut_contract.py \
  tests/test_notification_contract.py \
  tests/test_personnel_resolution_service.py \
  tests/test_batch_repository.py \
  tests/test_campaign_repository_ports.py \
  tests/test_observability.py \
  tests/test_ui_performance_budget_contract.py
```

## Política de falha rápida para testes instáveis (quarentena)

- Teste marcado como instável deve sair do gate principal e entrar em **quarentena** com etiqueta `@quarantine`.
- **SLA de correção:** até 5 dias úteis para remover da quarentena.
- O gate de release falha se:
  - quantidade de testes em quarentena aumentar sem justificativa; ou
  - houver teste em quarentena com SLA vencido.
- Cada item em quarentena deve registrar:
  - motivo técnico,
  - responsável,
  - data de entrada,
  - prazo de saída.
