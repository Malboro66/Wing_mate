from pathlib import Path


class IconLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, name: str) -> Path:
        return self.root / "icons" / name
