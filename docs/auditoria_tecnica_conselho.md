# Auditoria Técnica — Conselho Sênior (Backend, Frontend, DevOps, QA)

## Suposições técnicas adotadas

- A aplicação é desktop em Python com PyQt5, sem backend web exposto diretamente, e com forte uso de leitura de arquivos locais JSON para processamento de dados.
- Não há pipeline CI/CD formal versionado no repositório (ex.: GitHub Actions), apesar de existir suíte de testes em `tests/`.
- Não foram fornecidas métricas operacionais (latência, erro, build time, cobertura), portanto as recomendações priorizam redução de risco e instrumentação para medição.
- O contexto de negócio envolve uso recorrente por analistas/simuladores, com necessidade de confiabilidade local, baixa latência percebida e rastreabilidade de falhas.

## Risco crítico identificado (prioridade máxima)

### Vazamento de dados sensíveis em logs e tratamento de erros

Sem política explícita de classificação/mascaramento de dados em logs e exceções, há risco de exposição acidental de paths locais, conteúdos de arquivos ou metadados de usuário (OWASP A09/A01 em contexto desktop).

---

## 1. PADRONIZAÇÃO DE FRONTEIRAS DE MÓDULOS (HEXAGONAL LIGHT)

- **CATEGORIA:** Arquitetura de Código
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Mistura potencial entre lógica de domínio, parsing e preocupações de UI em pontos de integração, o que aumenta acoplamento e regressões.
- **CAUSA RAIZ:** Evolução orgânica da base com múltiplas telas e serviços sem enforcement arquitetural automatizado.
- **RECOMENDAÇÃO:**
  - Definir contratos explícitos entre camadas (`core`, `application`, `ui`) para os 5 fluxos mais críticos.
  - Introduzir testes de contrato de fronteira (entrada/saída) para serviços de aplicação.
  - Adicionar regra de lint arquitetural (import-linter ou script custom) bloqueando imports cruzados indevidos.
- **DEPENDÊNCIAS:** Nenhuma.
- **IMPACTO ESPERADO:** Redução de regressões por acoplamento e manutenção mais previsível em até 30-40% nos módulos críticos.
- **ESFORÇO:** Médio | **PRIORIDADE:** Alta

## 2. POLÍTICA DE LOGGING SEGURO E REDAÇÃO DE DADOS

- **CATEGORIA:** Segurança de Dados
- **RISCO:** 🔴 Crítico
- **PROBLEMA IDENTIFICADO:** Erros e logs podem expor dados operacionais sensíveis (paths, payloads, identificadores), ampliando superfície de vazamento.
- **CAUSA RAIZ:** Ausência de taxonomia de dados sensíveis e middleware/filtro central de redaction.
- **RECOMENDAÇÃO:**
  - Criar política de classificação (P0 sensível, P1 interno, P2 público) e guia de logging.
  - Implementar formatter/filtro central para mascarar campos sensíveis antes da persistência.
  - Revisar handlers de exceção para mensagens seguras ao usuário e detalhe técnico apenas em log protegido.
  - Adicionar testes unitários de não vazamento para casos de erro.
- **DEPENDÊNCIAS:** Depende do item 1 — padronização de pontos de entrada para aplicar filtro de forma consistente.
- **IMPACTO ESPERADO:** Mitigação direta de risco de exposição acidental e aderência a OWASP A09 (Security Logging and Monitoring Failures).
- **ESFORÇO:** Pequeno | **PRIORIDADE:** Alta

## 3. HARDENING DE ENTRADA DE ARQUIVOS E VALIDAÇÃO ESTRITA

- **CATEGORIA:** Segurança de Dados
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Carga de arquivos locais pode aceitar formatos/campos inesperados, causando falhas, corrupção lógica ou parsing inseguro.
- **CAUSA RAIZ:** Validação estrutural parcial sem schema versionado e fail-fast uniforme.
- **RECOMENDAÇÃO:**
  - Definir schemas versionados (ex.: `pydantic`/`jsonschema`) para os principais formatos de entrada.
  - Validar tamanho, encoding e estrutura antes do processamento completo.
  - Introduzir quarentena de arquivos inválidos com feedback acionável no UI.
- **DEPENDÊNCIAS:** Nenhuma.
- **IMPACTO ESPERADO:** Redução de falhas por entrada malformada e menor risco de indisponibilidade por dados inesperados.
- **ESFORÇO:** Médio | **PRIORIDADE:** Alta

## 4. ORÇAMENTO DE PERFORMANCE DE UI (STARTUP E INTERAÇÃO)

- **CATEGORIA:** Experiência do Usuário
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Sem orçamento de performance, o tempo de startup e resposta das telas tende a degradar sem visibilidade.
- **CAUSA RAIZ:** Ausência de metas objetivas (ex.: TTI desktop, tempo de troca de aba, render de listas pesadas).
- **RECOMENDAÇÃO:**
  - Definir SLOs de UX: startup < 2,5s (máquina de referência), troca de aba < 200ms, ações críticas < 500ms.
  - Instrumentar cronômetros de UI (telemetria local) e painéis de tendência por release.
  - Aplicar lazy-loading e virtualização para listas/tabelas densas.
- **DEPENDÊNCIAS:** Depende do item 8 — observabilidade para coleta consistente das métricas.
- **IMPACTO ESPERADO:** Melhoria perceptível de fluidez e prevenção de regressão de UX nas próximas releases.
- **ESFORÇO:** Médio | **PRIORIDADE:** Alta

## 5. ACESSIBILIDADE OPERACIONAL E CONSISTÊNCIA DE INTERAÇÕES

- **CATEGORIA:** Experiência do Usuário
- **RISCO:** 🟡 Médio
- **PROBLEMA IDENTIFICADO:** Sem checklist de acessibilidade, atalhos de teclado, foco e contraste podem variar entre telas.
- **CAUSA RAIZ:** Crescimento de componentes sem critérios mínimos de acessibilidade automatizados.
- **RECOMENDAÇÃO:**
  - Criar checklist obrigatório de acessibilidade desktop (navegação por teclado, ordem de foco, contraste, labels).
  - Adicionar testes de contrato de atalhos e foco para telas críticas.
  - Padronizar componentes de feedback (erro/sucesso/loading) com tokens de design.
- **DEPENDÊNCIAS:** Depende do item 1 — contratos de interface facilitam padronização transversal.
- **IMPACTO ESPERADO:** Menor curva de aprendizado, menos erros operacionais e melhor usabilidade para usuários intensivos.
- **ESFORÇO:** Pequeno | **PRIORIDADE:** Média

## 6. ESTRATÉGIA DE CACHE COM INVALIDAÇÃO EXPLÍCITA

- **CATEGORIA:** Eficiência de Consultas
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Cache local sem política clara de invalidação pode produzir dados stale ou recomputação excessiva.
- **CAUSA RAIZ:** Caches por instância sem contrato de ciclo de vida por contexto de tela/arquivo.
- **RECOMENDAÇÃO:**
  - Catalogar pontos de cache existentes e classificar por tipo (quente, morno, efêmero).
  - Definir chaves/TTL e gatilhos de invalidação por evento (mudança de arquivo, troca de campanha, refresh manual).
  - Medir hit rate e custo de recomputação para ajustar granularidade.
- **DEPENDÊNCIAS:** Depende do item 8 — métricas de observabilidade para hit/miss.
- **IMPACTO ESPERADO:** Redução de latência percebida e menor uso de CPU/I/O em fluxos repetitivos.
- **ESFORÇO:** Médio | **PRIORIDADE:** Alta

## 7. OTIMIZAÇÃO DE ACESSO A DADOS (ANTI N+1 DE ARQUIVOS)

- **CATEGORIA:** Eficiência de Consultas
- **RISCO:** 🟡 Médio
- **PROBLEMA IDENTIFICADO:** Leituras repetidas de múltiplos arquivos/recursos em sequência podem gerar padrão análogo a N+1 e aumentar I/O.
- **CAUSA RAIZ:** Falta de planejamento de pré-carregamento por lote para cenários de agregação.
- **RECOMENDAÇÃO:**
  - Mapear jornadas com maior volume de leitura e consolidar carregamento em batch.
  - Criar camada de repositório com APIs bulk-first (`load_many`, `resolve_many`).
  - Introduzir benchmark sintético de I/O por cenário crítico.
- **DEPENDÊNCIAS:** Depende do item 6 — cache e invalidação para manter consistência após batch.
- **IMPACTO ESPERADO:** Queda de 20-40% no tempo de processamento em fluxos de agregação.
- **ESFORÇO:** Médio | **PRIORIDADE:** Média

## 8. OBSERVABILIDADE PADRÃO (MÉTRICAS, TRACES E EVENTOS)

- **CATEGORIA:** Pipelines de CI/CD
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Sem baseline de telemetria, decisões de melhoria e troubleshooting ficam reativos.
- **CAUSA RAIZ:** Instrumentação parcial sem padrão de eventos técnicos e de negócio.
- **RECOMENDAÇÃO:**
  - Definir catálogo mínimo: startup_time_ms, action_duration_ms, error_rate, cache_hit_rate.
  - Padronizar correlação por `session_id` para facilitar diagnóstico de ponta a ponta.
  - Publicar relatório automático por release com comparação vs baseline.
- **DEPENDÊNCIAS:** Nenhuma.
- **IMPACTO ESPERADO:** MTTR menor e priorização orientada a dados já no próximo ciclo de entrega.
- **ESFORÇO:** Pequeno | **PRIORIDADE:** Alta

## 9. PIPELINE CI COM GATES DE QUALIDADE E TESTE DE REGRESSÃO

- **CATEGORIA:** Pipelines de CI/CD
- **RISCO:** 🟠 Alto
- **PROBLEMA IDENTIFICADO:** Ausência de pipeline versionado reduz confiabilidade de merge e aumenta risco de regressões silenciosas.
- **CAUSA RAIZ:** Execução manual de testes e checks sem gates obrigatórios.
- **RECOMENDAÇÃO:**
  - Criar pipeline CI (lint, type-check, testes unitários, testes de contrato) com execução em PR.
  - Definir thresholds iniciais: cobertura mínima por pacote crítico, bloqueio em falhas de contrato.
  - Habilitar cache de dependências e paralelismo para manter tempo total < 10 minutos.
- **DEPENDÊNCIAS:** Depende do item 8 — métricas para trend de estabilidade e tempo de build.
- **IMPACTO ESPERADO:** Redução de incidentes pós-merge e ciclo de feedback mais curto para equipe.
- **ESFORÇO:** Médio | **PRIORIDADE:** Alta

## 10. SHIFT-LEFT COM MATRIZ DE TESTES POR RISCO

- **CATEGORIA:** Pipelines de CI/CD
- **RISCO:** 🟡 Médio
- **PROBLEMA IDENTIFICADO:** Suíte pode estar desbalanceada (muitos testes de baixo risco, poucos cenários críticos de integração/contrato).
- **CAUSA RAIZ:** Crescimento incremental sem matriz explícita de cobertura por criticidade de fluxo.
- **RECOMENDAÇÃO:**
  - Criar matriz risco × tipo de teste (unitário, contrato, integração UI, regressão).
  - Priorizar os 10 fluxos de maior impacto e automatizar smoke de release.
  - Adotar política de falha rápida para testes instáveis (quarentena com SLA de correção).
- **DEPENDÊNCIAS:** Depende do item 9 — pipeline para execução contínua.
- **IMPACTO ESPERADO:** Aumento da confiança de release com menor custo de retrabalho em produção.
- **ESFORÇO:** Pequeno | **PRIORIDADE:** Média

## Ordem sugerida de execução (2–3 sprints)

- **Sprint 1:** itens 2, 8, 9 (segurança crítica + base de observabilidade + gates CI).
- **Sprint 2:** itens 1, 3, 6 (arquitetura, validação de entrada, cache robusto).
- **Sprint 3:** itens 4, 5, 7, 10 (UX, acessibilidade, otimização de I/O e maturidade de testes).
