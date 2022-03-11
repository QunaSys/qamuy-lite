from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np
from openfermion.transforms import get_fermion_operator, jordan_wigner
from qamuy_base.backend_ext.qulacs import QulacsVectorSimulator
from qamuy_core.algorithms.ansatz import SymmetryPreservingReal
from qamuy_core.algorithms.eigensolver.vqe import VQE, VqeCostFunction
from qamuy_core.algorithms.sampling_strategies import SamplingStrategyProportional
from qamuy_core.chemistry.reference_states import prepare_hf_and_excited_states
from qamuy_core.evaluator import EvaluatorBinom
from qamuy_core.transforms import JordanWigner
from qamuy_core.utils.parsers.openfermion_parsers.operator_parser import (
    parse_of_operators,
)
from qamuy_core.chemistry.get_core_and_active_orbital_indices import (
    get_core_and_active_orbital_indices,
)
import logging

from ql_worker.common.model import ActiveSpace, EstValue

from ql_worker.vqe.model import VqeInput, VqeResult

from qamuy_core.chemistry.qamuy_molecular_data import QamuyMolecularData
from qamuy_core.chemistry.qamuy_run_pyscf import qamuy_run_pyscf

if TYPE_CHECKING:
    from ql_worker.common.model import Molecule

logger = logging.getLogger(__name__)


def run_vqe(qamuy_hamiltonian, n_qubits: int, n_electrons: int) -> float:
    # state preparation
    ref_states = prepare_hf_and_excited_states(
        n_qubits, n_electrons, qubit_mapping_method=JordanWigner(), k=1
    )

    ansatz = SymmetryPreservingReal(n_qubits, depth=n_qubits)
    # initial parameters preparation
    param_size = ansatz.parameter_count
    init_params = 2 * np.pi * np.random.random(param_size)

    backend = QulacsVectorSimulator()
    n_shots = 1_000_000
    evaluator = EvaluatorBinom(
        backend=backend,
        default_sampling_strategy=SamplingStrategyProportional(n_shots),
    )
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

    return energy, result["cost_hist"]


def compose_molecular_data(mol: Molecule) -> QamuyMolecularData:
    atom_str_list = []

    for i, atom in enumerate(mol.atoms):
        x, y, z = atom.coordinates
        atom_str_list.append(f"{atom.species}@{i} {x} {y} {z}")
    mol_data = QamuyMolecularData(
        ";".join(atom_str_list), mol.basis, mol.multiplicity, mol.charge
    )
    mol_data = qamuy_run_pyscf(
        mol_data,
        density_fitting=False,
        skip_scf=False,
    )
    return mol_data


def generate_hamiltonian(
    molecule_data: QamuyMolecularData, active_space: Optional[ActiveSpace]
) -> Tuple["QubitOperator", int, int]:
    if active_space is not None:
        occupied_indices, active_indices = get_core_and_active_orbital_indices(
            active_space.n_electrons, active_space.n_orbitals, molecule_data.n_orbitals
        )
        molecule_data.set_active_space(
            n_active_orbs=active_space.n_orbitals,
            n_active_eles=active_space.n_electrons,
        )
        n_electrons = active_space.n_electrons
        n_qubits = 2 * active_space.n_orbitals
    else:
        occupied_indices = None
        active_indices = None
        n_electrons = molecule_data.n_electrons
        n_qubits = molecule_data.n_qubits

    fermionic_hamiltonian = get_fermion_operator(
        molecule_data.get_molecular_hamiltonian(
            occupied_indices=occupied_indices,
            active_indices=active_indices,
            density_fitting=False,
            use_hdf5=False,
        )
    )
    jw_hamiltonian = jordan_wigner(fermionic_hamiltonian)
    return parse_of_operators(n_qubits, jw_hamiltonian), n_electrons, n_qubits


def vqe_executor(input: VqeInput) -> Tuple[str, VqeResult]:
    molecular_data = compose_molecular_data(input.molecule)
    qamuy_hamiltonian, n_electrons, n_qubits = generate_hamiltonian(
        molecular_data, input.active_space
    )
    energy, cost_hist = run_vqe(
        qamuy_hamiltonian=qamuy_hamiltonian,
        n_qubits=n_qubits,
        n_electrons=n_electrons,
    )
    return "success", VqeResult(
        energy=EstValue(value=energy, std=0), cost_history=cost_hist
    )
