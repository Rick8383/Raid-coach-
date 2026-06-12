import hashlib, json

def structure_hash(structure: dict) -> str:
    return hashlib.sha256(json.dumps(structure, sort_keys=True).encode()).hexdigest()

def anti_repetition_score(candidate, history: list[dict]) -> float:
    score = 1.0
    c_hash = structure_hash(candidate.structure)
    for past in history[-20:]:
        if past.get("family_id") == candidate.family_id and past.get("variant") == candidate.variant:
            return 0.0
        if past.get("structure_hash") == c_hash:
            score *= 0.2
        elif past.get("family_id") == candidate.family_id:
            score *= 0.5
    return score
