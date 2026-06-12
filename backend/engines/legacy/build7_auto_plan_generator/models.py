
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
class GoalType(str, Enum):
    RAID='raid'; TRAIL='trail'; HYROX='hyrox'; CROSSFIT='crossfit'
@dataclass(slots=True)
class GoalInput:
    goal_type: GoalType; target_event: str; duration_weeks: int; priority: str='A'; target_level: str='competitive'
@dataclass(slots=True)
class GapAnalysis:
    primary_gaps: list[str]; secondary_gaps: list[str]; readiness_constraints: list[str]; risk_flags: list[str]
@dataclass(slots=True)
class MacroCycle:
    duration_weeks: int; objective: str; phases: list[str]
@dataclass(slots=True)
class MesoCycle:
    index: int; weeks: int; focus: list[str]; load_target: float
@dataclass(slots=True)
class WeeklyPlan:
    week_number: int; focus: list[str]; sessions: list[str]; load_target: float
@dataclass(slots=True)
class DailyPlan:
    day_number: int; week_number: int; session: str; objective: str; load: float
@dataclass(slots=True)
class AutoPlan:
    goal: GoalInput; gap_analysis: GapAnalysis; macro_cycle: MacroCycle; meso_cycles: list[MesoCycle]; weeks: list[WeeklyPlan]; days: list[DailyPlan]; adaptive_rules: list[str]=field(default_factory=list)
