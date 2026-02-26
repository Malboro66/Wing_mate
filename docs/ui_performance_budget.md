# Orçamento de Performance de UI (Startup e Interação)

## SLOs de UX (máquina de referência)

- **startup**: `< 2.5s` (`startup_time_ms <= 2500`).
- **troca de aba**: `< 200ms` (pior caso observado `max_tab_switch_ms <= 200`).
- **ações críticas**: `< 500ms` (`action_duration_ms <= 500`).

## Instrumentação aplicada

- `utils/observability.py`
  - catálogo mínimo de métricas: `startup_time_ms`, `action_duration_ms`, `error_rate`, `cache_hit_rate`, `max_tab_switch_ms`;
  - avaliação de orçamento de UX via `evaluate_ux_budget`;
  - correlação por `session_id` em todos os eventos;
  - relatório por release com `ux_budget` + `baseline_delta`.

- `main_app.py`
  - mede startup real da aplicação e registra `startup_completed`;
  - publica relatório automático em `logs/observability/observability_<release>.json`;
  - atualiza `logs/observability/baseline.json` para tendência por release.

- `app/ui/main_window.py`
  - mede tempo de troca de aba com `record_action_duration("tab_switch:...")`;
  - lazy-loading da aba de medalhas para reduzir custo de navegação (`_medals_dirty`, `_medals_loaded_once`).

- `app/ui/medals_tab.py`
  - atualização de contexto em chamada única (`set_context`) para evitar reload duplicado.
  - renderização em bateladas da grade (`QListView.Batched`) e `uniformItemSizes` para listas densas.

## Uso em CI/CD

- Consumir `ux_budget` e `baseline_delta` como gate opcional em pipeline.
- Exemplo: bloquear release se `tab_switch_within_slo == false` ou `startup_time_ms` piorar acima de limite acordado.
