# Build Scripts (PyInstaller)

Este diretório contém automação para gerar executáveis standalone para distribuição (ex.: GitHub Releases).

## Requisitos

```bash
pip install .[build]
```

## Gerar executável

```bash
python build_scripts/build_with_pyinstaller.py
```

Saída esperada:
- `dist/WingMate.exe` (Windows, `--onefile`)
- `dist/WingMate` (Linux/macOS, `--onefile`)

## Opções úteis

```bash
python build_scripts/build_with_pyinstaller.py --no-onefile
python build_scripts/build_with_pyinstaller.py --no-clean
```

## Observações

- O script inclui `app/assets` no bundle do executável.
- Para release no GitHub, anexe o artefato gerado em `dist/`.
