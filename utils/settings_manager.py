# utils/settings_manager.py
from PyQt5.QtCore import QSettings

class SettingsManager:
    _instance = None
    _settings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        return cls._instance
    
    def get(self, key: str, default=None):
        return self._settings.value(key, default)
    
    def set(self, key: str, value) -> None:
        self._settings.setValue(key, value)
        self._settings.sync()

# Uso global
settings = SettingsManager()
