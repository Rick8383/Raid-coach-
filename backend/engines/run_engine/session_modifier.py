from dataclasses import dataclass

@dataclass
class ModifiedSession:
    family_id: str
    variant: str
    expected_load: float
    structure: dict

def modify_session(family_id: str, availability_min: int = 60, level: str = "intermediate") -> ModifiedSession:
    if availability_min >= 80:
        variant, load = "3x12", 1.10
    elif availability_min >= 60:
        variant, load = "4x8", 1.00
    else:
        variant, load = "5x6", 0.90
    structure = {"warmup": 15, "main": [{"variant": variant, "type": family_id}], "cooldown": 10}
    return ModifiedSession(family_id=family_id, variant=variant, expected_load=load, structure=structure)
