from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RunCategory(str, Enum):
    RECOVERY = "recovery"
    Z2 = "z2"
    FARTLEK = "fartlek"
    TEMPO = "tempo"
    THRESHOLD = "threshold"
    VMA_SHORT = "vma_short"
    VMA_LONG = "vma_long"
    HILLS = "hills"
    LONG_RUN = "long_run"
    RAID = "raid"
    TEST = "test"

class ReadinessZone(str, Enum):
    PEAK = "peak"
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"

class FatigueZone(str, Enum):
    OPTIMAL = "optimal"
    WARNING = "warning"
    DANGER = "danger"

@dataclass(frozen=True)
class RunFamily:
    id: str
    name: str
    category: RunCategory
    difficulty: int
    tags: list[str] = field(default_factory=list)

@dataclass
class RunTemplate:
    id: str
    family_id: str
    level: str
    duration_min: int
    structure: dict[str, Any]
    tags: list[str] = field(default_factory=list)

@dataclass
class GeneratedRunSession:
    family_id: str
    template_id: str
    variant: str
    duration_min: int
    structure: dict[str, Any]
    category: RunCategory
    terrain_type: str
    expected_load: float
    target_type: str = "pace"
    pace_target: str | None = None
    rpe_target: int | None = None
    d_plus_target: int | None = None
    tags: list[str] = field(default_factory=list)
