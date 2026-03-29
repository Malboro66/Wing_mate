from pathlib import Path
from typing import List


class SplashLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def list(self) -> List[Path]:
        splash_dir = self.root / "splash"
        if not splash_dir.exists():
            return []
        return [p for p in splash_dir.iterdir() if p.is_file()]
