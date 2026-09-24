"""Narration for the coupled cluster downfolding explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words.
Numbers trace to Phys. Rev. Research 8, 013072 (2026), Tables II-V and Sec. IV.
"""

SEGMENTS = [
    ("problem", [
        dict(text="Predicting chemistry accurately means capturing electron correlation, and that requires large basis sets."),
        dict(text="Benzene in the cc-pVTZ basis has 264 orbitals, and free-base porphyrin in cc-pVDZ has 406, far beyond what current quantum hardware can simulate at the required accuracy.",
             say="Benzene in the C C P V T Z basis has 264 orbitals, and free-base porphyrin in C C P V D Z has 406, far beyond what current quantum hardware can simulate at the required accuracy."),
    ]),
    ("active", [
        dict(text="The common shortcut keeps a small active space, here six electrons in six orbitals, and ignores everything outside it."),
        dict(text="Most of the correlation energy, however, comes from the many virtual orbitals left out."),
        dict(text="Within that active space, CCSD(T) recovers about 3 percent of the benzene correlation energy and under 1 percent for porphyrin.",
             say="Within that active space, C C S D T recovers about 3 percent of the benzene correlation energy, and under 1 percent for porphyrin."),
    ]),
    ("downfold", [
        dict(text="Coupled cluster downfolding keeps the small active space but changes its Hamiltonian."),
        dict(text="The double unitary coupled cluster ansatz writes the ground state with an external operator, which reaches outside the active space, and an internal operator that stays within it."),
        dict(text="Transforming the full Hamiltonian with the external operator and projecting onto the active space gives an effective Hamiltonian, whose lowest eigenvalue reproduces the energy of the whole system when the external operator is exact."),
    ]),
    ("build", [
        dict(text="In practice, the external operator comes from classical CCSD amplitudes, and the transformation is truncated to a few commutators with one- and two-body terms.",
             say="In practice, the external operator comes from classical C C S D amplitudes, and the transformation is truncated to a few commutators, with one- and two-body terms."),
        dict(text="The resulting expressions span just over 1000 diagrams, generated automatically and evaluated on GPU supercomputers with the ExaChem code.",
             say="The resulting expressions span just over 1000 diagrams, generated automatically and evaluated on G P U supercomputers with the [ExaChem](/ˈɛksəkˌɛm/) code."),
    ]),
    ("solve", [
        dict(text="Six electrons in six orbitals fit on twelve qubits."),
        dict(text="In noiseless simulations, four solvers found the ground state of the downfolded Hamiltonian: ADAPT-VQE, qubit-ADAPT-VQE, ADAPT-GCIM, and a generalized unitary coupled cluster VQE.",
             say="In noiseless simulations, four solvers found the ground state of the downfolded Hamiltonian: adapt V Q E, qubit adapt V Q E, adapt G C I M, and a generalized unitary coupled cluster V Q E."),
        dict(text="For benzene and porphyrin, all four matched exact diagonalization to within 0.1 millihartree, and for stretched nitrogen, ADAPT-GCIM(2,2) and the generalized unitary coupled cluster ansatz came closest.",
             say="For benzene and porphyrin, all four matched exact diagonalization to within zero point one millihartree, and for stretched nitrogen, adapt G C I M two two, and the generalized unitary coupled cluster ansatz came closest."),
    ]),
    ("hardware", [
        dict(text="On hardware, qubit-ADAPT-VQE circuits with classically optimized parameters ran on Quantinuum's H1-1 trapped-ion computer and on IBM's Marrakesh and Kingston processors.",
             say="On hardware, qubit adapt V Q E circuits with classically optimized parameters ran on Quantinuum's H 1 1 trapped-ion computer, and on I B M's [Marrakesh](/mˌæɹəkˈɛʃ/) and Kingston processors."),
        dict(text="To fit the measurement budget, only the largest groups of Hamiltonian terms were measured, which adds 0.4 millihartree of error for benzene and 5.9 for porphyrin.",
             say="To fit the measurement budget, only the largest groups of Hamiltonian terms were measured, which adds zero point four millihartree of error for benzene, and five point nine for porphyrin."),
        dict(text="On H1-1, zero-noise extrapolation reran each circuit at noise factors of three and five, then fitted a line back to zero noise.",
             say="On H 1 1, zero-noise extrapolation reran each circuit at noise factors of three and five, then fitted a line back to zero noise."),
    ]),
    ("results", [
        dict(text="With zero-noise extrapolation, H1-1 gave −231.789 hartree for benzene and −986.749 hartree for porphyrin.",
             say="With zero-noise extrapolation, H 1 1 gave minus 231 point 7 8 9 hartree for benzene, and minus 986 point 7 4 9 hartree for porphyrin."),
        dict(text="These lie 17 and 70 millihartree above the CCSD(T) targets and recover about 98 percent of the CCSD(T) correlation energy, compared with 3 percent and under 1 percent from the bare active space.",
             say="These lie 17 and 70 millihartree above the C C S D T targets, and recover about 98 percent of the C C S D T correlation energy, compared with 3 percent and under 1 percent from the bare active space."),
    ]),
    ("amplify", [
        dict(text="Almost all hardware estimates also lie well below the CCSD energy whose amplitudes were used to build the effective Hamiltonian.",
             say="Almost all hardware estimates also lie well below the C C S D energy, whose amplitudes were used to build the effective Hamiltonian."),
        dict(text="The paper calls this accuracy amplification, a sign that the downfolded Hamiltonian captures correlation from outside the active space."),
    ]),
    ("close", [
        dict(text="Because the active space can grow with the hardware, downfolding lets the problem size match the available qubits, and the authors see such hybrid methods as a bridge from today's noisy devices to fault-tolerant quantum chemistry."),
    ]),
]
