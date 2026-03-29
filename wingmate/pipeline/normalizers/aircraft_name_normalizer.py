class AircraftNameNormalizer:
    def normalize(self, name: str) -> str:
        return " ".join((name or "").split()).strip()
