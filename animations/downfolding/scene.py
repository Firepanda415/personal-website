"""Explainer for "Coupled cluster downfolding theory in simulations of correlated systems on
quantum hardware" (Bauman, Zheng, et al., Phys. Rev. Research 8, 013072, 2026).

Energies are quoted from Tables II-V of the paper. The zero-noise-extrapolation points are
the measured H1-1 energies and variances from ZNE_plots_combine.ipynb in the Downfolding_VQE
repository (commit a137719), whose weighted linear fits reproduce Table V.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

CLASSICAL = GOLD
QUANTUM = DV

# Correlation energies (hartree), Table III: bare (6e, 6o) CCSD(T), H1-1 qubit-ADAPT-VQE, full CCSD(T).
CORRELATION = {"benzene": (0.031, 1.010, 1.027), "porphyrin": (0.033, 3.433, 3.503)}

# H1-1 energies at noise factors 1, 3, 5 (hartree) and their variances.
ZNE = {
    "benzene": dict(y=[-231.76064319007415, -231.7161734989753, -231.6576865799007],
                    var=[7.727866644371047e-05, 6.373443768082147e-05, 0.00010008416715273546],
                    noiseless=-231.7829, window=(-231.80, -231.64)),
    "porphyrin": dict(y=[-986.7431548924477, -986.7327677033621, -986.7205140249462],
                      var=[1.547613251088589e-05, 2.0730228253183782e-05, 2.9152107446148764e-05],
                      noiseless=-986.7608, window=(-986.77, -986.71)),
}

# Table V: every emulator and hardware estimate, with the CCSD source and CCSD(T) target.
ESTIMATES = {
    "benzene": dict(ccsd=-231.7537, target=-231.8058, window=(-231.82, -231.74), points=[
        ("H1-1 emulator", -231.7572, 0.0064), ("H1-1", -231.7606, 0.0088), ("emulator + ZNE", -231.7652, 0.0054),
        ("H1-1 + ZNE", -231.7887, 0.0072), ("Marrakesh + QESEM", -231.7810, 0.0259)]),
    "porphyrin": dict(ccsd=-986.6465, target=-986.8192, window=(-986.84, -986.62), points=[
        ("H1-1 emulator", -986.7495, 0.0037), ("H1-1", -986.7431, 0.0039), ("emulator + ZNE", -986.7535, 0.0030),
        ("H1-1 + ZNE", -986.7490, 0.0008), ("Kingston + QESEM", -986.7369, 0.0171)]),
}


def num(v, spec=".4f"):
    """Format a signed number with a typographic minus sign."""
    return format(v, spec).replace("-", "\u2212")


def wls(x, y, var):
    """Weighted least-squares line, as in the paper's ZNE fits; returns intercept, slope, intercept SE."""
    x, y, w = np.asarray(x, float), np.asarray(y), 1 / np.asarray(var)
    X = np.c_[np.ones_like(x), x]
    A = X.T @ (w[:, None] * X)
    beta = np.linalg.solve(A, X.T @ (w * y))
    scale = (w * (y - X @ beta) ** 2).sum() / (len(x) - 2)
    return beta[0], beta[1], np.sqrt(scale * np.linalg.inv(A)[0, 0])


def benzene_icon(r=0.55):
    ring = RegularPolygon(6, radius=r, color=INK, stroke_width=3).rotate(PI / 6)
    return VGroup(ring, Circle(radius=0.58 * r, color=INK, stroke_width=2.5))


def porphyrin_icon(r=0.62):
    macro = Circle(radius=r, color=INK, stroke_width=3)
    rings = VGroup(*[RegularPolygon(5, radius=0.2, color=INK, stroke_width=2.5, fill_color=PAPER, fill_opacity=1)
                     .rotate(a + PI / 2).move_to(r * np.array([np.cos(a), np.sin(a), 0])) for a in np.arange(4) * PI / 2])
    return VGroup(macro, rings)


def ladder(n, n_occ, height, width=1.9, stroke=1.2):
    """Evenly spaced orbital levels, occupied ones darker."""
    ys = np.linspace(-height / 2, height / 2, n)
    return VGroup(*[Line([-width / 2, y, 0], [width / 2, y, 0], stroke_width=stroke,
                         color=INK if i < n_occ else MUTED, stroke_opacity=0.9 if i < n_occ else 0.55)
                    for i, y in enumerate(ys)])


def value_axis(window, height, x, label_values):
    lo, hi = window
    axis = NumberLine(x_range=[lo, hi, (hi - lo) / 4], length=height, rotation=PI / 2, color=MUTED,
                      stroke_width=2, include_ticks=False).move_to([x, 0, 0])
    labels = VGroup(*[T(num(v, ".2f"), 15, MUTED).next_to(axis.n2p(v), LEFT, buff=0.12) for v in label_values])
    return axis, labels


class DownfoldingExplainer(Explainer):
    timing_file = BUILD / "downfolding" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.active_space()
        self.downfold()
        self.build_heff()
        self.solvers()
        self.hardware()
        self.results()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("Physical Review Research 8, 013072 · 2026")
        title = VGroup(T("Coupled cluster downfolding theory", 44, weight=MEDIUM),
                       T("in simulations of correlated systems", 44, weight=MEDIUM),
                       T("on quantum hardware", 44, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = VGroup(T("Nicholas P. Bauman*, Muqing Zheng*, Chenxu Liu, Nathan M. Myers, Ajay Panyala,", 22, MUTED),
                         T("Bo Peng, Ang Li, Karol Kowalski", 22, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        places = T("Pacific Northwest National Laboratory · University of Washington      * equal contribution", 18, MUTED)
        block = VGroup(venue, title, authors, places).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        places.next_to(authors, DOWN, buff=0.15, aligned_edge=LEFT)
        block.move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(block.get_corner(UL) + 0.35 * UP, block.get_corner(UL) + 0.35 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        self.play(Create(rule), FadeIn(venue, shift=0.1 * RIGHT), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in (title, authors, places)], lag_ratio=0.25), run_time=1.6)
        self.wait(2.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 01
    def problem(self):
        head = header(1, "Correlation needs large basis sets")
        cols = []
        for x, icon, name, basis, n, n_occ in [(-3.8, benzene_icon(), "benzene", "cc-pVTZ", 264, 21),
                                               (3.8, porphyrin_icon(), "free-base porphyrin", "cc-pVDZ", 406, 81)]:
            icon.move_to([x, 2.35, 0])
            label = VGroup(T(name, 24, INK, weight=MEDIUM), T(basis, 20, MUTED)).arrange(DOWN, buff=0.08).next_to(icon, DOWN, buff=0.25)
            lad = ladder(n, n_occ, 3.6, stroke=1.0).move_to([x, -1.2, 0])
            count = T(f"{n} orbitals", 24, ACCENT, weight=MEDIUM).next_to(lad, RIGHT, buff=0.3)
            cols.append((icon, label, lad, count))
        legend = VGroup(VGroup(Line(ORIGIN, 0.5 * RIGHT, color=INK, stroke_width=3), T("occupied", 18, INK)).arrange(RIGHT, buff=0.15),
                        VGroup(Line(ORIGIN, 0.5 * RIGHT, color=MUTED, stroke_width=3), T("virtual", 18, MUTED)).arrange(RIGHT, buff=0.15)
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -0.2, 0])
        qubits = VGroup(T("Jordan–Wigner mapping:", 18, MUTED), T("one qubit per spin orbital", 18, MUTED)).arrange(DOWN, buff=0.08).move_to([0, -2.6, 0])

        with self.voice("problem") as v:
            self.play(FadeIn(head), *[FadeIn(c[0], scale=0.8) for c in cols], *[FadeIn(c[1]) for c in cols], run_time=1.4)
            v.until(1)
            for icon, label, lad, count in cols:
                self.play(LaggedStart(*[Create(l) for l in lad], lag_ratio=0.004), run_time=1.6)
                self.play(FadeIn(count, shift=0.1 * LEFT), run_time=0.5)
            self.play(FadeIn(legend), FadeIn(qubits), run_time=0.8)
        self.problem_mobs = dict(head=head, cols=cols, rest=VGroup(legend, qubits))

    # ------------------------------------------------------------------ 02
    def active_space(self):
        o = self.problem_mobs
        head = header(2, "The bare active space")
        n_show, spacing = 16, 0.27
        ys = (np.arange(n_show) - (n_show - 1) / 2) * spacing - 0.3
        levels = VGroup(*[Line([-1.1, y, 0], [1.1, y, 0], stroke_width=2.5, color=INK if i < 8 else MUTED)
                          for i, y in enumerate(ys)]).shift(3.9 * LEFT)
        electrons = VGroup(*[VGroup(Dot(levels[i].get_center() + 0.12 * LEFT, radius=0.05, color=INK),
                                    Dot(levels[i].get_center() + 0.12 * RIGHT, radius=0.05, color=INK)) for i in range(8)])
        more_up = T("235 more virtual orbitals", 18, MUTED).next_to(levels, UP, buff=0.3)
        more_dn = T("13 more occupied orbitals", 18, MUTED).next_to(levels, DOWN, buff=0.3)
        window = SurroundingRectangle(levels[5:11], color=ACCENT, buff=0.12, stroke_width=3)
        win_lab = VGroup(T("(6e, 6o) active space", 22, ACCENT, weight=MEDIUM), T("12 qubits", 20, ACCENT)).arrange(DOWN, buff=0.08)
        win_lab.next_to(window, RIGHT, buff=0.35)
        outside = VGroup(*levels[:5], *levels[11:], *electrons[:5])
        dyn = Brace(VGroup(*levels[11:]), RIGHT, color=MUTED)
        dyn_lab = VGroup(T("most of the correlation", 18, INK), T("energy comes from here", 18, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).next_to(dyn, RIGHT, buff=0.12)
        chart_title = T("correlation energy (hartree)", 22, INK, weight=MEDIUM).move_to([3.3, 2.2, 0])
        per = 4.0 / 3.503
        rows = VGroup()
        for i, (name, (bare, _, full)) in enumerate(CORRELATION.items()):
            y0 = 1.3 - 1.9 * i
            lab = T(name, 22, INK, weight=MEDIUM).move_to([0.9, y0 + 0.35, 0], aligned_edge=LEFT)
            full_bar = Rectangle(width=full * per, height=0.24, stroke_width=0, fill_color=INK, fill_opacity=0.85).move_to([0.9, y0 - 0.05, 0], aligned_edge=LEFT)
            bare_bar = Rectangle(width=max(bare * per, 0.03), height=0.24, stroke_width=0, fill_color=ACCENT, fill_opacity=1).move_to([0.9, y0 - 0.45, 0], aligned_edge=LEFT)
            full_val = T(f"{full:.3f}  full CCSD(T)", 17, INK).next_to(full_bar, RIGHT, buff=0.12)
            share = "about 3%" if name == "benzene" else "under 1%"
            bare_val = T(f"{bare:.3f}  (6e, 6o) CCSD(T), {share}", 17, ACCENT).next_to(bare_bar, RIGHT, buff=0.12)
            rows.add(VGroup(lab, full_bar, full_val, bare_bar, bare_val))

        with self.voice("active") as v:
            benz = o["cols"][0]
            self.play(FadeOut(VGroup(*[m for c in o["cols"][1:] for m in c], o["rest"], benz[0], benz[3])),
                      ReplacementTransform(o["head"], head), ReplacementTransform(benz[2], levels),
                      benz[1].animate.scale(0.8).next_to(more_up, UP, buff=0.15), run_time=1.4)
            self.play(FadeIn(electrons), FadeIn(more_up), FadeIn(more_dn), run_time=0.8)
            self.play(Create(window), FadeIn(win_lab), outside.animate.set_opacity(0.3), run_time=1.2)
            v.until(1)
            self.play(outside.animate.set_opacity(1), FadeIn(dyn), FadeIn(dyn_lab), run_time=1.2)
            v.until(2)
            self.play(FadeIn(chart_title), run_time=0.5)
            for r in rows:
                self.play(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2]), GrowFromEdge(r[3], LEFT), FadeIn(r[4]), run_time=1.1)
        self.active_mobs = dict(head=head, levels=levels, electrons=electrons, window=window, win_lab=win_lab,
                                more=VGroup(more_up, more_dn, benz[1]), rest=VGroup(dyn, dyn_lab, chart_title, rows))

    # ------------------------------------------------------------------ 03
    def downfold(self):
        o = self.active_mobs
        head = header(3, "Coupled cluster downfolding")
        levels, window = o["levels"], o["window"]
        ansatz = M('ket(Psi) = e^(#c("' + CLASSICAL + '", $sigma_"ext"$)) e^(#c("' + ACCENT + '", $sigma_"int"$)) ket(Phi)', 1.35).move_to([2.6, 2.3, 0])
        ext_lab = T("external: reaches outside the active space", 19, CLASSICAL).move_to([2.6, 1.45, 0])
        int_lab = T("internal: stays within the active space", 19, ACCENT).next_to(ext_lab, DOWN, buff=0.12)
        heff = M('H^"eff" = (P + Q_"int") thin e^(-#c("' + CLASSICAL + '", $sigma_"ext"$)) H e^(#c("' + CLASSICAL + '", $sigma_"ext"$)) (P + Q_"int")', 1.1).move_to([2.6, -0.3, 0])
        heff_note = VGroup(T("lowest eigenvalue = energy of the whole system", 19, INK),
                           T("when the external operator is exact", 19, MUTED)).arrange(DOWN, buff=0.08).next_to(heff, DOWN, buff=0.35)

        def excite(i, j, color, bend):
            return CurvedArrow(levels[i].get_right() + 0.05 * RIGHT, levels[j].get_right() + 0.05 * RIGHT, angle=bend,
                               color=color, stroke_width=2.5, tip_length=0.12)
        ext_arrows = VGroup(excite(6, 13, CLASSICAL, -1.2), excite(7, 15, CLASSICAL, -1.3), excite(2, 9, CLASSICAL, -1.1))
        int_arrows = VGroup(*[CurvedArrow(levels[i].get_left() + 0.05 * LEFT, levels[j].get_left() + 0.05 * LEFT, angle=1.4,
                                          color=ACCENT, stroke_width=2.5, tip_length=0.12) for i, j in [(7, 8), (6, 9)]])
        fold = VGroup(*[levels[k] for k in (*range(0, 5), *range(11, 16))])
        block = RoundedRectangle(corner_radius=0.08, width=window.width, height=window.height, stroke_width=3,
                                 stroke_color=ACCENT, fill_color=ACCENT, fill_opacity=0.12).move_to(window)
        block_lab = M('H^"eff"', 1.0, ACCENT).next_to(block, LEFT, buff=0.3)

        with self.voice("downfold") as v:
            self.play(FadeOut(o["rest"]), FadeOut(o["win_lab"]), ReplacementTransform(o["head"], head), run_time=0.8)
            self.play(Indicate(window, color=ACCENT, scale_factor=1.04), run_time=1.0)
            v.until(1)
            self.play(Write(ansatz), run_time=1.6)
            self.play(LaggedStart(*[Create(a) for a in ext_arrows], lag_ratio=0.3), FadeIn(ext_lab), run_time=1.6)
            self.play(LaggedStart(*[Create(a) for a in int_arrows], lag_ratio=0.3), FadeIn(int_lab), run_time=1.2)
            v.until(2)
            self.play(Write(heff), run_time=2.0)
            self.play(FadeOut(ext_arrows), FadeOut(int_arrows), fold.animate.set_stroke(color=CLASSICAL, opacity=0.5), run_time=1.0)
            self.play(FadeIn(block), FadeIn(block_lab), run_time=1.0)
            self.play(FadeIn(heff_note, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def build_heff(self):
        head = header(4, "Building the effective Hamiltonian classically")
        bch = M('overline(H)_"ext" approx H + [H_N, sigma_"ext"] + 1/2 [[H_N, sigma_"ext"], sigma_"ext"] + 1/6 [[[F_N, sigma_"ext"], sigma_"ext"], sigma_"ext"]', 1.05).move_to([0, 2.1, 0])
        notes = VGroup(VGroup(M('sigma_"ext"', 0.8, CLASSICAL), T("from CCSD amplitudes", 21, CLASSICAL)).arrange(RIGHT, buff=0.12),
                       T("one- and two-body terms kept", 21, MUTED)).arrange(RIGHT, buff=0.8).next_to(bch, DOWN, buff=0.4)
        steps = [("CCSD", "external amplitudes"), ("SymGen", "just over 1000 diagrams"),
                 ("ExaChem", "GPU supercomputers"), ("Effective Hamiltonian", "(6e, 6o), public library")]
        boxes = VGroup(*[card([T(a, 24, CLASSICAL, weight=MEDIUM), T(b, 18, MUTED)], 2.7, CLASSICAL) for a, b in steps]).arrange(RIGHT, buff=0.55)
        boxes.move_to([0, -1.4, 0])
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, color=CLASSICAL, stroke_width=3,
                                max_tip_length_to_length_ratio=0.3) for i in range(3)])

        with self.voice("build") as v:
            self.play(FadeIn(head), Write(bch), run_time=2.2)
            self.play(FadeIn(notes, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            for i, b in enumerate(boxes):
                self.play(FadeIn(b, shift=0.1 * RIGHT), *([GrowArrow(arrows[i - 1])] if i else []), run_time=0.7)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def solvers(self):
        head = header(5, "Quantum solvers on the downfolded problem")
        n_q = 12
        ys = 1.9 - np.arange(n_q) * 0.33
        x0, x1 = -6.2, 0.4
        wires = VGroup(*[wire(y, x0, x1, QUANTUM, 2) for y in ys])
        q_lab = VGroup(T("12 qubits", 22, QUANTUM, weight=MEDIUM), T("(6e, 6o)", 18, QUANTUM)).arrange(DOWN, buff=0.06).next_to(wires, UP, buff=0.2).align_to(wires, LEFT)
        hf = gate('ket("HF")', 0.8, ys[0] - ys[-1] + 0.4, QUANTUM, 0.8).move_to([x0 + 0.7, ys.mean(), 0])
        spans = [(2, 7), (4, 9), (0, 5), (6, 11)]
        blocks = VGroup(*[gate(f"e^(theta_{k + 1} A_{k + 1})", 1.0, ys[a] - ys[b] + 0.35, QUANTUM, 0.75)
                          .move_to([x0 + 1.9 + 1.2 * k, (ys[a] + ys[b]) / 2, 0]) for k, (a, b) in enumerate(spans)])
        grow = T("adaptive ansatz: one operator per iteration", 18, MUTED).next_to(wires, DOWN, buff=0.25).align_to(wires, LEFT)

        names = ["ADAPT-VQE", "qubit-ADAPT-VQE", "ADAPT-GCIM", "UCCGSD VQE"]
        chips = VGroup(*[card([T(n, 20, QUANTUM, weight=MEDIUM)], 2.4, QUANTUM, pad=0.18) for n in names]).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        chips.move_to([3.9, 0.9, 0])
        chip_title = T("noiseless simulation", 20, MUTED).next_to(chips, UP, buff=0.2).align_to(chips, LEFT)

        table = VGroup(
            VGroup(T("benzene, cc-pVTZ", 20, INK, weight=MEDIUM), T("exact −231.7878", 18, MUTED), T("all four solvers −231.7878", 18, QUANTUM)),
            VGroup(T("porphyrin, cc-pVDZ", 20, INK, weight=MEDIUM), T("exact −986.7732", 18, MUTED), T("solvers −986.7731 to −986.7732", 18, QUANTUM)),
        )
        for g in table:
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        table.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([-4.2, -0.2, 0])
        errs = [("ADAPT-VQE", 0.8), ("qubit-ADAPT-VQE", 0.8), ("ADAPT-GCIM", 1.9), ("ADAPT-GCIM(2,2)", 0.2), ("UCCGSD", 0.3)]
        bars = VGroup()
        for i, (n, e) in enumerate(errs):
            y = 0.8 - 0.5 * i
            color = ACCENT if e < 0.5 else QUANTUM
            lab = T(n, 18, INK).move_to([0.4, y, 0], aligned_edge=RIGHT)
            bar = Rectangle(width=e * 1.2, height=0.26, stroke_width=0, fill_color=color, fill_opacity=0.9).move_to([0.6, y, 0], aligned_edge=LEFT)
            val = T(f"{e:.1f} mhartree", 17, color).next_to(bar, RIGHT, buff=0.1)
            bars.add(VGroup(lab, bar, val))
        bars_title = T("stretched N₂ (bond length doubled): error vs exact", 20, INK, weight=MEDIUM).next_to(bars, UP, buff=0.35).align_to(bars, LEFT)

        with self.voice("solve") as v:
            self.play(FadeIn(head), Create(wires), FadeIn(q_lab), FadeIn(hf), run_time=1.4)
            v.until(1)
            self.play(LaggedStart(*[FadeIn(b, shift=0.1 * RIGHT) for b in blocks], lag_ratio=0.4), FadeIn(grow), run_time=2.0)
            self.play(FadeIn(chip_title), LaggedStart(*[FadeIn(c, shift=0.1 * LEFT) for c in chips], lag_ratio=0.3), run_time=2.0)
            v.until(2)
            self.play(FadeOut(VGroup(wires, q_lab, hf, blocks, grow)), VGroup(chips, chip_title).animate.scale(0.8).move_to([5.4, 0.3, 0]), run_time=0.9)
            self.play(LaggedStart(*[FadeIn(g, shift=0.1 * UP) for g in table], lag_ratio=0.3), run_time=1.2)
            v.until(2, 0.5)
            self.play(FadeIn(bars_title), LaggedStart(*[GrowFromEdge(b[1], LEFT) for b in bars], lag_ratio=0.15),
                      FadeIn(VGroup(*[b[0] for b in bars])), FadeIn(VGroup(*[b[2] for b in bars])), run_time=1.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def hardware(self):
        head = header(6, "On quantum hardware")
        devices = VGroup(
            card([T("Quantinuum H1-1", 22, QUANTUM, weight=MEDIUM), T("trapped ion", 18, MUTED), T("zero-noise extrapolation", 18, INK)], 3.8, QUANTUM),
            card([T("IBM Marrakesh", 22, QUANTUM, weight=MEDIUM), T("superconducting, benzene", 18, MUTED), T("QESEM error mitigation", 18, INK)], 3.8, QUANTUM),
            card([T("IBM Kingston", 22, QUANTUM, weight=MEDIUM), T("superconducting, porphyrin", 18, MUTED), T("QESEM error mitigation", 18, INK)], 3.8, QUANTUM),
        ).arrange(RIGHT, buff=0.35).move_to([0, 1.9, 0])
        circ_note = T("qubit-ADAPT-VQE circuits, parameters optimized classically", 20, MUTED).next_to(devices, DOWN, buff=0.3)
        trunc = card([T("measured Hamiltonian terms", 22, INK, weight=MEDIUM),
                      T("benzene: 39 of 116 groups (143 of 371 Pauli strings), adds 0.4 mhartree", 19, INK),
                      T("porphyrin: 59 of 210 groups (311 of 735 Pauli strings), adds 5.9 mhartree", 19, INK)], 9.0).move_to([0, -1.3, 0])

        plots = VGroup()
        for k, (name, d) in enumerate(ZNE.items()):
            lo, hi = d["window"]
            ax = Axes(x_range=[0, 5.6, 1], y_range=[lo, hi, (hi - lo) / 4], x_length=5.4, y_length=4.0, tips=False,
                      axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-3.4 + 6.8 * k, -0.35, 0])
            b0, b1, se0 = wls([1, 3, 5], d["y"], d["var"])
            noiseless = DashedLine(ax.c2p(0, d["noiseless"]), ax.c2p(5.6, d["noiseless"]), color=MUTED, stroke_width=2, dash_length=0.08)
            nl_lab = T(f"noiseless {num(d['noiseless'])}", 15, MUTED).next_to(noiseless, UP, buff=0.05).align_to(noiseless, RIGHT)
            pts = VGroup(*[VGroup(Line(ax.c2p(x, y - np.sqrt(v)), ax.c2p(x, y + np.sqrt(v)), color=QUANTUM, stroke_width=2.5),
                                  Dot(ax.c2p(x, y), radius=0.07, color=QUANTUM)) for x, y, v in zip([1, 3, 5], d["y"], d["var"])])
            fit = Line(ax.c2p(0, b0), ax.c2p(5.4, b0 + 5.4 * b1), color=ACCENT, stroke_width=2.5)
            ex = VGroup(Line(ax.c2p(0, b0 - se0), ax.c2p(0, b0 + se0), color=ACCENT, stroke_width=3), Dot(ax.c2p(0, b0), radius=0.09, color=ACCENT))
            ex_lab = T(f"{num(b0)} ± {se0:.4f}", 17, ACCENT).next_to(ex, RIGHT, buff=0.15).shift(0.25 * DOWN)
            ticks = VGroup(*[T(str(n), 15, MUTED).next_to(ax.c2p(n, lo), DOWN, buff=0.1) for n in (0, 1, 3, 5)])
            ylabs = VGroup(*[T(num(v, ".2f"), 14, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in (lo, hi)])
            title = T(f"{name}, H1-1", 20, INK, weight=MEDIUM).next_to(ax, UP, buff=0.15).align_to(ax, LEFT)
            xlab = T("noise factor", 16, MUTED).next_to(ticks, DOWN, buff=0.08)
            plots.add(VGroup(ax, noiseless, nl_lab, ticks, ylabs, title, xlab, pts, fit, ex, ex_lab))
        ylab = T("energy (hartree)", 16, MUTED).rotate(PI / 2).next_to(plots[0], LEFT, buff=0.1)

        with self.voice("hardware") as v:
            self.play(FadeIn(head), LaggedStart(*[FadeIn(c, shift=0.1 * UP) for c in devices], lag_ratio=0.3), run_time=1.6)
            self.play(FadeIn(circ_note), run_time=0.6)
            v.until(1)
            self.play(FadeIn(trunc, shift=0.1 * UP), run_time=0.9)
            v.until(2)
            self.play(FadeOut(VGroup(devices, circ_note, trunc)), run_time=0.6)
            for p in plots:
                self.play(FadeIn(VGroup(*p[:7])), LaggedStart(*[FadeIn(q) for q in p[7]], lag_ratio=0.2), run_time=0.9)
            self.play(FadeIn(ylab), *[Create(p[8]) for p in plots], run_time=1.0)
            self.play(*[FadeIn(p[9], scale=0.6) for p in plots], *[FadeIn(p[10]) for p in plots], run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def results(self):
        head = header(7, "Results")
        panels = VGroup()
        for k, (name, d) in enumerate(ESTIMATES.items()):
            x = -3.6 + 7.0 * k
            lo, hi = d["window"]
            axis, labels = value_axis(d["window"], 4.2, x - 1.7, (lo, (lo + hi) / 2, hi))
            axis.shift(0.45 * UP)
            labels.shift(0.45 * UP)
            y_of = lambda e, axis=axis: axis.n2p(e)[1]
            left, right = x - 1.55, x + 1.6

            def level(e, color, dashed=False):
                cls = DashedLine if dashed else Line
                return cls([left, y_of(e), 0], [right, y_of(e), 0], color=color, stroke_width=3)
            ccsd = VGroup(level(d["ccsd"], CLASSICAL), T(f"CCSD {num(d['ccsd'])}", 15, CLASSICAL).next_to([right, y_of(d["ccsd"]), 0], RIGHT, buff=0.1))
            target = VGroup(level(d["target"], INK, dashed=True), T(f"CCSD(T) {num(d['target'])}", 15, INK).next_to([right, y_of(d["target"]), 0], RIGHT, buff=0.1))
            zne = next(p for p in d["points"] if p[0] == "H1-1 + ZNE")
            hw = VGroup(Line([x + 1.2, y_of(zne[1] - zne[2]), 0], [x + 1.2, y_of(zne[1] + zne[2]), 0], color=QUANTUM, stroke_width=3),
                        Dot([x + 1.2, y_of(zne[1]), 0], radius=0.09, color=QUANTUM))
            hw_lab = T(f"H1-1 + ZNE {num(zne[1])}", 16, QUANTUM).next_to(hw, LEFT, buff=0.15)
            gap = VGroup(DoubleArrow([x + 1.55, y_of(zne[1]), 0], [x + 1.55, y_of(d["target"]), 0], buff=0, color=MUTED, stroke_width=2,
                                     tip_length=0.12, max_tip_length_to_length_ratio=0.3),
                         T(f"{1000 * (zne[1] - d['target']):.0f} mhartree", 15, MUTED))
            gap[1].next_to(gap[0], RIGHT, buff=0.08)
            title = T(name, 24, INK, weight=MEDIUM).move_to([x, 2.85, 0])
            bare, hw_corr, full = CORRELATION[name]
            rec = VGroup(
                VGroup(T("bare active space", 16, ACCENT), Rectangle(width=2.6 * bare / full, height=0.18, stroke_width=0, fill_color=ACCENT, fill_opacity=1),
                       T("about 3%" if name == "benzene" else "under 1%", 16, ACCENT)),
                VGroup(T("downfolded, H1-1", 16, QUANTUM), Rectangle(width=2.6 * hw_corr / full, height=0.18, stroke_width=0, fill_color=QUANTUM, fill_opacity=1),
                       T(f"{100 * hw_corr / full:.0f}%", 16, QUANTUM)),
            )
            for r in rec:
                r[0].move_to([x - 0.2, 0, 0], aligned_edge=RIGHT)
                r[1].next_to(r[0], RIGHT, buff=0.15, aligned_edge=DOWN).shift(0.02 * UP)
                r[2].next_to(r[1], RIGHT, buff=0.1)
            rec.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([x + 0.3, -2.95, 0])
            rec_title = T("share of the CCSD(T) correlation energy", 16, MUTED).next_to(rec, UP, buff=0.12).align_to(rec, LEFT)
            panels.add(VGroup(title, axis, labels, ccsd, target, hw, hw_lab, gap, rec_title, rec))

        with self.voice("results") as v:
            self.play(FadeIn(head), *[FadeIn(VGroup(p[0], p[1], p[2])) for p in panels], run_time=0.8)
            self.play(*[Create(p[4][0]) for p in panels], *[FadeIn(p[4][1]) for p in panels], run_time=0.8)
            self.play(*[FadeIn(p[5], scale=0.6) for p in panels], *[FadeIn(p[6]) for p in panels], run_time=0.9)
            v.until(1)
            self.play(*[GrowFromCenter(p[7][0]) for p in panels], *[FadeIn(p[7][1]) for p in panels], run_time=0.9)
            v.until(1, 0.3)
            self.play(*[FadeIn(p[8]) for p in panels], *[FadeIn(p[9]) for p in panels], run_time=1.0)

        head8 = header(8, "Accuracy amplification")
        extra = VGroup()
        for p, (name, d) in zip(panels, ESTIMATES.items()):
            axis = p[1]
            x = axis.get_center()[0] + 1.7
            others = [q for q in d["points"] if q[0] != "H1-1 + ZNE"]
            xs = x - 0.9 + 0.45 * np.arange(len(others))
            dots = VGroup(*[VGroup(Line([xx, axis.n2p(e - s)[1], 0], [xx, axis.n2p(e + s)[1], 0], color=QUANTUM, stroke_width=2, stroke_opacity=0.6),
                                   Dot([xx, axis.n2p(e)[1], 0], radius=0.06, color=QUANTUM, fill_opacity=0.6)) for xx, (_, e, s) in zip(xs, others)])
            best = next(e for n, e, _ in d["points"] if n == "H1-1 + ZNE")
            arrow = Arrow([x + 1.35, axis.n2p(d["ccsd"])[1], 0], [x + 1.35, axis.n2p(best)[1], 0],
                          buff=0.05, color=CLASSICAL, stroke_width=4, max_tip_length_to_length_ratio=0.2)
            extra.add(VGroup(dots, arrow))
        note = T("all emulator and hardware estimates in Table V", 18, QUANTUM).move_to([0, -2.2, 0])
        with self.voice("amplify") as v:
            self.play(ReplacementTransform(head, head8), *[FadeOut(VGroup(p[6], p[7], p[8], p[9])) for p in panels], run_time=0.8)
            self.play(*[Create(p[3][0]) for p in panels], *[FadeIn(p[3][1]) for p in panels], run_time=0.8)
            self.play(*[Indicate(p[3], color=CLASSICAL, scale_factor=1.03) for p in panels], run_time=0.8)
            self.play(LaggedStart(*[FadeIn(e[0]) for e in extra], lag_ratio=0.3), FadeIn(note), run_time=1.2)
            self.play(*[GrowArrow(e[1]) for e in extra], run_time=1.0)
            v.until(1)
            amp = T("accuracy amplification", 30, CLASSICAL, weight=MEDIUM).move_to([0, -2.9, 0])
            self.play(FadeIn(amp, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("Downfolding matches the problem size to the available qubits,", 30, weight=MEDIUM),
                       T("and the effective Hamiltonian carries correlation", 30, weight=MEDIUM),
                       T("from outside the active space.", 30, weight=MEDIUM),
                       T("The authors see such hybrid methods as a bridge from noisy devices to fault-tolerant chemistry.", 22, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lines[3].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the paper"),
                      T("Bauman, Zheng, Liu, Myers, Panyala, Peng, Li, Kowalski. Phys. Rev. Research 8, 013072 (2026)", 20),
                      T("doi.org/10.1103/b1t6-ln6v   ·   arXiv:2507.01199", 20, ACCENT),
                      T("Effective Hamiltonians: github.com/npbauman/DUCC-Hamiltonian-Library", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.4)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class DownfoldingPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Coupled cluster downfolding", size=30).to_corner(UL, buff=0.6)
        lad = ladder(40, 20, 5.6, width=1.8, stroke=3).move_to([-5.4, -0.6, 0])
        window = SurroundingRectangle(lad[17:23], color=ACCENT, buff=0.1, stroke_width=6)
        heff = M('H^"eff" = (P + Q_"int") thin e^(-#c("' + CLASSICAL + '", $sigma_"ext"$)) H e^(#c("' + CLASSICAL + '", $sigma_"ext"$)) (P + Q_"int")', 1.3)
        heff.scale_to_fit_width(min(heff.width, 9.6)).next_to(lad, RIGHT, buff=0.6).shift(0.9 * UP)
        sub = T("(6e, 6o) active space on 12 qubits", 36, ACCENT, weight=MEDIUM).next_to(heff, DOWN, buff=0.7).align_to(heff, LEFT)
        self.add(label, lad, window, heff, sub)
