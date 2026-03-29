from dataclasses import dataclass


@dataclass
class AppSettings:
    language: str = "pt_BR"
    theme: str = "dark"
