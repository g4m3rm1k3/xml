# code app/domain.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class GCodeCommand:
    code: str
    value: float | str

@dataclass
class GCodeLine:
    number: Optional[int]
    commands: List[GCodeCommand]
    comment: Optional[str]

@dataclass
class MachineState:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    modals: Dict[str, str | float] = None
    toolpath: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None

    def __post_init__(self):
        if self.modals is None:
            self.modals = {
                "motion": "G0",
                "position_mode": "G90",
                "units": "G21",
                "feed_rate": 0.0,
            }
        if self.toolpath is None:
            self.toolpath = []