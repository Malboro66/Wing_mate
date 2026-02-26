# Otimização de acesso a dados (anti N+1 de arquivos)

## Jornadas críticas mapeadas

- Resolução de país/medalhas por piloto em `Personnel` (varredura de múltiplos JSON).
- Agregação de relatórios e metadados em campanhas com muitos arquivos.

## Estratégia adotada

- Camada de repositório bulk-first: `JsonBatchRepository`.
  - `load_many(paths)`: pré-carrega em lote com cache do parser.
  - `resolve_many(payloads, resolver)`: resolve itens de negócio a partir de dados já carregados.
- Serviço `PersonnelResolutionService` migrou para leitura em batch.
- API de parser `get_json_many(...)` para padronizar pré-carregamento.

## Benchmark sintético

- Função: `benchmark_personnel_io_scenario(...)` em `app/application/io_benchmark.py`.
- Compara estratégia naive (instância por arquivo) versus batch por cenário.
- Métrica principal: `gain_pct`.

## Próximos passos

- Integrar cache + invalidação por diretório/campanha para consistência pós-batch.
- Promover benchmark para job dedicado de performance no CI.
