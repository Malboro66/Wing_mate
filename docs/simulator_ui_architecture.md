# Estrutura inicial de UI para seleção de simuladores

## Estrutura sugerida

- `main.py`: ponto de entrada do fluxo de seleção (novo shell de navegação).
- `app/application/app_config.py`: persistência e validação de caminhos obrigatórios.
- `app/ui/simulator_selection_main_window.py`: janela raiz com `QStackedWidget` e navegação.
- `app/ui/era_selection_widget.py`: seleção de era (WW1/WW2) com trava de configuração.
- `app/ui/ww1_simulator_selection_widget.py`: seleção de simuladores da WW1.
- `app/ui/future_feature_widget.py`: placeholder de funcionalidades futuras.
- `app/ui/settings_widget.py`: configuração de caminhos e validação imediata.
- `app/ui/i18n.py`: catálogo de textos traduzíveis PT/EN.

## Fluxo

1. Usuário abre a aplicação (`main.py`) e entra na tela de seleção de era.
2. Botão de engrenagem (global) abre `SettingsWidget`.
3. Após caminhos válidos, `AppConfig` libera botão da era correspondente.
4. Na WW1, somente `IL2- Flying Circus (PWCG)` navega para a UI principal (`app/ui/main_window.py`).
5. Demais opções navegam para `FutureFeatureWidget`.

## Regras de trava

- `WW1`: exige caminhos válidos para `IL2-FC`, `RoF` e `PWCG`.
- `WW2`: placeholder, permanece desabilitado no momento.

## Feedback

- Status visual por campo (`Válido`/`Inválido`) em `SettingsWidget`.
- Toast via `notification_bus` para caminhos inválidos e confirmação de salvar.
- Aviso na `EraSelectionWidget` quando não há configuração mínima.
