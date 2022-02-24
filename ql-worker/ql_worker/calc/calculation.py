import numpy as np
from openfermion.chem import MolecularData
from openfermion.transforms import get_fermion_operator, jordan_wigner
from openfermionpyscf import run_pyscf
from qamuy_base.backend_ext.qulacs import QulacsVectorSimulator
from qamuy_core.algorithms.ansatz import SymmetryPreservingReal
from qamuy_core.operator import Observable
from qamuy_core.algorithms.eigensolver.vqe import VQE, VqeCostFunction
from qamuy_core.algorithms.sampling_strategies import SamplingStrategyProportional
from qamuy_core.chemistry.reference_states import prepare_hf_and_excited_states
from qamuy_core.evaluator import EvaluatorBinom
from qamuy_core.transforms import JordanWigner
from qamuy_core.utils.parsers.openfermion_parsers.operator_parser import (
    parse_of_operators,
)
from ql_worker.common.molecule import Molecule
from ql_worker.common.job import JobResultCalc, JobResult
import logging

logger = logging.getLogger(__name__)


def run_vqe(
    qamuy_hamiltonian, n_qubits: int, n_electrons: int, tolerance: float
) -> float:
    # state preparation
    ref_states = prepare_hf_and_excited_states(
        n_qubits, n_electrons, qubit_mapping_method=JordanWigner(), k=1
    )

    ansatz = SymmetryPreservingReal(n_qubits, depth=n_qubits)
    # initial parameters preparation
    param_size = ansatz.parameter_count
    init_params = 2 * np.pi * np.random.random(param_size)

    backend = QulacsVectorSimulator()
    # full commute: N^3.2 * exp(7.3)
    # bitwise commute: N^4.8 * exp(5.1)
    n_shots_for_1mHa = np.exp(7.3) * (n_qubits ** 3.2)
    n_shots = n_shots_for_1mHa / (tolerance / 1e-3) ** 2
    evaluator = EvaluatorBinom(
        backend=backend,
        default_sampling_strategy=SamplingStrategyProportional(n_shots),
    )
    # TODO change options according to the tolerance
    options = {
        "disp": True,
        "maxiter": 2048,
        # "maxfev": 2048,
        "ftol": 1e-6,
        # "gtol": 1e-6,
    }

    vqe_cost_function = VqeCostFunction(
        ansatz, qamuy_hamiltonian, evaluator, ref_states=ref_states
    )
    vqe = VQE(vqe_cost_function)
    result = vqe.find_minimum(
        "BFGS", init_params, options=options, use_shift_rule=True, callback=None
    )
    energy = result["cost_hist"][-1]

    return energy


def compose_molecular_data(mol: Molecule) -> MolecularData:
    geometry = [[atom, mol.position[index]] for index, atom in enumerate(mol.atoms)]
    molecule = MolecularData(geometry, mol.basis, mol.multiplicity, mol.charge)
    return run_pyscf(molecule)


def generate_hamiltonian(molecule_data: MolecularData) -> Observable:
    fermionic_hamiltonian = get_fermion_operator(
        molecule_data.get_molecular_hamiltonian()
    )
    jw_hamiltonian = jordan_wigner(fermionic_hamiltonian)
    return parse_of_operators(molecule_data.n_qubits, jw_hamiltonian)


def calculation(job_id: str, molecule: Molecule, tolerance: float) -> JobResult:
    try:
        molecular_data = compose_molecular_data(molecule)
        qamuy_hamiltonian = generate_hamiltonian(molecular_data)
        energy = run_vqe(
            qamuy_hamiltonian=qamuy_hamiltonian,
            n_qubits=molecular_data.n_qubits,
            n_electrons=molecular_data.n_electrons,
            tolerance=tolerance,
        )
    except Exception as e:
        logger.exception(e)
        return JobResultCalc(is_success=False, job_id=job_id, energy=0)

    return JobResultCalc(is_success=True, job_id=job_id, energy=energy)
