# Wing Mate

Wing Mate é uma aplicação desktop (PyQt5) para explorar dados de campanhas e esquadrões do IL-2,
com foco em análise, enriquecimento de dados e observabilidade básica.

## Como executar

1. Crie e ative um ambiente virtual Python.
2. Instale as dependências do projeto.
3. Inicie a aplicação:

```bash
python main_app.py
```

## Testes

Para executar testes unitários selecionados:

```bash
pytest tests/test_error_feedback.py tests/test_observability.py
```


## Smoke de release (shift-left)

Para um gate rápido dos fluxos críticos:

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
