from __future__ import annotations
from hyrox_family_registry import get_hyrox_families
from hyrox_models import LEVELS, HyroxBlock, HyroxStation, HyroxTemplate

LEVEL_MULTIPLIERS = {
    "beginner": 0.70,
    "intermediate": 0.85,
    "advanced": 1.00,
    "deload": 0.75,
    "competition": 1.10,
    "elite": 1.25,
}

class HyroxTemplateFactory:
    def build_all(self) -> list[HyroxTemplate]:
        templates = []
        for family in get_hyrox_families():
            templates.extend(self.build_for_family(family))
        return templates

    def build_for_family(self, family) -> list[HyroxTemplate]:
        return [self._build_template(family, level) for level in LEVELS]

    def _build_template(self, family, level: str) -> HyroxTemplate:
        multiplier = LEVEL_MULTIPLIERS[level]
        duration = max(20, int(family.base_duration_min * multiplier))

        blocks = []
        for station in family.stations:
            if station == HyroxStation.RUN:
                blocks.append(HyroxBlock(station=station, distance_m=int(1000 * multiplier), duration_min=max(6, int(8 * multiplier))))
            elif station in {HyroxStation.SKIERG, HyroxStation.ROW}:
                blocks.append(HyroxBlock(station=station, distance_m=int(1000 * multiplier), duration_min=max(5, int(7 * multiplier))))
            elif station in {HyroxStation.SLED_PUSH, HyroxStation.SLED_PULL}:
                blocks.append(HyroxBlock(station=station, distance_m=50, load_kg=int(80 * multiplier), duration_min=max(4, int(6 * multiplier))))
            elif station == HyroxStation.BURPEE_BROAD_JUMP:
                blocks.append(HyroxBlock(station=station, distance_m=80, duration_min=max(5, int(8 * multiplier))))
            elif station == HyroxStation.FARMER_CARRY:
                blocks.append(HyroxBlock(station=station, distance_m=200, load_kg=int(24 * multiplier), duration_min=max(4, int(6 * multiplier))))
            elif station == HyroxStation.SANDBAG_LUNGE:
                blocks.append(HyroxBlock(station=station, distance_m=100, load_kg=int(20 * multiplier), duration_min=max(5, int(7 * multiplier))))
            elif station == HyroxStation.WALL_BALL:
                blocks.append(HyroxBlock(station=station, reps=int(100 * multiplier), load_kg=int(6 * multiplier), duration_min=max(5, int(8 * multiplier))))

        return HyroxTemplate(
            template_id=f"{family.family_id}_{level}",
            family_id=family.family_id,
            level=level,
            duration_min=duration,
            expected_load=round(multiplier, 2),
            blocks=blocks,
            tags=["hyrox", level, *family.pattern_tags],
        )

def build_all_hyrox_templates() -> list[HyroxTemplate]:
    return HyroxTemplateFactory().build_all()
