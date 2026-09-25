"""Explainer for "Quantum Information Harvesting with the Parallel Quantum Flow Algorithm"
(Bauman, Panyala, Liu, Zheng, Wang, Kowalski, J. Phys. Chem. Lett., 2026; arXiv:2606.04186v1).

Equations follow Eqs. 1-8 of the paper with the N = 1 Trotter step used there. Qubit counts,
cycle sizes, and correlation-energy fractions are quoted from Table 1 and the Results section.
The water energy profile is traced from Fig. 3 and the cycle-size reruns come from data.json
(see extract_data.py). The four-occupied, six-virtual sampling example is illustrative.
"""
import itertools
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

QFLOW = ACCENT       # QFlow, internal amplitudes, the global pool
CLASSICAL = GOLD     # external amplitudes and downfolding on classical processors
QUANTUM = DV         # qubits and the VQE solver
DATA = json.loads((Path(__file__).resolve().parent / "data.json").read_text())

# Table 1: basis, parent-problem qubits, active spaces per cycle, mean QFlow energy, % of CCSD correlation.
TABLE = [("cc-pVDZ", 46, 292, -76.2313, 96.8), ("aug-cc-pVDZ", 80, 1089, -76.2620, 97.1),
         ("cc-pVTZ", 114, 2387, -76.3168, 97.1), ("aug-cc-pVTZ", 182, 6412, -76.3259, 97.2),
         ("cc-pVQZ", 228, 10319, -76.3426, 97.2)]
PROPANE_QUBITS = 164

# Illustrative toy problem for the sampling algorithm (Fig. 1 of the paper).
TOY_OCC = [-1.30, -0.72, -0.58, -0.49]
TOY_VIR = [0.18, 0.27, 0.41, 0.55, 0.78, 1.05]
TOY_SEED = 7


def num(v, spec=".4f"):
    """Format a signed number with a typographic minus sign."""
    return format(v, spec).replace("-", "−")


def col(color, expr):
    return f'#c("{color}", ${expr}$)'


SIG_INT = col(QFLOW, 'sigma_"int" (i)')
SIG_EXT = col(CLASSICAL, 'sigma_"ext" (i)')


def toy_draws():
    """Run the coverage-driven sampler on the toy problem. Returns every draw with the groups it newly covers."""
    rng = random.Random(TOY_SEED)
    n_occ, n_vir = len(TOY_OCC), len(TOY_VIR)
    left = {(a, b) for a in itertools.combinations(range(n_occ), 2) for b in itertools.combinations(range(n_vir), 2)}
    draws = []
    while left:
        occ = tuple(sorted(rng.sample(range(n_occ), 3)))
        vir = tuple(sorted(rng.sample(range(n_vir), 3)))
        cover = {(a, b) for a in itertools.combinations(occ, 2) for b in itertools.combinations(vir, 2)}
        new = cover & left
        left -= new
        draws.append(dict(occ=occ, vir=vir, cover=cover, new=new,
                          gap=sum(TOY_VIR[v] for v in vir) - sum(TOY_OCC[o] for o in occ)))
    return draws


def molecule(atoms, bonds, scale=1.0):
    """Ball-and-stick sketch: atoms are (x, y, radius, color)."""
    pts = [np.array([x, y, 0]) * scale for x, y, _, _ in atoms]
    sticks = VGroup(*[Line(pts[a], pts[b], color=MUTED, stroke_width=4) for a, b in bonds])
    balls = VGroup(*[Circle(radius=r * scale, stroke_color=INK, stroke_width=2.5, fill_color=c, fill_opacity=1).move_to(p)
                     for p, (_, _, r, c) in zip(pts, atoms)])
    return VGroup(sticks, balls)


def water(scale=1.0):
    return molecule([(0, 0, 0.32, WASH), (-0.62, -0.45, 0.2, PAPER), (0.62, -0.45, 0.2, PAPER)], [(0, 1), (0, 2)], scale)


def propane(scale=1.0):
    c = [(-0.9, -0.2), (0, 0.3), (0.9, -0.2)]
    atoms = [(x, y, 0.26, WASH) for x, y in c]
    hs = [(-1.45, 0.25), (-1.25, -0.8), (-0.6, -0.75), (-0.35, 0.95), (0.35, 0.95), (1.45, 0.25), (1.25, -0.8), (0.6, -0.75)]
    owner = [0, 0, 0, 1, 1, 2, 2, 2]
    atoms += [(x, y, 0.15, PAPER) for x, y in hs]
    return molecule(atoms, [(0, 1), (1, 2)] + [(o, 3 + k) for k, o in enumerate(owner)], scale)


def orbital_ladder(n_occ, n_vir, height, width=1.6, stroke=2.5):
    """Evenly spaced orbital levels, occupied (ink, with electron pairs) below virtual (muted)."""
    n = n_occ + n_vir
    ys = np.linspace(-height / 2, height / 2, n)
    levels = VGroup(*[Line([-width / 2, y, 0], [width / 2, y, 0], stroke_width=stroke, color=INK if i < n_occ else MUTED)
                      for i, y in enumerate(ys)])
    return levels


def electrons(levels, idx, color=INK, r=0.045):
    return VGroup(*[VGroup(Dot(levels[i].get_center() + 0.1 * LEFT, radius=r, color=color),
                           Dot(levels[i].get_center() + 0.1 * RIGHT, radius=r, color=color)) for i in idx])


def mini_space(color=QFLOW, width=0.7, gap=0.12, stroke=2.2):
    """A (3, 3) active space: three occupied levels with electron pairs, three empty virtual levels."""
    lv = VGroup(*[Line([-width / 2, (i - 2.5) * gap, 0], [width / 2, (i - 2.5) * gap, 0], stroke_width=stroke,
                       color=color, stroke_opacity=1 if i < 3 else 0.55) for i in range(6)])
    frame = RoundedRectangle(corner_radius=0.06, width=width + 0.24, height=6 * gap + 0.16, stroke_color=color,
                             stroke_width=1.8, fill_color=PAPER, fill_opacity=1)
    return VGroup(frame, lv.move_to(frame))


class QFlowExplainer(Explainer):
    timing_file = BUILD / "qflow" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.idea()
        self.math()
        self.cover()
        self.flow()
        self.water()
        self.basis()
        self.propane_results()
        self.scope()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("The Journal of Physical Chemistry Letters · 2026")
        title = VGroup(T("Quantum Information Harvesting", 46, weight=MEDIUM),
                       T("with the Parallel Quantum Flow Algorithm", 46, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = T("Nicholas P. Bauman, Ajay Panyala, Chenxu Liu, Muqing Zheng, Meng Wang, Karol Kowalski", 22, MUTED)
        places = T("Pacific Northwest National Laboratory · University of British Columbia · University of Washington", 18, MUTED)
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
        head = header(1, "Too many qubits for one problem")
        h2o, c3h8 = water(1.3).move_to([-3.2, 0.6, 0]), propane(1.1).move_to([3.2, 0.6, 0])
        names = VGroup(T("water", 24, weight=MEDIUM).next_to(h2o, DOWN, buff=0.45),
                       T("propane", 24, weight=MEDIUM).next_to(c3h8, DOWN, buff=0.45))
        cost = T("wave-function cost grows exponentially with the number of orbitals", 22, MUTED).move_to([0, -2.4, 0])

        x0, per = -2.2, 7.8 / 240
        rows = [(f"water, {b}", q) for b, q, *_ in TABLE] + [("propane, cc-pVDZ", PROPANE_QUBITS)]
        ys = 1.9 - 0.62 * np.arange(len(rows))
        axis = Line([x0, ys[0] + 0.45, 0], [x0, ys[-1] - 0.45, 0], color=MUTED, stroke_width=2)
        bars, labels, values = VGroup(), VGroup(), VGroup()
        for (name, q), y in zip(rows, ys):
            focus = name.endswith("cc-pVQZ") or name.startswith("propane")
            bars.add(Rectangle(width=q * per, height=0.36, stroke_width=0, fill_color=QUANTUM,
                               fill_opacity=0.9 if focus else 0.35).move_to([x0, y, 0], aligned_edge=LEFT))
            labels.add(T(name, 20, INK if focus else MUTED).next_to([x0, y, 0], LEFT, buff=0.2))
            values.add(T(f"{q} qubits", 19, QUANTUM if focus else MUTED).next_to(bars[-1], RIGHT, buff=0.12))
            values[-1].add_background_rectangle(color=PAPER, opacity=1, buff=0.05)
        line100 = DashedLine([x0 + 100 * per, ys[0] + 0.55, 0], [x0 + 100 * per, ys[-1] - 0.5, 0], color=ACCENT,
                             stroke_width=3, dash_length=0.1)
        lab100 = VGroup(T("about 100 logical qubits", 20, ACCENT, weight=MEDIUM),
                        T("projected for 2028–2029", 18, ACCENT)).arrange(DOWN, buff=0.06).next_to(line100, UP, buff=0.12)
        qpe = T("phase estimation on realistic Hamiltonians may still be out of reach", 20, MUTED).move_to([0.6, -2.55, 0])
        qubit_note = T("qubits = 2 × (orbitals)", 17, MUTED).move_to([4.8, -3.2, 0])

        with self.voice("problem") as v:
            self.play(FadeIn(head), FadeIn(h2o, scale=0.8), FadeIn(c3h8, scale=0.8), FadeIn(names), run_time=1.2)
            self.play(FadeIn(cost, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            self.play(FadeOut(VGroup(h2o, c3h8, names, cost)), run_time=0.6)
            self.play(Create(axis), Create(line100), FadeIn(lab100), run_time=1.0)
            self.play(FadeIn(qpe), run_time=0.7)
            v.until(2)
            self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars], lag_ratio=0.12), FadeIn(labels), run_time=1.6)
            self.play(FadeIn(values), FadeIn(qubit_note), run_time=0.7)
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def idea(self):
        head = header(2, "Many small problems")
        big = orbital_ladder(4, 20, 5.4, width=1.8).move_to([-5.0, -0.25, 0])
        e_big = electrons(big, range(4))
        big_lab = VGroup(T("target space", 20, weight=MEDIUM), T("all orbitals", 17, MUTED)).arrange(DOWN, buff=0.05).next_to(big, UP, buff=0.15)
        rng = np.random.default_rng(3)
        picks = [(sorted(rng.choice(4, 3, replace=False)), sorted(4 + rng.choice(20, 3, replace=False))) for _ in range(3)]
        spaces = VGroup(*[mini_space() for _ in range(24)]).arrange_in_grid(rows=4, cols=6, buff=(0.35, 0.5)).move_to([1.6, 0.0, 0])
        dots = T("…", 30, QFLOW).next_to(spaces, RIGHT, buff=0.25)
        heffs = VGroup(*[M('H^"eff"', 0.7, CLASSICAL).next_to(s, UP, buff=0.06) for s in spaces])
        each = T("each active space has its own effective Hamiltonian", 20, CLASSICAL).next_to(spaces, DOWN, buff=0.3)
        rule = T("qubits set by the largest active space", 24, QUANTUM, weight=MEDIUM).move_to([1.6, -3.3, 0])

        with self.voice("idea") as v:
            self.play(FadeIn(head), LaggedStart(*[Create(l) for l in big], lag_ratio=0.03), FadeIn(e_big), FadeIn(big_lab), run_time=1.4)
            for k, (occ, vir) in enumerate(picks):
                sel = VGroup(*[big[i] for i in occ], *[big[i] for i in vir])
                self.play(sel.animate.set_color(QFLOW).set_stroke(width=5), run_time=0.45)
                self.play(TransformFromCopy(sel, spaces[k]), sel.animate.set_color(MUTED).set_stroke(width=2.5), run_time=0.7)
                for i in occ:
                    big[i].set_color(INK)
            self.play(LaggedStart(*[FadeIn(s, scale=0.8) for s in spaces[3:]], lag_ratio=0.05), FadeIn(dots), run_time=1.6)
            v.until(1)
            self.play(LaggedStart(*[FadeIn(h, shift=0.05 * DOWN) for h in heffs], lag_ratio=0.03), FadeIn(each), run_time=1.6)
            v.until(2)
            self.play(FadeIn(rule, shift=0.1 * UP), Indicate(spaces[0], color=QUANTUM, scale_factor=1.2), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def math(self):
        head = header(3, "Coupled active-space problems")
        e_full = M('E = bra(Phi) e^(-sigma) H e^(sigma) ket(Phi)', 1.2)
        split = M(f'sigma approx {SIG_INT} + {SIG_EXT}', 1.2)
        heff = M(f'H^"eff" (i) = (P + Q_"int" (i)) thin e^(-{SIG_EXT}) H e^({SIG_EXT}) (P + Q_"int" (i))', 1.1)
        energy = M(f'E(i) = bra(Psi_"int" (i)) H^"eff" (i) ket(Psi_"int" (i)), quad ket(Psi_"int" (i)) = e^({SIG_INT}) ket(Phi)', 1.1)
        eqs = VGroup(e_full, split, heff, energy).arrange(DOWN, buff=0.42).move_to([0, 0.75, 0])
        for e in eqs:
            if e.width > 12.4:
                e.scale_to_fit_width(12.4)
        e_lab = T("all orbitals: the target space", 18, MUTED).next_to(e_full, RIGHT, buff=0.5)
        split_lab = VGroup(T("internal: within active space i", 18, QFLOW),
                           T("external: reaches outside it", 18, CLASSICAL)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).next_to(split, RIGHT, buff=0.5)
        trotter = T("simplest Trotter approximation (N = 1)", 17, MUTED).next_to(heff, RIGHT, buff=0.3)
        if trotter.get_right()[0] > 7.0:
            trotter.next_to(heff, DOWN, buff=0.08).align_to(heff, RIGHT)

        nodes = VGroup(*[VGroup(Circle(radius=0.34, stroke_color=QFLOW, stroke_width=2.5, fill_color=PAPER, fill_opacity=1),
                                M(f'cal(A)_{k}', 0.75, QFLOW)) for k in range(1, 5)])
        for n in nodes:
            n[1].move_to(n[0])
        nodes.arrange(RIGHT, buff=1.3).move_to([0, -2.85, 0])
        links = VGroup(*[CurvedDoubleArrow(nodes[a][0].get_top(), nodes[b][0].get_top(), angle=-0.9, color=CLASSICAL, stroke_width=2.2,
                                           tip_length=0.14) for a, b in [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3)]])
        couple = T("amplitudes found in one active space enter the others' effective Hamiltonians", 18, CLASSICAL).next_to(nodes, DOWN, buff=0.22)

        with self.voice("math") as v:
            self.play(FadeIn(head), Write(e_full), run_time=1.4)
            self.play(FadeIn(e_lab), run_time=0.5)
            v.until(1)
            self.play(FadeIn(split, shift=0.1 * DOWN), run_time=1.0)
            self.play(FadeIn(split_lab), run_time=0.6)
            v.until(2)
            self.play(FadeIn(heff, shift=0.1 * DOWN), run_time=1.2)
            self.play(FadeIn(trotter), run_time=0.5)
            v.until(3)
            self.play(FadeIn(energy, shift=0.1 * DOWN), run_time=1.1)
            v.until(4)
            self.play(LaggedStart(*[FadeIn(n, scale=0.8) for n in nodes], lag_ratio=0.15), run_time=0.8)
            self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.12), FadeIn(couple), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def cover(self):
        head = header(4, "Covering every double excitation")
        draws = toy_draws()
        n_occ, n_vir = len(TOY_OCC), len(TOY_VIR)
        occ_pairs = list(itertools.combinations(range(n_occ), 2))
        vir_pairs = list(itertools.combinations(range(n_vir), 2))

        # Orbital ladder with illustrative energies.
        def y_of(e):
            return -2.2 + (e + 1.4) / 2.6 * 4.2
        levels = VGroup(*[Line([-0.6, y_of(e), 0], [0.6, y_of(e), 0], stroke_width=3, color=INK) for e in TOY_OCC] +
                        [Line([-0.6, y_of(e), 0], [0.6, y_of(e), 0], stroke_width=3, color=MUTED) for e in TOY_VIR]).shift(5.6 * LEFT)
        pairs = electrons(levels, range(n_occ), r=0.05)
        occ_lab = T("occupied", 17, INK).next_to(levels[:n_occ], LEFT, buff=0.15)
        vir_lab = T("virtual", 17, MUTED).next_to(levels[n_occ:], LEFT, buff=0.15)
        e_lab = T("orbital energy", 15, MUTED).rotate(PI / 2).next_to(levels, RIGHT, buff=0.2)

        cell = 0.38
        grid = VGroup(*[Square(cell, stroke_color=LINE, stroke_width=1.2, fill_color=PAPER, fill_opacity=1)
                        .move_to([j * cell, -i * cell, 0]) for i in range(len(occ_pairs)) for j in range(len(vir_pairs))])
        grid.move_to([1.0, 1.2, 0])
        index = {(a, b): i * len(vir_pairs) + j for i, a in enumerate(occ_pairs) for j, b in enumerate(vir_pairs)}
        g_title = VGroup(T("double-excitation groups (o₁, o₂, v₁, v₂)", 19, weight=MEDIUM),
                         T("rows: occupied pairs · columns: virtual pairs", 16, MUTED)).arrange(DOWN, buff=0.06).next_to(grid, UP, buff=0.2)
        toy = T("illustrative: 4 occupied and 6 virtual orbitals, 90 groups", 16, MUTED).next_to(grid, DOWN, buff=0.18)

        def counter(kept, left):
            return VGroup(T(f"active spaces kept: {kept}", 20, QFLOW, weight=MEDIUM),
                          T(f"groups left: {left}", 20, MUTED)).arrange(RIGHT, buff=0.6).move_to([1.0, -1.05, 0])

        count = counter(0, len(grid))
        impl = VGroup(T("QFlow in ExaChem", 34, QFLOW, weight=MEDIUM),
                      T("parallel implementation for high-performance computers", 22, INK),
                      T("single and double excitations", 22, MUTED)).arrange(DOWN, buff=0.18).move_to([0, 0.2, 0])
        verdict_pos = np.array([1.0, -1.6, 0])
        real = VGroup(T("water, cc-pVTZ: 4 occupied, 53 virtual orbitals", 18, INK),
                      T("8,268 groups → 2,387 active spaces of size (3, 3)", 18, QFLOW)).arrange(DOWN, buff=0.08).move_to([1.0, -2.65, 0])

        with self.voice("cover") as v:
            self.play(FadeIn(head), FadeIn(impl, shift=0.1 * UP), run_time=1.0)
            v.until(1)
            self.play(FadeOut(impl), LaggedStart(*[Create(l) for l in levels], lag_ratio=0.05), FadeIn(pairs),
                      FadeIn(occ_lab), FadeIn(vir_lab), FadeIn(e_lab), run_time=1.2)
            self.play(FadeIn(grid, lag_ratio=0.01), FadeIn(g_title), FadeIn(toy), run_time=1.2)
            demo = index[((0, 1), (0, 1))]
            self.play(grid[demo].animate.set_fill(QFLOW, 0.9),
                      *[levels[i].animate.set_color(QFLOW).set_stroke(width=5) for i in (0, 1, n_occ, n_occ + 1)], run_time=0.7)
            self.play(grid[demo].animate.set_fill(PAPER, 1),
                      *[levels[i].animate.set_color(INK if i < n_occ else MUTED).set_stroke(width=3) for i in (0, 1, n_occ, n_occ + 1)], run_time=0.5)
            v.until(2)
            self.play(FadeIn(count), run_time=0.4)
            slow = 5
            fast = max((v.dur(2) + 0.8 - slow * 1.0) / max(len(draws) - slow, 1), 0.12)
            kept, left = 0, len(grid)
            for k, d in enumerate(draws):
                sel = [*d["occ"], *[n_occ + j for j in d["vir"]]]
                kept += bool(d["new"])
                left -= len(d["new"])
                rt = 1.0 if k < slow else fast
                on = [levels[i].animate.set_color(QFLOW).set_stroke(width=5) for i in sel]
                fills = [grid[index[g]].animate.set_fill(QFLOW, 0.85) for g in d["new"]]
                seen = [grid[index[g]].animate.set_stroke(QFLOW, width=2.5) for g in d["cover"] - d["new"]]
                new_count = counter(kept, left)
                if k < slow:
                    verdict = T("new groups: keep" if d["new"] else "no new group: discard", 18, QFLOW if d["new"] else MUTED).move_to(verdict_pos)
                    self.play(*on, run_time=0.35 * rt)
                    self.play(*fills, *seen, FadeIn(verdict), FadeOut(count), FadeIn(new_count), run_time=0.45 * rt)
                    count = new_count
                    self.play(FadeOut(verdict), *[levels[i].animate.set_color(INK if i < n_occ else MUTED).set_stroke(width=3) for i in sel],
                              *[grid[index[g]].animate.set_stroke(LINE, width=1.2) for g in d["cover"] - d["new"]], run_time=0.2 * rt)
                else:
                    self.remove(count)
                    self.add(new_count)
                    count = new_count
                    if fills:
                        self.play(*fills, run_time=rt)
                    else:
                        self.wait(rt)
            v.until(3)
            kept_draws = sorted([d for d in draws if d["new"]], key=lambda d: d["gap"])
            owner = {}
            for rank, d in enumerate(kept_draws):
                for g in d["cover"]:
                    owner.setdefault(g, rank)
            shade = [interpolate_color(ManimColor(QFLOW), ManimColor(PAPER), 0.75 * r / (len(kept_draws) - 1)) for r in range(len(kept_draws))]
            order = T("sorted by orbital energy difference; shade = owning active space", 17, MUTED).move_to(verdict_pos)
            self.play(FadeIn(order), run_time=0.5)
            self.play(LaggedStart(*[AnimationGroup(*[grid[index[g]].animate.set_fill(shade[r], 1) for g, r in owner.items() if r == rank])
                                    for rank in range(len(kept_draws))], lag_ratio=0.3), run_time=2.6)
            self.play(FadeIn(real, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def flow(self):
        head = header(5, "The parallel flow")
        space = mini_space(QFLOW, width=1.3, gap=0.26, stroke=3.5).move_to([0, 0.3, 0])
        space_e = VGroup(*[VGroup(Dot(space[1][i].get_center() + 0.14 * LEFT, radius=0.06, color=QFLOW),
                                  Dot(space[1][i].get_center() + 0.14 * RIGHT, radius=0.06, color=QFLOW)) for i in range(3)])
        space_lab = VGroup(T("3 occupied + 3 virtual orbitals", 22, INK), T("6 electrons in 6 orbitals → 12 qubits", 22, QUANTUM, weight=MEDIUM)
                           ).arrange(DOWN, buff=0.1).next_to(space, DOWN, buff=0.35)

        queue = VGroup(*[mini_space(QFLOW, width=0.5, gap=0.07, stroke=1.6) for _ in range(9)]).arrange(DOWN, buff=0.1).move_to([-6.1, -0.35, 0])
        queue_pos = queue.get_center()
        q_lab = VGroup(T("sorted", 15, MUTED), T("active spaces", 15, MUTED)).arrange(DOWN, buff=0.03).next_to(queue, UP, buff=0.12)
        lanes_y = [1.55, 0.0, -1.55]
        down = VGroup(*[card([T("downfold (DUCC)", 19, CLASSICAL, weight=MEDIUM), T("ExaChem · classical", 16, MUTED)], 2.9, CLASSICAL, pad=0.18)
                        .move_to([-2.9, y, 0]) for y in lanes_y])
        vqe = VGroup(*[card([T("VQE, UCCSD ansatz", 19, QUANTUM, weight=MEDIUM), T("NWQSim · 12 qubits", 16, MUTED)], 2.9, QUANTUM, pad=0.18)
                       .move_to([0.9, y, 0]) for y in lanes_y])
        lane_lab = VGroup(*[T(f"group {k + 1}", 15, MUTED).next_to(down[k], UP, buff=0.06).align_to(down[k], LEFT) for k in range(3)])
        heff_arrows = VGroup(*[Arrow(d.get_right(), q.get_left(), buff=0.08, color=CLASSICAL, stroke_width=3, max_tip_length_to_length_ratio=0.25)
                               for d, q in zip(down, vqe)])
        heff_tags = VGroup(*[M('H^"eff"', 0.5, CLASSICAL).next_to(a, UP, buff=0.02) for a in heff_arrows])

        pool_box = RoundedRectangle(corner_radius=0.15, width=2.6, height=4.2, stroke_color=QFLOW, stroke_width=3,
                                    fill_color=PAPER, fill_opacity=1).move_to([5.3, -0.1, 0])
        pool_title = VGroup(T("global pool", 20, QFLOW, weight=MEDIUM), T("of amplitudes", 17, QFLOW)).arrange(DOWN, buff=0.04).next_to(pool_box, UP, buff=0.12)
        amp = VGroup(*[Dot(radius=0.07, color=LINE) for _ in range(88)]).arrange_in_grid(rows=11, cols=8, buff=0.17).move_to(pool_box)
        write = VGroup(*[Arrow(q.get_right(), [pool_box.get_left()[0], q.get_center()[1], 0], buff=0.08, color=QUANTUM, stroke_width=3,
                               max_tip_length_to_length_ratio=0.2) for q in vqe])
        bus_y = -2.75
        read = VGroup(Line([pool_box.get_bottom()[0], pool_box.get_bottom()[1], 0], [pool_box.get_bottom()[0], bus_y, 0], color=QFLOW, stroke_width=3),
                      Line([pool_box.get_bottom()[0], bus_y, 0], [-2.9, bus_y, 0], color=QFLOW, stroke_width=3),
                      Arrow([-2.9, bus_y, 0], down[2].get_bottom(), buff=0.02, color=QFLOW, stroke_width=3, max_tip_length_to_length_ratio=0.3))
        read_lab = T("current amplitudes", 16, QFLOW).next_to(read[1], DOWN, buff=0.08)
        barrier = DashedLine([-4.85, 2.35, 0], [-4.85, -2.4, 0], color=INK, stroke_width=3, dash_length=0.12)
        barrier_lab = T("all groups wait at the end of each cycle", 16, INK).next_to(barrier.get_start(), RIGHT, buff=0.12).shift(0.35 * UP)
        cycle = T("cycle 1", 20, QFLOW, weight=MEDIUM).move_to([-6.1, -3.1, 0])
        harvest = T("later active spaces use amplitudes harvested from earlier ones", 22, QFLOW, weight=MEDIUM).move_to([0, -3.45, 0])

        filled = [0]

        def fill(n):
            start = filled[0]
            filled[0] = min(start + n, len(amp))
            return [amp[i].animate.set_color(QFLOW) for i in range(start, filled[0])]

        with self.voice("flow") as v:
            self.play(FadeIn(head), FadeIn(space, scale=0.9), FadeIn(space_e), run_time=1.0)
            self.play(FadeIn(space_lab, shift=0.1 * UP), run_time=0.7)
            v.until(1)
            self.play(ReplacementTransform(VGroup(space, space_e), queue[0]), FadeOut(space_lab), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(q, shift=0.1 * DOWN) for q in queue[1:]], lag_ratio=0.08), FadeIn(q_lab), run_time=0.8)
            self.play(FadeIn(down[0]), FadeIn(lane_lab[0]), FadeIn(pool_box), FadeIn(pool_title), FadeIn(amp), run_time=0.8)
            self.play(Create(read), FadeIn(read_lab), run_time=1.0)
            v.until(2)
            self.play(GrowArrow(heff_arrows[0]), FadeIn(heff_tags[0]), FadeIn(vqe[0]), run_time=0.9)
            self.play(GrowArrow(write[0]), *fill(6), run_time=0.9)
            v.until(3)
            self.play(FadeIn(down[1:]), FadeIn(lane_lab[1:]), FadeIn(vqe[1:]), *[GrowArrow(a) for a in heff_arrows[1:]],
                      FadeIn(heff_tags[1:]), *[GrowArrow(w) for w in write[1:]], run_time=1.0)
            for batch in range(3):
                movers = [queue[3 * batch + k] for k in range(3)]
                self.play(*[m.animate.scale(0.9).move_to(down[k].get_left() + 0.35 * LEFT) for k, m in enumerate(movers)], run_time=0.6)
                self.play(*[FadeOut(m) for m in movers], *fill(9), *[vqe[k][0].animate(rate_func=there_and_back).set_stroke(width=7) for k in range(3)], run_time=0.7)
            self.play(Create(barrier), FadeIn(barrier_lab), FadeIn(cycle), run_time=0.7)
            fresh = VGroup(*[mini_space(QFLOW, width=0.5, gap=0.07, stroke=1.6) for _ in range(9)]).arrange(DOWN, buff=0.1).move_to(queue_pos)
            self.play(FadeIn(fresh, lag_ratio=0.1), Transform(cycle, T("cycle 2", 20, QFLOW, weight=MEDIUM).move_to(cycle)), run_time=0.8)
            v.until(4)
            self.play(Indicate(amp, color=QFLOW, scale_factor=1.05), Indicate(read, color=QFLOW), FadeIn(harvest, shift=0.1 * UP), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def water(self):
        head = header(6, "Water, cc-pVTZ basis")
        tr = DATA["h2o_tz"]
        n, cyc, e = np.array(tr["combination"]), np.array(tr["cycle"]), np.array(tr["energy"])
        lo, hi = -76.36, -76.045
        ax = Axes(x_range=[0, 12000, 2000], y_range=[lo, hi, 0.05], x_length=9.6, y_length=4.2, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([0.6, -0.45, 0])
        ax.x_axis.set_stroke(opacity=0)
        base = Line(ax.c2p(0, lo), ax.c2p(12000, lo), color=MUTED, stroke_width=2)
        yt = VGroup(*[T(num(y, ".2f"), 15, MUTED).next_to(ax.c2p(0, y), LEFT, buff=0.12) for y in (-76.30, -76.20, -76.10)])
        xt = VGroup(*[T(f"{x:,}", 15, MUTED).next_to(ax.c2p(x, lo), DOWN, buff=0.1) for x in (0, 4000, 8000, 12000)])
        xlab = T("active-space solves, cycles in sequence", 17, MUTED).next_to(xt, DOWN, buff=0.08)
        ylab = T("energy (hartree)", 17, MUTED).next_to(ax.y_axis, UP, buff=0.12).shift(0.3 * RIGHT)
        ccsd_y = DATA["h2o_tz"]["ccsd"]
        ccsd = DashedLine(ax.c2p(0, ccsd_y), ax.c2p(12000, ccsd_y), color=INK, stroke_width=2.5, dash_length=0.1)
        ccsd_lab = T("all-orbital CCSD", 16, INK).next_to(ccsd, DOWN, buff=0.06).align_to(ccsd, RIGHT)
        source = T("traced from Fig. 3 of the paper", 15, MUTED).next_to(ax, RIGHT, buff=0.1).align_to(ax, DOWN).shift(0.5 * UP)
        if source.get_right()[0] > 7.0:
            source.next_to(xlab, RIGHT, buff=0.6)

        curves = []
        for k in range(1, 6):
            m = cyc == k
            pts = [ax.c2p(x, y) for x, y in zip(n[m][::2], e[m][::2])]
            curves.append(VMobject(stroke_color=QFLOW, stroke_width=3.5).set_points_as_corners(pts))
        bounds = [n[cyc == k][0] for k in range(2, 6)]
        seps = VGroup(*[DashedLine(ax.c2p(b, lo), ax.c2p(b, hi), color=LINE, stroke_width=1.5, dash_length=0.06) for b in bounds])
        edges = [0, *bounds, 12000]
        cyc_labs = VGroup(*[T(f"cycle {k + 1}", 15, MUTED).move_to(ax.c2p((edges[k] + edges[k + 1]) / 2, -76.08)) for k in range(5)])

        facts = VGroup(T("114 qubits → cycles of 2,387 active spaces, 12 qubits each", 21, QFLOW, weight=MEDIUM),
                       T("oxygen 1s core uncorrelated · 140 groups of 2 cores", 17, MUTED)).arrange(DOWN, buff=0.08).move_to([0.6, 2.75, 0])
        bare = T("first 140, one per group: bare Hamiltonian", 16, CLASSICAL).next_to(ax.c2p(450, -76.12), RIGHT, buff=0.1)
        end1 = ax.c2p(bounds[0], e[cyc == 1][-1])
        mark = Dot(end1, radius=0.08, color=INK)
        pct = VGroup(T("end of cycle 1:", 17, INK), T("95% of CCSD correlation energy", 17, INK, weight=MEDIUM)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).next_to(end1, UP, buff=0.35).shift(0.9 * RIGHT)
        conv = VGroup(T("cycle 3 → 4: every active space changes < 1 mHa", 17, INK),
                      T("cycle 4 → 5: tens of µHa", 17, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to(ax.c2p(8200, -76.2))

        with self.voice("water") as v:
            self.play(FadeIn(head), FadeIn(facts[0], shift=0.1 * DOWN), run_time=1.0)
            self.play(FadeIn(facts[1]), Create(ax), Create(base), FadeIn(yt), FadeIn(xt), FadeIn(xlab), FadeIn(ylab), run_time=1.2)
            self.play(Create(ccsd), FadeIn(ccsd_lab), FadeIn(source), run_time=0.8)
            v.until(1)
            self.play(Create(curves[0]), run_time=max(v.dur(1) - 0.5, 2.0), rate_func=linear)
            self.play(FadeIn(bare), run_time=0.5)
            v.until(2)
            self.play(FadeIn(mark, scale=0.5), FadeIn(pct, shift=0.1 * UP), run_time=0.9)
            v.until(3)
            self.play(Create(seps), FadeIn(cyc_labs), *[Create(c) for c in curves[1:]], run_time=2.0)
            self.play(FadeIn(conv, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def basis(self):
        head = header(7, "Five basis sets for water")
        cols_x = [-5.3, -3.1, 2.4, 5.2]
        heads = VGroup(T("basis", 17, MUTED), T("full problem", 17, MUTED), T("active spaces per cycle", 17, MUTED),
                       T("of CCSD correlation", 17, MUTED))
        for h, x in zip(heads, cols_x):
            h.move_to([x, 2.35, 0])
        heads[1].align_to([cols_x[1], 0, 0], LEFT)
        rule = Line([-6.6, 2.05, 0], [6.6, 2.05, 0], color=LINE, stroke_width=2)
        per = 3.3 / 228
        rows = VGroup()
        for k, (b, q, size, _, pct) in enumerate(TABLE):
            y = 1.5 - 0.72 * k
            bar = Rectangle(width=q * per, height=0.34, stroke_width=0, fill_color=QUANTUM, fill_opacity=0.8).move_to([cols_x[1], y, 0], aligned_edge=LEFT)
            rows.add(VGroup(T(b, 20, INK).move_to([cols_x[0], y, 0]), bar, T(f"{q} qubits", 18, QUANTUM).next_to(bar, RIGHT, buff=0.1),
                            T(f"{size:,}", 20, QFLOW, weight=MEDIUM).move_to([cols_x[2], y, 0]),
                            T(f"{pct:.1f}%", 20, INK, weight=MEDIUM).move_to([cols_x[3], y, 0])))
        note = T("each active space: 12 qubits, 3 occupied and 3 virtual orbitals", 18, MUTED).move_to([0, -2.35, 0])
        box = SurroundingRectangle(VGroup(*[r[4] for r in rows]), color=ACCENT, buff=0.15, stroke_width=2.5)
        trend = T("rises slightly with basis size", 17, ACCENT).next_to(box, DOWN, buff=0.15)
        src = T("Table 1 of the paper; mean QFlow energy over active spaces", 15, MUTED).move_to([0, -3.3, 0])

        with self.voice("basis") as v:
            self.play(FadeIn(head), FadeIn(heads), Create(rule), run_time=0.9)
            self.play(LaggedStart(*[AnimationGroup(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2]), FadeIn(r[3])) for r in rows],
                                  lag_ratio=0.3), FadeIn(note), FadeIn(src), run_time=2.6)
            self.play(Indicate(rows[4][3], color=QFLOW), Indicate(rows[4][2], color=QUANTUM), run_time=1.0)
            v.until(1)
            self.play(LaggedStart(*[FadeIn(r[4], shift=0.1 * LEFT) for r in rows], lag_ratio=0.2), run_time=1.4)
            self.play(Create(box), FadeIn(trend), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def propane_results(self):
        head = header(8, "Propane, cc-pVDZ basis")
        mol = propane(1.3).move_to([-4.6, 0.3, 0])
        mol_lab = VGroup(T("C₃H₈, all electrons correlated", 19, INK), T("13 occupied, 69 virtual orbitals", 17, MUTED)
                         ).arrange(DOWN, buff=0.06).next_to(mol, DOWN, buff=0.35)
        full = card([T("full problem", 18, MUTED), T("164 qubits", 36, QUANTUM, weight=MEDIUM)], 3.2, QUANTUM).move_to([-0.3, 0.9, 0])
        arrow = Arrow(full.get_right(), full.get_right() + 1.3 * RIGHT, buff=0.1, color=MUTED, stroke_width=3)
        flow = card([T("QFlow, per cycle", 18, MUTED), T("56,860 active spaces", 32, QFLOW, weight=MEDIUM), T("12 qubits each", 18, QUANTUM)],
                    3.9, QFLOW).next_to(arrow, RIGHT, buff=0.1)
        params = card([T("unique parameters optimized", 18, MUTED), T("1.17 million", 32, QFLOW, weight=MEDIUM)], 3.9, QFLOW
                      ).next_to(flow, DOWN, buff=0.35)
        res = VGroup(T("95% of the CCSD correlation energy by cycle 3 (average)", 22, INK, weight=MEDIUM),
                     T("every active space converged below 1 mHa · 116 groups of 2 cores", 17, MUTED)
                     ).arrange(DOWN, buff=0.1).move_to([0, -2.75, 0])

        with self.voice("propane") as v:
            self.play(FadeIn(head), FadeIn(mol, scale=0.85), FadeIn(mol_lab), run_time=1.0)
            self.play(FadeIn(full, shift=0.1 * RIGHT), run_time=0.7)
            v.until(0, 0.4)
            self.play(GrowArrow(arrow), FadeIn(flow, shift=0.1 * RIGHT), run_time=1.0)
            v.until(0, 0.72)
            self.play(FadeIn(params, shift=0.1 * DOWN), run_time=0.8)
            v.until(1)
            self.play(FadeIn(res, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 09
    def scope(self):
        head = header(9, "Scope")
        items = [
            ("Active-space solutions ran on a quantum simulator (NWQSim)", "percentages are relative to all-orbital CCSD", QUANTUM),
            ("Reported energy: average of the active-space energies", "suited to mainly dynamical correlation, which the paper notes is hard for existing quantum algorithms", QFLOW),
            ("Routes to the remaining correlation", "more complete effective Hamiltonians, larger active spaces, higher excitations", CLASSICAL),
        ]
        cards = VGroup(*[card([T(a, 22, c, weight=MEDIUM), T(b, 18, MUTED)], 11.6, c) for a, b, c in items]).arrange(DOWN, buff=0.35).move_to([0, -0.1, 0])
        with self.voice("scope") as v:
            self.play(FadeIn(head), FadeIn(cards[0], shift=0.1 * UP), run_time=0.9)
            for k, s in ((1, 1), (2, 3)):
                v.until(s)
                self.play(FadeIn(cards[k], shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("In this work, QFlow turned one large simulation", 32, weight=MEDIUM),
                       T("into many twelve-qubit problems run in parallel.", 32, weight=MEDIUM),
                       T("The authors propose it for early fault-tolerant machines, running many shallow circuits side by side.", 22, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lines[2].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the paper"),
                      T("Bauman, Panyala, Liu, Zheng, Wang, Kowalski. J. Phys. Chem. Lett. (2026)", 20),
                      T("doi.org/10.1021/acs.jpclett.6c02025   ·   arXiv:2606.04186", 20, ACCENT),
                      T("Code: github.com/ExaChem/exachem", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.4)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class QFlowPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Parallel Quantum Flow", size=30).to_corner(UL, buff=0.6)
        big = orbital_ladder(4, 26, 5.8, width=2.0, stroke=3).move_to([-5.2, -0.5, 0])
        for i in (1, 2, 3, 6, 11, 19):
            big[i].set_color(ACCENT).set_stroke(width=6)
        spaces = VGroup(*[mini_space(ACCENT, width=0.9, gap=0.14, stroke=3) for _ in range(12)]).arrange_in_grid(rows=3, cols=4, buff=0.35)
        spaces.move_to([1.6, 0.4, 0])
        sub = T("114 qubits  →  2,387 × 12 qubits", 40, ACCENT, weight=MEDIUM).next_to(spaces, DOWN, buff=0.6)
        arrow = Arrow([big.get_right()[0] + 0.2, spaces.get_center()[1], 0], spaces.get_left() + 0.2 * LEFT, buff=0.1, color=MUTED, stroke_width=6)
        self.add(label, big, spaces, sub, arrow)
