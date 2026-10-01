"""Narration for the NWQLib (Northwest Quantum Library) explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words. `S` fills it in from SPOKEN.

Sources, all in the NWQLib repository at the commit recorded in data.json:
- plate, workflow, plan, estimate, solve: examples/qls_linear_system_intro.ipynb (the result card,
  Sections 2 and 3, Go deeper A and D, Appendix B) and docs/algorithms/qls.md, recomputed in data.json.
- scale: examples/resource_estimation_at_scale.ipynb (the overview cell, the compiled checks and
  Section 1) and the section "Plan and estimate beyond simulation" of docs/algorithms/qls.md,
  recomputed in data.json.
- methods: README.md ("Algorithms"), examples/README.md and `python -m nwqlib algorithms`.
- get: README.md ("Installation" and "Backend support") and LICENSE.
"""

# Slightly faster than the series default (tts.SPEED), chosen by the author for this video.
SPEED = 1.12
NBSP = "\u00a0"  # keeps a term on one subtitle line

SPOKEN = {
    "NWQLib": "N W Q Lib",
    "NWQ-Sim": "N W Q Sim",
    "GCiM": "G C I M",
    "QCELS": "Q C E L S",
    "RWPE": "R W P E",
    "SPE": "S P E",
    "RFE": "R F E",
    "LCHS": "L C H S",
    "QLS": "Q L S",
    "CX": "C X",
    "BSD": "B S D",
    "PyPI": "pie P I",
    "IonQ": "Ion Q",
    "NumPy": "num pie",
    "Aer": "[Aer](/ˈɛɹ/)",
    "Qiskit": "[Qiskit](/kˈɪskɪt/)",
    "Quantinuum": "[Quantinuum](/kwˌɑntɪnˈuəm/)",
    "Dalzell": "[Dalzell](/dælzˈɛl/)",
    "Pauli": "[Pauli](/pˈWli/)",
    "Chebyshev": "[Chebyshev](/ʧˈɛbɪʃɛf/)",
    "Lanczos": "[Lanczos](/lˈɑnʦOʃ/)",
    "ancillas": "[ancillas](/ænsˈɪləz/)",
    "Ax = b": "A x equals b",
    "Poisson": "[Poisson](/pwɑsˈOn/)",
}


def S(text, say=None):
    spoken = say or text.replace(NBSP, " ")
    if say is None:
        for word, sound in SPOKEN.items():
            spoken = spoken.replace(word, sound)
    return dict(text=text, say=spoken) if spoken != text else dict(text=text)


SEGMENTS = [
    ("plate", [
        S("A metal plate with cold edges is warmed by two heaters. On a four-by-four grid, its steady temperature solves a linear system, Ax = b, with sixteen unknowns."),
        S("A quantum solver based on singular value transformation needs a circuit that prepares b, a block encoding of A, a polynomial that approximates the inverse, and the phase angles that apply this polynomial. The solver then outputs the solution as a normalized quantum state."),
    ]),
    ("workflow", [
        S("NWQLib, the Northwest Quantum Library from Pacific Northwest National Laboratory, builds these pieces from A and b and returns x with its physical scale and phase."),
        S("You state the problem and choose QLS, the quantum linear solver, with an accuracy. Then plan selects the construction, estimate counts its gates, and solve runs it."),
    ]),
    ("plan", [
        S("For the plate, plan chose a Pauli block encoding with normalization α = 8.",
          "For the plate, plan chose a [Pauli](/pˈWli/) block encoding with normalization alpha equal to 8."),
        S("It places the eigenvalues of A/α between 0.095 and 0.905, so the encoded condition number κ, one over the smallest of them, is 10.5.",
          "It places the eigenvalues of A over alpha between 0 point 0 9 5 and 0 point 9 0 5, so the encoded condition number kappa, one over the smallest of them, is 10 point 5."),
        S("Next, plan selected an odd polynomial of degree 59 that matches 1/(κx) to a relative error of one percent on the interval from 1/κ to 1, which holds every eigenvalue.",
          "Next, plan selected an odd polynomial of degree 59 that matches one over kappa x to a relative error of one percent on the interval from one over kappa to one, which holds every eigenvalue."),
        S("From the polynomial it computed sixty phase\u00a0angles for a nine-qubit circuit. Four qubits hold the sixteen temperatures, and five are ancillas."),
    ]),
    ("estimate", [
        S("Before any circuit existed, estimate added up the gate count that each block's formula gives and predicted 7,846 CX gates."),
        S("At optimization level 1, Qiskit compiled the circuit to 7,710."),
        S("Every count is labeled as exact, an upper bound or an estimate, and a quantity that no formula covers, such as the circuit depth, is reported as unavailable."),
    ]),
    ("solve", [
        S("The call to solve simulated the circuit on Qiskit's\u00a0Aer\u00a0simulator and read every amplitude exactly. It kept the branch in which the ancillas signal success, which has probability 0.16, and restored the physical scale.",
          "The call to solve simulated the circuit on [Qiskit](/kˈɪskɪt/)'s [Aer](/ˈɛɹ/) simulator and read every amplitude exactly. It kept the branch in which the [ancillas](/ænsˈɪləz/) signal success, which has probability 0 point 1 6, and restored the physical scale."),
        S("The result is the temperature field itself, with a relative\u00a0error of 0.91 percent against NumPy's direct solve, within the one-percent error allowance of the selected polynomial.",
          "The result is the temperature field itself, with a relative error of 0 point 9 1 percent against num pie's direct solve, within the one-percent error allowance of the selected polynomial."),
        S("With finite shots, as on hardware, solve returns quantities such as a quadratic form of x instead of the vector."),
        S("The result keeps its plan, so it can be checked, saved and reloaded without running the circuit again."),
    ]),
    ("scale", [
        S("When A and b come in a compact form, such\u00a0as a periodic\u00a0stencil and a product state, plan and estimate work at sizes that no state-vector simulator can hold."),
        S("For a screened Poisson equation on a ring of 2¹⁰⁰ sites, plan chose a banded block encoding with κ = 2 and a polynomial of degree 11.",
          "For a screened [Poisson](/pwɑsˈOn/) equation on a ring of two to the hundredth sites, plan chose a banded block encoding with kappa equal to 2 and a polynomial of degree 11."),
        S("The estimate is 225,734 CX gates per attempt on 104 qubits, and the two calls took under a tenth of a second on a laptop.",
          "The estimate is 225,734 C X gates per attempt on 104 qubits, and the two calls took under a tenth of a second on a laptop."),
        S("On this ring, at five sizes between four and sixteen system qubits, the predicted count equals the CX\u00a0count of the compiled circuit before optimization."),
        S("A state vector of 104 qubits would need about 3 × 10³² bytes. These counts are logical, without noise or error correction.",
          "A state vector of 104 qubits would need about 3 times 10 to the 32 bytes. These counts are logical, without noise or error correction."),
    ]),
    ("methods", [
        S("The other methods use the same workflow. QLS also offers Dalzell's\u00a0shortcut, which returns the direction of x, and LCHS solves linear\u00a0differential\u00a0equations with a constant matrix and source."),
        S("For eigenvalues such as ground-state energies, NWQLib offers Chebyshev Lanczos, fixed and adaptive GCiM, and four phase-estimation methods, including QCELS."),
        S("Quantum Hamiltonian descent searches for the minimum of a function over a box, with an augmented Lagrangian for constraints. The expectation method computes expectation\u00a0values of observables written as Pauli sums."),
        S("Example notebooks solve complete problems with most of these methods, and one notebook plans five method families at up to one hundred qubits."),
    ]),
    ("get", [
        S("Circuits run locally on Aer or NWQ-Sim. Adapters for IBM Runtime, IonQ and Quantinuum Nexus have passed offline checks, and runs on live hardware are not yet qualified.",
          "Circuits run locally on [Aer](/ˈɛɹ/) or N W Q Sim. Adapters for I B M Runtime, Ion Q and [Quantinuum](/kwˌɑntɪnˈuəm/) Nexus have passed offline checks, and runs on live hardware are not yet qualified."),
        S("NWQLib is open source under the BSD 2-Clause license. Install it from PyPI with pip, and find the documentation and examples on GitHub."),
    ]),
    ("close", [
        S("With NWQLib, you state a scientific problem, see a quantum\u00a0algorithm's estimated resources before any circuit is built, and get its answer with the evidence behind it."),
    ]),
]
