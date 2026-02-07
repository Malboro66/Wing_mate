# models/mission.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Mission:
    date: str
    time: str
    aircraft: str
    duty: str
    locality: str
    airfield: str = 'N/A'
    pilots: List[str] = field(default_factory=list)
    weather: str = 'Não disponível'
    description: str = ''
    ha_report: str = ''
    
    @property
    def parsed_date(self) -> Optional[datetime]:
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(self.date, fmt)
            except ValueError:
                continue
        return None
