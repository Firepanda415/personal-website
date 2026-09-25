"""Narration for the NWQLib (Northwest Quantum Library) explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words; `S` fills it in from SPOKEN.

Sources, all in the NWQLib repository at the commit recorded in data.json:
- problem: docs/why_nwqlib.md ("A workflow at the level of the scientific problem" and "The
  algorithm layer that Qiskit 2.x does not provide").
- workflow: docs/quickstart.md and docs/scientist.md.
- plate, evidence (example 1): examples/qls_linear_system_intro.ipynb, recomputed in data.json,
  including its report and reference check (Appendix B and C); the ring planning from "Plan and
  estimate beyond simulation" in docs/algorithms/qls.md, also recomputed; the
  unknown-is-not-zero rule from docs/resources.md.
- gcim (example 2): examples/gcim_lanczos_qpe_eigenvalue_intro.ipynb (exact evaluation from
  state vectors, the circuit count with exact outcome probabilities in Section 4 and Appendix A,
  the reanalysis in Section 4 and the report in Appendix B), and docs/why_nwqlib.md for the
  comparison with other packages (checked on 2026-09-25).
- others: README.md and docs/examples.md for the methods and their example notebooks, and
  docs/why_nwqlib.md for what other packages also provide.
- running: docs/backends.md and docs/CODE_TOUR.md.
- scope: docs/examples.md (at most 12 simulated qubits), docs/why_nwqlib.md and
  docs/algorithms/qls.md for the inputs QLS needs from the user, and the open work in
  docs/ROADMAP.md.
"""

# Slightly faster than the series default (tts.SPEED) because this video covers a whole library.
SPEED = 1.12

SPOKEN = {
    "NWQLib": "N W Q Lib",
    "NWQ-Sim": "N W Q Sim",
    "ADAPT-GCIM": "adapt G C I M",
    "GCIM": "G C I M",
    "QCELS": "Q C E L S",
    "QSVT": "Q S V T",
    "LCHS": "L C H S",
    "QLS": "Q L S",
    "HHL": "H H L",
    "CCSD": "C C S D",
    "CX": "C X",
    "Aer": "[Aer](/ˈɛɹ/)",
    "Qiskit": "[Qiskit](/kˈɪskɪt/)",
    "Qualtran": "[Qualtran](/kwˈɔltɹæn/)",
    "Quantinuum": "[Quantinuum](/kwˌɑntɪnˈuəm/)",
    "Dalzell": "[Dalzell](/dælzˈɛl/)",
    "numpy": "num pie",
    "H4": "H four",
    "Ax = b": "A x equals b",
    "A/α": "A over alpha",
}


def S(text, say=None):
    spoken = say or text
    if say is None:
        for word, sound in SPOKEN.items():
            spoken = spoken.replace(word, sound)
    return dict(text=text, say=spoken) if spoken != text else dict(text=text)


SEGMENTS = [
    ("problem", [
        S("Suppose you have a scientific problem, such as a linear system Ax = b from a heat or flow model, and you want to try a quantum algorithm on it."),
        S("Papers on quantum linear solvers work with a block encoding, a circuit that holds A divided by a normalization α, and with a polynomial of that matrix and its phase angles.",
          "Papers on quantum linear solvers work with a block encoding, a circuit that holds A divided by a normalization alpha, and with a polynomial of that matrix and its phase angles."),
        S("Between your matrix and an answer lie many steps, from bounding the condition number to keeping the successful outcomes and restoring the scale and phase of x."),
        S("In comparable examples from PennyLane and CUDA-Q, the example code, outside the library, restores the scale of x. Qiskit 2 has no block encoding, QSVT or LCHS in its circuit library.",
          "In comparable examples from Penny Lane and CUDA Q, the example code, outside the library, restores the scale of x. [Qiskit](/kˈɪskɪt/) 2 has no block encoding, Q S V T or L C H S in its circuit library."),
    ]),
    ("workflow", [
        S("NWQLib, the Northwest Quantum Library from Pacific Northwest National Laboratory, connects these steps at the level of the scientific problem, and it builds Qiskit circuits."),
        S("You state the problem and configure a method. Then plan selects the construction, estimate counts its cost, and solve runs the circuit and returns a Result."),
        S("The Result keeps its Plan and data, so verification, saving and reanalysis act on the same record."),
    ]),
    ("plate", [
        S("The first example is a square plate with cold edges and two heaters inside. On a four-by-four grid, its steady temperature solves a linear system with sixteen unknowns."),
        S("With QLS, the quantum linear solver, planning chose a Pauli block encoding with α = 8, which gives an encoded condition number of 10.5. It then chose an odd polynomial of degree 59 that approximates the inverse within ε = 0.01.",
          "With Q L S, the quantum linear solver, planning chose a [Pauli](/pˈWli/) block encoding with alpha equal to 8, which gives an encoded condition number of 10 point 5. It then chose an odd polynomial of degree 59 that approximates the inverse within epsilon equal to 0 point 0 1."),
        S("It also computed the phase angles and fixed the circuit at nine qubits."),
        S("Before any circuit exists, estimate adds up a resource law for each block, a formula for its gate count, and predicts 7,846 CX gates. Compiled by Qiskit, the circuit has 7,710."),
        S("Solving simulated the circuit on Aer, kept the outcome in which the ancilla qubits signal success, and restored the physical scale.",
          "Solving simulated the circuit on [Aer](/ˈɛɹ/), kept the outcome in which the [ancilla](/ænsˈɪlə/) qubits signal success, and restored the physical scale."),
        S("The returned x is the temperature field itself, not a unit vector. It agrees with numpy's direct solve to 0.91 percent, and each shot succeeds with probability 0.16.",
          "The returned x is the temperature field itself, not a unit vector. It agrees with num pie's direct solve to 0 point 9 1 percent, and each shot succeeds with probability 0 point 1 6."),
        S("Only a simulator reads out all sixteen amplitudes. Hardware runs estimate quantities such as a quadratic form of x from shots."),
    ]),
    ("evidence", [
        S("In the plate's estimate, a cost that no law covers, such as circuit depth, is reported as unknown instead of zero."),
        S("Problems given in compact form can be planned beyond simulation. A periodic stencil with 2⁴⁰ unknowns and a product-state right-hand side is estimated at 44 qubits and about 92,000 CX gates, with nothing solved.",
          "Problems given in compact form can be planned beyond simulation. A periodic stencil with two to the fortieth unknowns and a product-state right-hand side is estimated at 44 qubits and about 92,000 C X gates, with nothing solved."),
        S("The plate's report states that accuracy was not assessed. The polynomial's error bound, 0.0098, covers only one part of the error of the answer.",
          "The plate's report states that accuracy was not assessed. The polynomial's error bound, 0 point 0 0 9 8, covers only one part of the error of the answer."),
        S("A reference check runs only on request. Here, verify solved the system classically and found the same 0.91 percent error, within the method's allowance of 1 percent.",
          "A reference check runs only on request. Here, verify solved the system classically and found the same 0 point 9 1 percent error, within the method's allowance of 1 percent."),
    ]),
    ("gcim", [
        S("The second example, the ground-state energy of a molecule, uses ADAPT-GCIM, a generator-coordinate-inspired eigensolver. No other package checked in September 2026 implements it, and its authors publish it as research code."),
        S("From the Hartree–Fock state, each iteration adds basis states from the excitation with the largest energy gradient and diagonalizes the Hamiltonian in that basis, without optimizing any angle.",
          "From the Hartree Fock state, each iteration adds basis states from the excitation with the largest energy gradient and diagonalizes the Hamiltonian in that basis, without optimizing any angle."),
        S("On a stretched H4 chain, where CCSD lies 18 millihartree below the exact energy, it reaches that exact energy, the full CI value, in eight iterations.",
          "On a stretched H four chain, where C C S D lies 18 milli-hartree below the exact energy, it reaches that exact energy, the full C I value, in eight iterations."),
        S("Every matrix element here was computed exactly from state vectors. With exact outcome probabilities, running the same eight iterations as circuits would execute 47,352 of them."),
        S("The Result stores every matrix element, so the cutoff for nearly dependent basis directions can be changed without new evaluations."),
        S("Its report calls the energy a projected estimate that does not establish the ground state, which the full CI reference confirms here.",
          "Its report calls the energy a projected estimate that does not establish the ground state, which the full C I reference confirms here."),
    ]),
    ("others", [
        S("The other methods use the same workflow. LCHS solves linear differential equations with a constant matrix and source, such as a pulse carried by a flow or a heated rod whose ends a penalty holds cold."),
        S("Dalzell's shortcut returns the direction of a linear-system solution, shown on a two-step collision history from a lattice Boltzmann fluid model.",
          "[Dalzell](/dælzˈɛl/)'s shortcut returns the direction of a linear-system solution, shown on a two-step collision history from a lattice [Boltzmann](/bˈOltsmən/) fluid model."),
        S("Chebyshev Lanczos and four phase-estimation methods, including QCELS, estimate energies of molecular, spin or lattice Hamiltonians from an initial state that overlaps the ground state.",
          "[Chebyshev](/ʧˈɛbɪʃɛf/) [Lanczos](/lˈɑnʦOʃ/) and four phase-estimation methods, including Q C E L S, estimate energies of molecular, spin or lattice Hamiltonians from an initial state that overlaps the ground state."),
        S("Quantum Hamiltonian descent searches for the minimum of a function of a few variables over a box, and the expectation method measures observables written as Pauli sums.",
          "Quantum Hamiltonian descent searches for the minimum of a function of a few variables over a box, and the expectation method measures observables written as [Pauli](/pˈWli/) sums."),
        S("QSVT, block encodings, LCHS, Dalzell's shortcut, Chebyshev Lanczos and quantum Hamiltonian descent also exist in other packages, such as PennyLane, Qrisp, Qualtran, Classiq and QHDOPT. For these, what sets NWQLib apart is the workflow around them.",
          "Q S V T, block encodings, L C H S, [Dalzell](/dælzˈɛl/)'s shortcut, [Chebyshev](/ʧˈɛbɪʃɛf/) [Lanczos](/lˈɑnʦOʃ/) and quantum Hamiltonian descent also exist in other packages, such as Penny Lane, [Qrisp](/kɹˈɪsp/), [Qualtran](/kwˈɔltɹæn/), Classiq and Q H D opt. For these, what sets N W Q Lib apart is the workflow around them."),
    ]),
    ("running", [
        S("Circuits run locally on Aer, or on CPUs with NWQ-Sim. Adapters for IBM Runtime, IonQ and Quantinuum Nexus have passed offline checks, and runs on live hardware have not been qualified.",
          "Circuits run locally on [Aer](/ˈɛɹ/), or on CPUs with N W Q Sim. Adapters for I B M Runtime, Ion Q and [Quantinuum](/kwˌɑntɪnˈuəm/) Nexus have passed offline checks, and runs on live hardware have not been qualified."),
        S("Each method guide maps the implemented steps to their paper equations and to the functions that compute them."),
    ]),
    ("scope", [
        S("The example notebooks simulate at most twelve qubits, and dense matrices serve only small systems."),
        S("For QLS, a Pauli-sum A needs a condition-number bound from you, and Dalzell's shortcut needs an estimate of the solution norm.",
          "For Q L S, a [Pauli](/pˈWli/)-sum A needs a condition-number bound from you, and [Dalzell](/dælzˈɛl/)'s shortcut needs an estimate of the solution norm."),
        S("Time-dependent LCHS, error bounds for the physical output of GCIM, and validation on hardware are open work."),
    ]),
    ("close", [
        S("With NWQLib, you state a scientific problem and get a quantum algorithm's result with its estimated circuit cost and the evidence behind it."),
    ]),
]
