"""Cohérence & progression des séances de course VMA.

Régression du bug « 3×20×300 m = 18 km juste pour le cœur » : le volume de
fractionné (distance courue à l'effort) doit rester cohérent quel que soit le
seed, et croître de façon progressive avec l'avancée du plan (`progress`).
"""
from engines.run_generator import generate_run
from engines.run_generator.generator import RUN_TYPES


def _vma_courte_volume_m(det: dict) -> float:
    b = det["body"][0]
    frac_m = float(str(b["fraction"]).replace("m", ""))
    return b["series"] * b["reps"] * frac_m


def _vma_longue_volume_m(det: dict) -> float:
    return float(sum(it.get("distance_m", 0) for it in det["body"]))


def test_all_run_types_generate():
    for t in RUN_TYPES:
        for seed in range(1, 101):
            det = generate_run(t, seed)
            assert det["duration_min"] > 0
            assert det["distance_km"] > 0


def test_vma_courte_volume_is_coherent():
    # Aucune séance ne doit dépasser ~5 km d'effort fractionné, jamais 18 km.
    for seed in range(1, 101):
        for progress in [None, 0, 5, 10, 20, 40]:
            det = generate_run("vma_courte", seed, progress=progress)
            vol = _vma_courte_volume_m(det)
            assert 1200 <= vol <= 5200, f"seed={seed} progress={progress} vol={vol}"


def test_vma_longue_volume_is_coherent():
    for seed in range(1, 101):
        for progress in [None, 0, 5, 10, 20, 40]:
            det = generate_run("vma_longue", seed, progress=progress)
            vol = _vma_longue_volume_m(det)
            assert 2000 <= vol <= 6000, f"seed={seed} progress={progress} vol={vol}"


def test_start_of_plan_is_gentle():
    # Début de plan (progress=0) : volume moyen bas et cohérent (≈ 2×10×300).
    vols = [_vma_courte_volume_m(generate_run("vma_courte", s, progress=0))
            for s in range(1, 101)]
    assert sum(vols) / len(vols) <= 2800


def test_volume_is_progressive():
    # Le volume moyen de fractionné doit croître entre début et milieu de plan.
    def avg(kind, vol_fn, progress):
        return sum(vol_fn(generate_run(kind, s, progress=progress))
                   for s in range(1, 101)) / 100
    assert avg("vma_courte", _vma_courte_volume_m, 20) > avg("vma_courte", _vma_courte_volume_m, 0)
    assert avg("vma_longue", _vma_longue_volume_m, 20) > avg("vma_longue", _vma_longue_volume_m, 0)
