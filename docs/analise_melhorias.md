# Análise técnica do estado atual do Wing Mate

## 1) Lista de melhorias de Back-end

1. **Extrair regras de negócio da camada de UI para serviços de domínio**  
   Hoje há parsing, transformação e persistência acontecendo dentro de componentes visuais (tabs). Isso dificulta testes unitários, versionamento das regras e reuso. Criar serviços como `SquadronEnrichmentService`, `ProfileService` e `MedalsService` reduziria acoplamento e deixaria o código mais previsível.

2. **Padronizar I/O de arquivos com utilitários de escrita/leitura segura em toda a aplicação**  
   Já existe `atomic_write` e `safe_read_json` em `utils/file_operations.py`, mas boa parte do código ainda usa `open(...)` diretamente em múltiplos módulos. Consolidar tudo em uma API única de I/O reduziria risco de corrupção e inconsistência de tratamento de erro.

3. **Introduzir validação de esquema para JSONs de entrada e saída**  
   O sistema processa muitos JSONs externos do PWCG e também gera metadados internos sem schema explícito. Adotar validação (ex.: Pydantic/dataclasses + validação) evitaria falhas silenciosas e melhoraria mensagens para o usuário.

4. **Corrigir e endurecer o tratamento de exceções em serialização JSON**  
   Há captura de `json.JSONEncodeError`, exceção que não existe no módulo `json` padrão do Python. O correto é capturar `TypeError`/`ValueError` (ou `OSError` para I/O). Esse tipo de erro hoje pode mascarar falhas reais de gravação.

5. **Aumentar cobertura de testes automáticos para core e utilitários**  
   A suíte atual está concentrada em UI (`test_profile_tab`) e depende de plugin externo. Falta cobertura para parser/processor, que concentram regras críticas de dados.

---

## 2) Lista de melhorias de Front-end (PyQt)

1. **Aplicar design system de componentes e estilos**  
   Existem estilos e comportamentos espalhados entre abas (labels, botões, grupos, tabelas). Centralizar tokens visuais e widgets base melhora consistência visual e reduz retrabalho.

2. **Melhorar feedback de erro orientado ao usuário**  
   Hoje muitas falhas aparecem apenas como mensagens genéricas em `QMessageBox`. É recomendável exibir contexto acionável (arquivo, ação sugerida, botão de “detalhes técnicos”, copiar erro).

3. **Fortalecer responsividade e acessibilidade de telas densas**  
   Algumas telas usam muitas informações em tabelas/painéis. Melhorias como ordenação explícita, filtros rápidos, tooltips, navegação por teclado e contraste configurável aumentam usabilidade.

4. **Criar estados visuais padronizados (loading/empty/error/success)**  
   A aplicação já tem progress bar e estado busy no fluxo principal, mas isso pode ser expandido para cada aba com placeholders consistentes, evitando “tela vazia” sem contexto.

5. **Separar ViewModel das widgets complexas**  
   Tabs como perfil, missões e esquadrões podem ganhar classes intermediárias (ViewModel/Presenter) para reduzir lógica no widget e facilitar testes de comportamento sem UI real.

---

## 3) Lista de melhorias de Arquitetura

1. **Definir arquitetura por camadas (UI → Application → Domain → Infrastructure)**  
   Atualmente existe um começo de separação (`core/`, `ui/`, `utils/`), mas ainda com cruzamento de responsabilidades. Formalizar camadas e contratos deixa evolução mais segura.

2. **Criar interfaces explícitas para repositórios e serviços**  
   Já há um `CampaignRepository`, porém ainda minimalista. Evoluir para interfaces/portas e implementações concretas facilita mocks, testes e futuras integrações (ex.: outras fontes além de JSON local).

3. **Introduzir container simples de dependências (DI manual)**  
   Construir parser/processor/repositories em um ponto central de bootstrap evita instanciação dispersa nas views e melhora previsibilidade de ciclo de vida.

4. **Adotar observabilidade mínima estruturada**  
   Existe `StructuredLogger`, mas sem padronização global de eventos/chaves. Definir eventos de domínio (sync_started, sync_failed, profile_saved etc.) permitiria diagnóstico mais rápido em produção.

5. **Planejar modularização para plugins de conteúdo**  
   Como o app manipula muitos assets por país/campanha, um modelo de “módulos de conteúdo” (medalhas/esquadrões/ranks) reduziria acoplamento com filesystem fixo e abriria caminho para extensibilidade.

---

## 4) Lista de melhorias de Segurança

1. **Sanitizar e restringir caminhos de arquivos selecionados pelo usuário**  
   A aplicação lê e grava arquivos em paths vindos de `QFileDialog` e de dados externos; é importante validar extensão real, tamanho e canonical path para evitar abuso de path traversal/symlink.

2. **Implementar política de permissões e diretórios permitidos**  
   Definir quais diretórios podem ser lidos/escritos por tipo de operação (importação, exportação, cache, logs) reduz risco de gravação acidental em áreas sensíveis.

3. **Reduzir exposição de dados sensíveis em logs**  
   O logging atual inclui paths e detalhes de erro. É recomendável mascarar informações potencialmente sensíveis e separar nível técnico para modo debug.

4. **Assinatura/validação de integridade para metadados críticos**  
   JSONs de assets/meta podem ser adulterados externamente. Checksums simples (ou hash versionado) ajudam a detectar corrupção e manipulação indevida.

5. **Fortalecer estratégia de tratamento de falhas “secure-by-default”**  
   Em leituras inválidas, hoje frequentemente há fallback silencioso. Em fluxos críticos, preferir bloqueio com mensagem clara em vez de continuar com dados parcialmente confiáveis.

---

## Prioridade sugerida (90 dias)

- **Sprint 1 (rápido impacto):** corrigir exceções JSON incorretas, padronizar I/O seguro e melhorar mensagens de erro.
- **Sprint 2 (qualidade):** refatorar lógica de negócio para serviços + testes unitários em `core`.
- **Sprint 3 (estrutura):** definir camadas formais, contratos de repositório e observabilidade padronizada.
- **Sprint 4 (hardening):** validação de paths, política de diretórios e estratégia de integridade de metadados.
