# Arquitetura por Camadas (formalização)

## Camadas

1. **UI (`app/ui`)**
   - Responsável por widgets, interação do usuário e feedback visual.
   - Não deve conter regra de negócio ou regras de persistência.

2. **Application (`app/application`)**
   - Orquestra casos de uso entre UI e domínio.
   - Define portas/contratos para desacoplar dependências.

3. **Domain (`app/core`)**
   - Regras de negócio, validações e transformação de dados.
   - Serviços de domínio e entidades de validação.

4. **Infrastructure (`utils` e filesystem externo)**
   - Implementações técnicas de I/O, serialização e utilitários.
   - Ex.: `atomic_json_write`, `safe_read_json`.

## Regras de dependência

- UI pode depender de Application.
- Application pode depender de Domain (via portas/contratos).
- Domain pode depender de Infrastructure utilitária.
- Camadas inferiores **não** dependem de UI.

## Estado atual aplicado

- `InsertSquadsTab` (UI) agora usa `SquadronEnrichmentApplicationService` (Application).
- `SquadronEnrichmentApplicationService` depende de `SquadronEnrichmentDomainPort`.
- `SquadronEnrichmentService` implementa a regra de domínio e validação de schema.
