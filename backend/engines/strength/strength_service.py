from __future__ import annotations
import hashlib

from .family_registry import (STRENGTH_FAMILIES, get_families_by_category,
                              get_raid_test_families)
from .models import (AdaptiveLoadInput, GeneratedStrengthSession, LoadDecision,
                     ProgressionPhase, StrengthCategory)
from .progression_engine import AdaptiveLoadEngine, LongTermProgressionEngine
from .template_factory import STRENGTH_TEMPLATES


class StrengthAnalytics:
    @staticmethod
    def weekly_tonnage(sessions: list[dict]) -> float:
        """sessions: [{'weight_kg': x, 'reps': n, 'sets': s}, ...]"""
        total = 0.0
        for s in sessions:
            total += s.get("weight_kg", 0.0) * s.get("reps", 0) * s.get("sets", 0)
        return round(total, 1)

    @staticmethod
    def category_balance(history_family_ids: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {c.value: 0 for c in StrengthCategory}
        fam_map = {f.family_id: f.category.value for f in STRENGTH_FAMILIES}
        for fid in history_family_ids:
            cat = fam_map.get(fid)
            if cat:
                counts[cat] += 1
        return counts


class StrengthSessionSelector:
    """Selects family + template with anti-repetition over last 20 sessions."""

    def select(self, phase: ProgressionPhase, level: str,
               raid_focus: bool, recent_family_ids: list[str],
               seed: str = "") -> tuple[str, str]:
        recent = set(recent_family_ids[-20:])
        pool = get_raid_test_families() if raid_focus else list(STRENGTH_FAMILIES)
        fresh = [f for f in pool if f.family_id not in recent]
        if not fresh:
            fresh = pool  # everything seen recently: allow reuse
        idx = int(hashlib.sha256((seed + phase.value + level).encode()).hexdigest(), 16)
        family = fresh[idx % len(fresh)]
        candidates = [t for t in STRENGTH_TEMPLATES
                      if t.family_id == family.family_id and t.level == level]
        if not candidates:
            candidates = [t for t in STRENGTH_TEMPLATES if t.family_id == family.family_id]
        return family.family_id, candidates[0].template_id


class StrengthEngineService:
    """Build 8 pipeline:
    AdaptiveLoad -> Phase -> Level -> Selector(anti-rep) -> GeneratedStrengthSession
    """

    def __init__(self) -> None:
        self.load_engine = AdaptiveLoadEngine()
        self.progression = LongTermProgressionEngine()
        self.selector = StrengthSessionSelector()

    def generate(self, load_input: AdaptiveLoadInput, week_in_block: int,
                 weeks_to_goal: int | None, athlete_level: str,
                 raid_focus: bool, recent_family_ids: list[str],
                 seed: str = "") -> GeneratedStrengthSession:
        load_out = self.load_engine.decide(load_input)
        phase = self.progression.phase_for_week(week_in_block, weeks_to_goal)
        if load_out.decision == LoadDecision.DELOAD:
            phase = ProgressionPhase.DELOAD
        level = self.progression.level_for_phase(phase, athlete_level)
        family_id, template_id = self.selector.select(
            phase, level, raid_focus, recent_family_ids, seed)
        template = next(t for t in STRENGTH_TEMPLATES if t.template_id == template_id)
        session = GeneratedStrengthSession(
            session_id=f"strs_{seed or 'x'}_{template_id}",
            family_id=family_id,
            template_id=template_id,
            level=level,
            phase=phase,
            duration_min=max(20, round(template.duration_min * load_out.load_modifier)),
            expected_load=round(template.expected_load * load_out.load_modifier, 1),
            blocks=template.blocks,
            load_decision=load_out.decision,
            tags=template.tags,
        )
        session.validate()
        return session
