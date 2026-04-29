from enum import StrEnum
from dataclasses import dataclass


class Product(StrEnum):
    OBSIDIAN_CUTLERY = "OBSIDIAN_CUTLERY"
    PYROFLEX_CELLS = "PYROFLEX_CELLS"
    THERMALITE_CORE = "THERMALITE_CORE"
    LAVA_CAKE = "LAVA_CAKE"
    MAGMA_INK = "MAGMA_INK"
    SCORIA_PASTE = "SCORIA_PASTE"
    ASHES_OF_THE_PHOENIX = "ASHES_OF_THE_PHOENIX"
    VOLCANIC_INCENSE = "VOLCANIC_INCENSE"
    SULFUR_REACTOR = "SULFUR_REACTOR"


@dataclass(frozen=True)
class Article:
    headline: str
    body: str
