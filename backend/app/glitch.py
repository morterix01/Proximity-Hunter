from dataclasses import dataclass

from .config import settings
from .models import GlitchTier


@dataclass
class GlitchResult:
    tier: GlitchTier
    old_price: float
    new_price: float
    drop_pct: float


def compute_drop_pct(reference: float, current: float) -> float:
    """Percent drop of current vs reference. 0 if reference invalid or price rose."""
    if reference is None or reference <= 0 or current is None or current < 0:
        return 0.0
    drop = (reference - current) / reference * 100.0
    return max(0.0, round(drop, 2))


def classify(reference: float, current: float) -> GlitchResult:
    """Map a price drop to a glitch tier using configured thresholds.

    >= GLITCH_ERROR_THRESHOLD  -> Errore Prezzo (error)
    >= GLITCH_SUPER_THRESHOLD  -> Super Sconto  (super)
    otherwise                  -> none
    """
    drop = compute_drop_pct(reference, current)

    if drop >= settings.glitch_error_threshold:
        tier = GlitchTier.ERROR
    elif drop >= settings.glitch_super_threshold:
        tier = GlitchTier.SUPER
    else:
        tier = GlitchTier.NONE

    return GlitchResult(tier=tier, old_price=reference, new_price=current, drop_pct=drop)
