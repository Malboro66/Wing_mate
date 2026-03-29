from pathlib import Path


class AssetManager:
    def __init__(self, assets_root: Path) -> None:
        self.assets_root = assets_root

    def path(self, *parts: str) -> Path:
        return self.assets_root.joinpath(*parts)
