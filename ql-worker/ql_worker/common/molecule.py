from dataclasses import dataclass
from typing import List


@dataclass
class Molecule:
    atoms: List[str]
    position: List[List[float]]
    basis: str
    charge: int
    multiplicity: int
