from pathlib import Path


class CampaignFileSource:
    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")
