from wingmate.infrastructure.config.app_settings import AppSettings


class ConfigLoader:
    def load(self) -> AppSettings:
        return AppSettings()
