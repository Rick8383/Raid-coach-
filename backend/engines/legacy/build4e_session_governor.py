
from enum import Enum

class Decision(str, Enum):
    ALLOW="allow"
    REDUCE="reduce"
    MODIFY="modify"
    BLOCK="block"

def evaluate(readiness:int,recovery:int):
    if readiness < 35 or recovery < 35:
        return Decision.BLOCK
    if readiness < 60 or recovery < 60:
        return Decision.REDUCE
    if readiness < 75 or recovery < 75:
        return Decision.MODIFY
    return Decision.ALLOW
