<div align="center">
  <h1>🪶 Wing Mate</h1>
  <p>
    <em>A central hub for deep analytics and enriched insights on IL-2 flight campaigns & squadrons.</em>
  </p>
  <p>
    <img alt="PyPI - Python Version" src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python">
    <img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/SEU_REPO/wingmate/ci.yml?branch=main&label=Tests&logo=github">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg">
    <img alt="Contributions Welcome" src="https://img.shields.io/badge/contributions-welcome-brightgreen">
  </p>
</div>

> 💡 **Wing Mate** revoluciona o modo como entusiastas e squads do IL-2 analisam campanhas, mergulhando profundamente em dados, observabilidade e produtividade – com uma UX desktop nativa e robusta.

---

## ✨ Principais Funcionalidades

- 📊 **Analítica de Campanhas**: Visualize, filtre e compare campanhas IL-2.
- 👥 **Gestão de Esquadrões**: Detalhamento completo dos membros e desempenho do esquadrão.
- 🔍 **Enriquecimento & Insights**: Geração de relatórios, visão de eventos e métricas avançadas.
- 🟢 **Observabilidade Integrada**: Logs estruturados, notificações e diagnósticos.
- ♿ **Acessibilidade**: Atalhos, feedback visual e navegação ágil.
- 🔒 **Arquitetura Modular**: Pronto para extensões e integrações.

---

## 🧰 Stack Tecnológica

| 🚀 Tecnologia         | Descrição                |
|----------------------|-------------------------|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="22"/> **Python 3.8+** | Linguagem principal |
| <img src="https://upload.wikimedia.org/wikipedia/commons/6/6a/PyQt_logo.svg" width="22"/> **PyQt5**               | GUI Moderno        |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytest/pytest-original.svg" width="22"/> **Pytest** | Testes Automatizados|
| 🗃️ **Logging Estruturado** | Observabilidade        |

---

## 🌳 Estrutura Sugerida de Diretórios

```text
wingmate/
├── app/
│   ├── ui/
│   └── ...
├── utils/
├── tests/
├── logs/
├── main_app.py
├── requirements.txt
└── README.md
```

---

## 🚀 Guia de Instalação Rápida

> Siga o checklist para experimentar o "Hello World" do Wing Mate em minutos:

- [x] **Clone o repositório**
    ```bash
    git clone https://github.com/SEU_USUARIO/wingmate.git
    cd wingmate
    ```
- [x] **Crie e ative o ambiente Python**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # (Linux/macOS)
    .venv\Scripts\activate     # (Windows)
    ```
- [x] **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```
- [x] **Execute o aplicativo**
    ```bash
    python main_app.py
    ```
    <details>
      <summary><b>Exemplo de código: Inicialização da aplicação</b></summary>

    ```python
    from PyQt5.QtWidgets import QApplication
    from app.ui.simulator_selection_main_window import MainWindow

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
    ```
    </details>

---

## 🧪 Testes & Smoke Gates

### Executando testes unitários
```bash
pytest tests/test_error_feedback.py tests/test_observability.py
```

### Smoke de Release (Shift-Left)
Para garantir contratos essenciais antes de releases:
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

---

## 🤝 Como Contribuir

> "Colaborar faz o open source girar! ✨"

- Faça um fork do projeto
- Crie um branch com sua feature: `git checkout -b feature/minha-novidade`
- Realize commits claros e objetivos
- Mantenha os testes passando (`pytest`)
- Abra um Pull Request — sugestões, melhorias e dúvidas são bem-vindas!

Checklist de Pull Request:
- [ ] Funcionalidade documentada
- [ ] Testes automatizados criados ou atualizados
- [ ] Build e linter rodaram sem falhas

---

## 📝 Licença

Distribuído sob a Licença MIT. Consulte [`LICENSE`](./LICENSE) para mais.

---

## 🏆 Créditos

Desenvolvido com ❤️ por [Equipe Wing Mate](https://github.com/SEU_USUARIO/wingmate/graphs/contributors).

Agradecimentos: IL-2 modding community, maintainers PyQt, open source testers.

> _"Seu feedback e contribuição são fundamentais. Bem-vindo ao esquadrão Wing Mate!"_