from __future__ import annotations
from .models import (LifeConstraint, MemoryDigest, MemoryEntry, MemoryKind,
                     TwinState)


class AthleteMemory:
    """Mémoire long terme : apprend des patterns, oublie progressivement
    l'anecdotique, garde l'important (poids décroissant, breakthrough durables)."""

    DECAY_PER_30D = {
        MemoryKind.SESSION_RESPONSE: 0.85,
        MemoryKind.FATIGUE_PATTERN: 0.95,
        MemoryKind.PREFERENCE: 0.98,
        MemoryKind.INJURY_SIGNAL: 0.99,   # on n'oublie presque jamais un signal blessure
        MemoryKind.BREAKTHROUGH: 0.97,
    }
    MAX_ENTRIES = 500

    def __init__(self) -> None:
        self.entries: list[MemoryEntry] = []

    def remember(self, entry: MemoryEntry) -> None:
        entry.validate()
        self.entries.append(entry)
        if len(self.entries) > self.MAX_ENTRIES:
            # drop the lightest-weight oldest entries
            self.entries.sort(key=lambda e: (e.weight, e.date))
            self.entries = self.entries[len(self.entries) - self.MAX_ENTRIES:]

    def apply_decay(self, periods_30d: int = 1) -> None:
        if periods_30d < 0:
            raise ValueError("periods >= 0")
        for e in self.entries:
            e.weight = round(e.weight * self.DECAY_PER_30D[e.kind] ** periods_30d, 3)
        self.entries = [e for e in self.entries if e.weight >= 0.05]

    def digest(self) -> MemoryDigest:
        def top(kind: MemoryKind, positive: bool | None = None, n: int = 5) -> list[str]:
            pool = [e for e in self.entries if e.kind == kind]
            if positive is True:
                pool = [e for e in pool if "+" in e.tags or "positive" in e.tags]
            elif positive is False:
                pool = [e for e in pool if "-" in e.tags or "negative" in e.tags]
            pool.sort(key=lambda e: e.weight, reverse=True)
            return [e.summary for e in pool[:n]]

        return MemoryDigest(
            works_well=top(MemoryKind.SESSION_RESPONSE, True),
            works_poorly=top(MemoryKind.SESSION_RESPONSE, False),
            risk_signals=top(MemoryKind.INJURY_SIGNAL),
            preferences=top(MemoryKind.PREFERENCE),
            recent_breakthroughs=top(MemoryKind.BREAKTHROUGH),
        )


class DigitalTwin:
    """Courbes fitness/fatigue/forme (modèle Banister EWMA 42j/7j)."""

    def __init__(self, state: TwinState | None = None) -> None:
        self.state = state or TwinState()

    def ingest_day(self, load_su: float) -> TwinState:
        return self.state.update(load_su)

    def simulate(self, daily_loads: list[float]) -> list[TwinState]:
        out: list[TwinState] = []
        sim = TwinState(self.state.fitness, self.state.fatigue)
        for load in daily_loads:
            sim.update(load)
            out.append(TwinState(sim.fitness, sim.fatigue))
        return out

    def form_label(self) -> str:
        tsb = self.state.form
        if tsb > 5:
            return "fresh"
        if tsb > -10:
            return "neutral"
        if tsb > -25:
            return "fatigued"
        return "overreached"

    def taper_projection(self, days: int = 14, taper_load: float = 12.0) -> float:
        """TSB projeté après un affûtage — utile avant benchmarks/sélection."""
        if not 1 <= days <= 28:
            raise ValueError("days 1-28")
        sims = self.simulate([taper_load] * days)
        return sims[-1].form


class LifeEngine:
    """Contraintes vie réelle → capacité d'entraînement effective du jour."""

    def __init__(self) -> None:
        self.constraints: list[LifeConstraint] = []

    def add(self, c: LifeConstraint) -> None:
        c.validate()
        self.constraints.append(c)

    def capacity_for(self, date: str) -> float:
        """1.0 = pleine capacité ; impacts multiples se cumulent (multiplicatif)."""
        cap = 1.0
        for c in self.constraints:
            if c.date_from <= date <= c.date_to:
                cap *= (1 - c.impact)
        return round(max(0.0, cap), 2)

    def active_notes(self, date: str) -> list[str]:
        return [f"{c.kind.value}: {c.note}" for c in self.constraints
                if c.date_from <= date <= c.date_to and c.note]
