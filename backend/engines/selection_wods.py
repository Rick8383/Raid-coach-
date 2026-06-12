"""WODs Sélection RAID — benchmarks officiels + générateur de variantes.

Source : WODs réels des sélections RAID (fournis par l'athlète, 11/06/2026).
Les WODs changent chaque année mais gardent le même ADN opérationnel :
- formats death-by EMOM, time cap courts sous lest
- mouvements : cardio machine, box over, tractions, burpees target,
  trap bar, farmer walk, portage mannequin/bélier
Standards matériels : gilet 10 kg, gilet lourd 20 kg, bélier 16 kg, mannequin 75 kg.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

# ---------- Standards matériels (validés utilisateur 11/06/2026) ----------
EQUIPMENT_STANDARDS = {
    "vest_kg": 10.0,
    "heavy_vest_kg": 20.0,
    "ram_kg": 16.0,        # bélier de porte
    "dummy_kg": 75.0,      # mannequin rescue
    "trap_bar_dl_kg": 115.0,
}


@dataclass(slots=True, frozen=True)
class SelectionWOD:
    wod_id: str
    name: str
    wod_format: str          # "death_by_emom" | "time_cap_loaded"
    description: list[str]
    scoring: str
    equipment: list[str]
    is_official_benchmark: bool = False
    year: int | None = None


# ---------- BENCHMARKS OFFICIELS (à refaire toutes les 8-12 semaines) ----------
OFFICIAL_BENCHMARKS = [
    SelectionWOD(
        wod_id="wod_selection_pdc_2026",
        name="WOD PDC Sélection 2026 (officiel)",
        wod_format="death_by_emom",
        description=[
            "Death by EMOM +1 (la 1re minute : 1 tour, puis +1 par minute jusqu'à échec)",
            "11 cal ski erg",
            "11 box over",
            "11 cal row",
            "11 tractions",
            "11 burpees target",
        ],
        scoring="Dernière minute complétée + reps dans la minute d'échec",
        equipment=["ski_erg", "box", "rower", "pullup_bar", "target"],
        is_official_benchmark=True,
        year=2026,
    ),
    SelectionWOD(
        wod_id="wod_selection_force_2026",
        name="WOD Force Sélection 2026 (officiel)",
        wod_format="time_cap_loaded",
        description=[
            "Time cap 5 min — gilet (10 kg) + gilet lourd (20 kg)",
            "30 cal echo bike",
            "4 × (10 deadlift trap bar @115 kg + 5 m farmer walk trap bar)",
            "10 box over @bélier (16 kg)",
            "Max distance @mannequin (75 kg) dans le temps restant",
        ],
        scoring="Distance mannequin (m) si circuit terminé, sinon progression dans le circuit",
        equipment=["echo_bike", "trap_bar", "box", "ram_16kg", "dummy_75kg",
                   "vest_10kg", "heavy_vest_20kg"],
        is_official_benchmark=True,
        year=2026,
    ),
]


# ---------- ADN des WODs sélection : pools de substitution ----------
_CARDIO_POOL = ["cal ski erg", "cal row", "cal echo bike", "m run navette"]
_GYM_POOL = ["tractions", "burpees target", "box over", "toes to bar", "dips"]
_LOADED_POOL = [
    "deadlift trap bar @115 kg",
    "farmer walk trap bar (5 m)",
    "box over @bélier (16 kg)",
    "portage mannequin (75 kg)",
    "sandbag carry (40 kg)",
    "fente marchée @bélier (16 kg)",
]
_DEATH_BY_REPS = [9, 10, 11, 12]
_TIME_CAPS = [5, 6, 7, 8]


class SelectionWODGenerator:
    """Génère des variantes du même ADN opérationnel, jamais deux fois la même.
    Déterministe par seed (reproductible, anti-répétition par historique)."""

    def _pick(self, pool: list[str], seed: str, k: int, salt: str = "") -> list[str]:
        out: list[str] = []
        available = list(pool)
        for i in range(min(k, len(available))):
            h = int(hashlib.sha256(f"{seed}:{salt}:{i}".encode()).hexdigest(), 16)
            out.append(available.pop(h % len(available)))
        return out

    @staticmethod
    def _fresh_seed(seed: str, prefix: str, recent_wod_ids: list[str] | None) -> str:
        """Dérive un seed dont l'id n'est pas dans l'historique (borné à 50 essais :
        au-delà, l'anti-répétition cède plutôt que de boucler indéfiniment)."""
        for _ in range(50):
            wod_id = f"{prefix}{hashlib.sha256(seed.encode()).hexdigest()[:8]}"
            if not recent_wod_ids or wod_id not in recent_wod_ids:
                break
            seed += "_alt"
        return seed

    def death_by_variant(self, seed: str, recent_wod_ids: list[str] | None = None) -> SelectionWOD:
        seed = self._fresh_seed(seed, "sel_db_", recent_wod_ids)
        wod_id = f"sel_db_{hashlib.sha256(seed.encode()).hexdigest()[:8]}"
        reps = _DEATH_BY_REPS[int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(_DEATH_BY_REPS)]
        cardio = self._pick(_CARDIO_POOL, seed, 2, "cardio")
        gym = self._pick(_GYM_POOL, seed, 3, "gym")
        movements = [f"{reps} {m}" for m in (cardio[:1] + gym[:2] + cardio[1:2] + gym[2:3])]
        return SelectionWOD(
            wod_id=wod_id,
            name=f"Death By Sélection — variante {wod_id[-4:].upper()}",
            wod_format="death_by_emom",
            description=["Death by EMOM +1"] + movements,
            scoring="Dernière minute complétée + reps",
            equipment=["selon mouvements"],
        )

    def time_cap_variant(self, seed: str, recent_wod_ids: list[str] | None = None) -> SelectionWOD:
        seed = self._fresh_seed(seed, "sel_tc_", recent_wod_ids)
        wod_id = f"sel_tc_{hashlib.sha256(seed.encode()).hexdigest()[:8]}"
        h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
        cap = _TIME_CAPS[h % len(_TIME_CAPS)]
        cardio = self._pick(_CARDIO_POOL, seed, 1, "c")[0]
        loaded = self._pick(_LOADED_POOL, seed, 3, "l")
        finisher = "portage mannequin (75 kg)" if "portage mannequin (75 kg)" not in loaded else "sandbag carry (40 kg)"
        return SelectionWOD(
            wod_id=wod_id,
            name=f"Force Sélection — variante {wod_id[-4:].upper()}",
            wod_format="time_cap_loaded",
            description=(
                [f"Time cap {cap} min — gilet 10 kg" + (" + gilet lourd 20 kg" if h % 2 else "")]
                + [f"{20 + h % 15} {cardio}"]
                + [f"3-4 × ({8 + h % 5} {m})" for m in loaded[:2]]
                + [f"10 {loaded[2]}"]
                + [f"Max distance {finisher} dans le temps restant"]
            ),
            scoring="Distance finisher (m) ou progression circuit",
            equipment=["selon mouvements", "vest_10kg"],
        )

    def progression_block(self, weeks: int, seed: str) -> list[SelectionWOD]:
        """Bloc de préparation : alternance variantes, benchmarks officiels en
        semaine 1 (baseline) et dernière semaine (re-test)."""
        if not 4 <= weeks <= 16:
            raise ValueError("weeks must be 4-16")
        block: list[SelectionWOD] = list(OFFICIAL_BENCHMARKS)  # baseline S1
        for w in range(2, weeks):
            gen = self.death_by_variant if w % 2 == 0 else self.time_cap_variant
            block.append(gen(f"{seed}_w{w}"))
        block += list(OFFICIAL_BENCHMARKS)  # re-test dernière semaine
        return block
