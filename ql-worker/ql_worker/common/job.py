from dataclasses import dataclass
from typing import Union


@dataclass
class JobResultEst:
    is_success: bool
    job_id: str
    cost_sec: float


@dataclass
class JobResultCalc:
    is_success: bool
    job_id: str
    energy: float


JobResult = Union[JobResultEst, JobResultCalc]
