"""Narration for the ADAPT-GCIM explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words.
Numbers trace to npj Quantum Inf. 10, 127 (2024), Tables 1-3 and the main text, and to the
abstract of Phys. Rev. Research 5, 023200 (2023) for the earlier generator coordinate paper.
"""

SEGMENTS = [
    ("problem", [
        dict(text="A variational quantum eigensolver, or VQE, finds a molecule's ground-state energy by tuning circuit parameters to minimize the measured energy.",
             say="A variational quantum eigensolver, or V Q E, finds a molecule's ground-state energy by tuning circuit parameters to minimize the measured energy."),
        dict(text="That search is a constrained optimization, and an inexact ansatz, local minima, or barren plateaus can stop it short of the true ground state."),
    ]),
    ("gcm", [
        dict(text="An earlier paper from the same team, on quantum algorithms for generator coordinate methods, took a different route."),
        dict(text="It prepares generating functions, a reference state acted on by low-depth circuits, and measures the Hamiltonian and overlap matrices between them."),
        dict(text="Solving the resulting Hill–Wheeler equation, a generalized eigenvalue problem, gives ground- and excited-state energies in one step instead of an iterative optimization.",
             say="Solving the resulting Hill Wheeler equation, a generalized eigenvalue problem, gives ground- and excited-state energies in one step, instead of an iterative optimization."),
    ]),
    ("toy", [
        dict(text="A two-electron toy model shows why this helps."),
        dict(text="Two Givens rotations reach four electronic configurations, but a VQE ansatz built from them has only two free parameters.",
             say="Two Givens rotations reach four electronic configurations, but a V Q E ansatz built from them has only two free parameters."),
        dict(text="The generator coordinate inspired method, GCIM, applies the same rotations separately and together, giving four generating functions whose span contains the target state.",
             say="The generator coordinate inspired method, G C I M, applies the same rotations separately and together, giving four generating functions whose span contains the target state."),
        dict(text="With the same rotations, the lowest GCIM eigenvalue is never above the best VQE energy.",
             say="With the same rotations, the lowest G C I M eigenvalue is never above the best V Q E energy."),
    ]),
    ("choose", [
        dict(text="Choosing the generating functions is the hard part."),
        dict(text="Every product of K rotations gives 2^K functions, and the original method relied on prior knowledge of the molecule to choose them.",
             say="Every product of K rotations gives two to the K functions, and the original method relied on prior knowledge of the molecule to choose them."),
    ]),
    ("adapt", [
        dict(text="ADAPT-GCIM makes the choice automatic.",
             say="Adapt G C I M makes the choice automatic."),
        dict(text="Each iteration selects the unitary coupled cluster excitation with the largest energy gradient, evaluated on a surrogate state whose rotation angle stays fixed."),
        dict(text="The selected operator adds two generating functions, so the basis grows linearly, and a generalized eigenvalue problem returns the energy."),
        dict(text="No circuit parameter is optimized along the way."),
    ]),
    ("results", [
        dict(text="The tests covered four molecules in seven geometries: H4, LiH, BeH2, and H6.",
             say="The tests covered four molecules in seven geometries: H four, lithium hydride, beryllium hydride, and H six."),
        dict(text="For H6 stretched to 5 Å, a strongly correlated case, ADAPT-GCIM reached an error of 9.6 × 10⁻⁸ hartree in 37 iterations, while ADAPT-VQE needed 84 iterations to reach 1.2 × 10⁻⁶.",
             say="For H six stretched to five angstroms, a strongly correlated case, adapt G C I M reached an error of nine point six times ten to the minus eight hartree in 37 iterations, while adapt V Q E needed 84 iterations to reach one point two times ten to the minus six."),
        dict(text="On the same laptop, energy evaluations took 12 seconds for ADAPT-GCIM and about three and a half hours for ADAPT-VQE, which also ran 11,313 optimization rounds.",
             say="On the same laptop, energy evaluations took 12 seconds for adapt G C I M, and about three and a half hours for adapt V Q E, which also ran 11,313 optimization rounds."),
    ]),
    ("costs", [
        dict(text="GCIM needs more measurements per iteration, because the Hamiltonian and overlap matrices grow with the square of the number of generating functions, and a nearly singular overlap matrix has to be regularized.",
             say="G C I M needs more measurements per iteration, because the Hamiltonian and overlap matrices grow with the square of the number of generating functions, and a nearly singular overlap matrix has to be regularized."),
        dict(text="For weakly correlated molecules it can also need more iterations than ADAPT-VQE, and a variant with a few short optimization rounds, ADAPT-GCIM(5,2), used fewer iterations than ADAPT-VQE on both H6 geometries where it was tested.",
             say="For weakly correlated molecules it can also need more iterations than adapt V Q E, and a variant with a few short optimization rounds, adapt G C I M five two, used fewer iterations than adapt V Q E on both H six geometries where it was tested."),
        dict(text="A first test on IBM's ibm_osaka for linear H4 reduced the ground-state energy error from 0.046 to 3.9 × 10⁻⁹ hartree with problem-specific error mitigation.",
             say="A first test on I B M's Osaka processor for linear H four reduced the ground-state energy error from zero point zero four six to three point nine times ten to the minus nine hartree, with problem-specific error mitigation."),
    ]),
    ("link", [
        dict(text="The same solver later found the ground states of downfolded Hamiltonians for benzene and porphyrin in the coupled cluster downfolding study."),
    ]),
    ("close", [
        dict(text="By replacing constrained optimization with a generalized eigenvalue problem over adaptively chosen generating functions, ADAPT-GCIM removed the parameter optimization behind most of ADAPT-VQE's run time in these tests.",
             say="By replacing constrained optimization with a generalized eigenvalue problem over adaptively chosen generating functions, adapt G C I M removed the parameter optimization behind most of adapt V Q E's run time in these tests."),
    ]),
]
