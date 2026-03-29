from pathlib import Path


class MissionLogSource:
    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")
