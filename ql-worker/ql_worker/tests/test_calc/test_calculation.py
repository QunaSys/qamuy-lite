from ql_worker.calc.calculation import (
    calculation,
    compose_molecular_data,
    generate_hamiltonian,
    run_vqe,
)
from ql_worker.common.molecule import Molecule
from openfermion.chem import MolecularData
from qamuy_core.operator import Observable
from openfermionpyscf import run_pyscf
from openfermion.transforms import get_fermion_operator, jordan_wigner
from qamuy_core.utils.parsers.openfermion_parsers.operator_parser import (
    parse_of_operators,
)


def test_compose_molecular_data():
    mol = Molecule(
        atoms=["H", "H"],
        position=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],
        basis="sto-3g",
        charge=0,
        multiplicity=1,
    )
    molecular_data = compose_molecular_data(mol=mol)
    assert isinstance(molecular_data, MolecularData)


def test_generate_hamiltonian():
    molecule = MolecularData(
        [["H", [0, 0, 0]], ["H", [0.0, 0.0, 0.74]]], "sto-3g", 1, 0
    )
    molecule = run_pyscf(molecule)
    observable = generate_hamiltonian(molecule)
    assert isinstance(observable, Observable)
    energy = run_vqe(observable, molecule.n_qubits, molecule.n_electrons, 0.01)
    assert isinstance(energy, float)


def test_run_vqe():
    molecule = MolecularData(
        [["H", [0, 0, 0]], ["H", [0.0, 0.0, 0.74]]], "sto-3g", 1, 0
    )
    molecule = run_pyscf(molecule)
    fermionic_hamiltonian = get_fermion_operator(molecule.get_molecular_hamiltonian())
    jw_hamiltonian = jordan_wigner(fermionic_hamiltonian)
    observable = parse_of_operators(molecule.n_qubits, jw_hamiltonian)
    energy = run_vqe(observable, molecule.n_qubits, molecule.n_electrons, 0.01)
    assert isinstance(energy, float)


def test_calculation():
    mol = Molecule(
        atoms=["H", "H"],
        position=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],
        basis="sto-3g",
        charge=0,
        multiplicity=1,
    )
    job_id = "test"
    result = calculation(molecule=mol, job_id=job_id, tolerance=0.01)
    assert result.job_id == job_id
    assert result.is_success is True
    assert isinstance(result.energy, float)
