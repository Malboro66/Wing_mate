# Modularização de Conteúdo (plugins)

Este documento formaliza um modelo de módulos de conteúdo para reduzir acoplamento ao filesystem fixo (`assets/medals`, `assets/squadrons`, `assets/ranks`) e abrir caminho para extensibilidade.

## Objetivo

- Permitir conteúdo versionado por módulo (medalhas/esquadrões/patentes/campanhas).
- Habilitar carregamento de pacotes externos sem alterar código da UI.
- Padronizar descoberta de conteúdo por manifest.

## Estrutura proposta

- Registro central: `ContentModuleRegistry` (`app/application/content_module_registry.py`)
- Módulos built-in:
  - `medals`
  - `squadrons`
  - `ranks`
- Diretório opcional para plugins: `app/assets/modules/<plugin>/module.json`

## Exemplo de `module.json`

```json
{
  "id": "ww1_pack",
  "name": "WW1 Pack",
  "category": "medals",
  "path": "content",
  "version": "1.1.0",
  "enabled": true
}
```

## Regras mínimas de validação

Campos obrigatórios:
- `id`
- `name`
- `category`
- `path`

Campos opcionais:
- `version` (default `1.0.0`)
- `enabled` (default `true`)

## Integração gradual

1. UI/serviços passam a resolver caminhos via `registry.resolve(module_id, ...)`.
2. Módulos built-in continuam funcionando (compatibilidade).
3. Plugins externos podem sobrescrever/expandir conteúdo sem editar código.

