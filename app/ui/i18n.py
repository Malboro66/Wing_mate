from __future__ import annotations

from typing import Dict


class AppI18n:
    """Camada simples de i18n para strings de alto nível da MainWindow."""

    PT_BR = "pt_BR"
    EN_US = "en_US"

    LANG_LABELS: Dict[str, str] = {
        PT_BR: "Português",
        EN_US: "English",
    }

    _T: Dict[str, Dict[str, str]] = {
        "window_title": {
            PT_BR: "Wing Mate",
            EN_US: "Wing Mate",
        },
        "toolbar_actions": {
            PT_BR: "Ações",
            EN_US: "Actions",
        },
        "select_folder": {
            PT_BR: "Selecionar Pasta PWCGFC",
            EN_US: "Select PWCGFC Folder",
        },
        "sync_data": {
            PT_BR: "Sincronizar Dados",
            EN_US: "Sync Data",
        },
        "copy_path_action": {
            PT_BR: "Copiar caminho",
            EN_US: "Copy path",
        },
        "no_path_selected": {
            PT_BR: "Nenhum caminho selecionado",
            EN_US: "No path selected",
        },
        "copy_button": {
            PT_BR: "Copiar",
            EN_US: "Copy",
        },
        "copy_button_tooltip": {
            PT_BR: "Copiar caminho do PWCGFC",
            EN_US: "Copy PWCGFC path",
        },
        "campaign_label": {
            PT_BR: "Campanha:",
            EN_US: "Campaign:",
        },
        "language_label": {
            PT_BR: "Idioma:",
            EN_US: "Language:",
        },
        "profile_tab": {
            PT_BR: "Perfil do Piloto",
            EN_US: "Pilot Profile",
        },
        "missions_tab": {
            PT_BR: "Missões",
            EN_US: "Missions",
        },
        "squadron_tab": {
            PT_BR: "Esquadrão",
            EN_US: "Squadron",
        },
        "aces_tab": {
            PT_BR: "Ases",
            EN_US: "Aces",
        },
        "medals_tab": {
            PT_BR: "Medalhas",
            EN_US: "Medals",
        },
        "insert_squads_tab": {
            PT_BR: "Insert Squads",
            EN_US: "Insert Squads",
        },
        "input_medals_tab": {
            PT_BR: "Input Medals",
            EN_US: "Input Medals",
        },
        "select_folder_warning": {
            PT_BR: "Selecione a pasta PWCGFC e uma campanha.",
            EN_US: "Select PWCGFC folder and a campaign.",
        },
        "sync_in_progress": {
            PT_BR: "Sincronização já em andamento...",
            EN_US: "Sync already in progress...",
        },
        "campaigns_loaded": {
            PT_BR: "{count} campanhas carregadas.",
            EN_US: "{count} campaigns loaded.",
        },
        "copy_path_empty": {
            PT_BR: "Nenhum caminho para copiar.",
            EN_US: "No path to copy.",
        },
        "copy_path_success": {
            PT_BR: "Caminho copiado para a área de transferência.",
            EN_US: "Path copied to clipboard.",
        },
        "sync_success": {
            PT_BR: "Dados carregados com sucesso.",
            EN_US: "Data loaded successfully.",
        },
        "sync_failed": {
            PT_BR: "Falha ao sincronizar dados.",
            EN_US: "Failed to sync data.",
        },
        "folder_dialog_title": {
            PT_BR: "Selecionar Pasta PWCGFC",
            EN_US: "Select PWCGFC Folder",
        },
        "path_prefix": {
            PT_BR: "Caminho:",
            EN_US: "Path:",
        },
    }

    @classmethod
    def t(cls, key: str, lang: str, **kwargs: str) -> str:
        lang_dict = cls._T.get(key, {})
        text = lang_dict.get(lang) or lang_dict.get(cls.PT_BR) or key
        if kwargs:
            return text.format(**kwargs)
        return text
