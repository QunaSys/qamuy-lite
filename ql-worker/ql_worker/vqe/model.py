from pydantic import BaseModel
from typing import List, Optional
from ql_worker.common.model import ActiveSpace, EstValue, Molecule, Ansatz, Penalty


class VqeInput(BaseModel):
    molecule: Molecule
    ansatz: Ansatz
    active_space: Optional[ActiveSpace]
    penalties: Optional[List[Penalty]]


class VqeResult(BaseModel):
    cost_history: List[float]
    energy: EstValue


class VqeRequest(BaseModel):
    input: VqeInput


class VqeResponse(BaseModel):
    status: str
    result: VqeResult
