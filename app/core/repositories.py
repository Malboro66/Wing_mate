# core/repositories.py
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from .data_parser import IL2DataParser

@dataclass
class Campaign:
    name: str
    player_serial: str
    squadron_name: str
    reference_date: Optional[str] = None

class CampaignRepository:
    def __init__(self, parser: IL2DataParser):
        self._parser = parser
    
    def get_campaign(self, name: str) -> Optional[Campaign]:
        raw = self._parser.get_campaign_info(name)
        if not raw:
            return None
        return Campaign(
            name=name,
            player_serial=str(raw.get('referencePlayerSerialNumber', '')),
            squadron_name=raw.get('referencePlayerSquadronName', 'N/A'),
            reference_date=raw.get('campaignDate')
        )
    
    def get_missions(self, campaign_name: str, serial: str) -> List[Dict[str, Any]]:
        return self._parser.get_combat_reports(campaign_name, serial)
