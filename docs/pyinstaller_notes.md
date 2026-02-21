# PyInstaller notes (Wing Mate)

## Atualização de `.spec`

Após introduzir ícones SVG de status e novos widgets de UI, garanta no arquivo `.spec`:

- Inclusão dos SVGs de `app/assets/icons/status_*.svg` em `datas`.
- Inclusão do pacote `app.ui` completo (ou módulos explícitos `toast_widget`, `skeleton_widget`, `shortcut_mixin`) quando usar coleta manual.

Exemplo (trecho):

```python
datas=[
    ('app/assets/icons/status_active.svg', 'app/assets/icons'),
    ('app/assets/icons/status_wounded.svg', 'app/assets/icons'),
    ('app/assets/icons/status_mia.svg', 'app/assets/icons'),
    ('app/assets/icons/status_kia.svg', 'app/assets/icons'),
    ('app/assets/icons/status_pow.svg', 'app/assets/icons'),
    ('app/assets/icons/status_hospital.svg', 'app/assets/icons'),
    ('app/assets/icons/status_leave.svg', 'app/assets/icons'),
]
```

## Regressão visual recomendada após mudança de tema

Após qualquer mudança de stylesheet global, validar manualmente:

- `QMessageBox`
- `QFileDialog`
- `QComboBox`
- `QTableWidget` (abas principais)

Porque widgets nativos do Qt podem reagir de forma diferente entre Windows/Linux/macOS.
