
from .models import MacroCycle
class MacroCycleBuilder:
    def validate(self, macro: MacroCycle) -> bool:
        return macro.duration_weeks>0 and bool(macro.phases) and bool(macro.objective)
