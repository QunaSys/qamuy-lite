from email.mime import multipart
from typing import List, Optional
from pydantic import BaseModel


class Atom(BaseModel):
    species: str
    coordinates: List[float]


class Molecule(BaseModel):
    atoms: List[Atom]
    charge: int
    multiplicity: int
    basis: str


class Penalty(BaseModel):
    type: str
    weight: float


class ActiveSpace(BaseModel):
    n_electrons: int
    n_orbitals: int


class Ansatz(BaseModel):
    type: str
    steps: int


class EstValue(BaseModel):
    value: float
    std: float
