"""Built-in print specifications and validation."""
from __future__ import annotations
from dataclasses import dataclass

PT_PER_MM = 72 / 25.4

@dataclass(frozen=True)
class PrintProfile:
    id: str
    name: str
    width_mm: float
    height_mm: float
    bleed_mm: float = 3.0
    min_dpi: int = 300
    tolerance_mm: float = 1.0

    @property
    def width_pt(self) -> float:
        return self.width_mm * PT_PER_MM

    @property
    def height_pt(self) -> float:
        return self.height_mm * PT_PER_MM

PROFILES: dict[str, PrintProfile] = {
    "a4-flyer": PrintProfile("a4-flyer", "A4 flyer", 210, 297),
    "a3-poster": PrintProfile("a3-poster", "A3 poster", 297, 420),
    "business-card": PrintProfile("business-card", "Business card", 90, 54, 3, 300, .5),
    "label": PrintProfile("label", "Product label", 100, 150, 2, 300, .5),
}

def get_profile(profile_id: str) -> PrintProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown profile '{profile_id}'. Choose from: {', '.join(PROFILES)}") from exc
