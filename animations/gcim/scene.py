"""Explainer for "Unleashed from constrained optimization: quantum computing for quantum chemistry
employing generator coordinate inspired method" (Zheng, Peng, Li, Yang, Kowalski,
npj Quantum Inf. 10, 127, 2024), linked to the earlier "Quantum algorithms for generator
coordinate methods" (Phys. Rev. Research 5, 023200, 2023).

The convergence curves come from data.json (see extract_data.py). Other values are quoted
from Tables 1-3 and the main text of the npj paper.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

GCIM = ACCENT
VQE = DV
SOLVE = GOLD
DATA = json.loads((Path(__file__).resolve().parent / "data.json").read_text())

# Table 3 (H6), minimum ADAPT iterations to the listed error.
ITERATIONS = [("H6, 1.0584 Å", 79, 70, 67), ("H6, 5.0000 Å", 37, 84, 26)]


def config_panel(occupied, label):
    """Four spin orbitals with two electrons, as in the toy model of Fig. 1a."""
    levels = VGroup(*[Line(LEFT * 0.45, RIGHT * 0.45, color=INK, stroke_width=2.5).shift(UP * 0.28 * i) for i in range(4)])
    dots = VGroup(*[Dot(levels[i].get_center() + 0.08 * UP, radius=0.07, color=ACCENT) for i in occupied])
    lab = M(label, 0.8).next_to(levels, DOWN, buff=0.25)
    return VGroup(levels, dots, lab)


def landscape(x):
    """An illustrative VQE energy landscape: a local minimum, a lower minimum, and a flat region."""
    return (1.25 - 0.45 * np.exp(-(x - 1.3) ** 2 / 0.22) - 0.85 * np.exp(-(x - 3.1) ** 2 / 0.32)
            + 0.03 * np.sin(6 * x) * np.exp(-(x - 5.2) ** 2))


def grid(n, size=0.26, color=SOLVE):
    return VGroup(*[Square(size, stroke_color=color, stroke_width=1.5, fill_color=color, fill_opacity=0.15)
                    .move_to([j * size, -i * size, 0]) for i in range(n) for j in range(n)])


class GCIMExplainer(Explainer):
    timing_file = BUILD / "gcim" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.gcm()
        self.toy()
        self.choose()
        self.adapt()
        self.results()
        self.costs()
        self.link()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("npj Quantum Information 10, 127 · 2024")
        title = VGroup(T("Unleashed from constrained optimization:", 40, weight=MEDIUM),
                       T("quantum computing for quantum chemistry employing", 40, weight=MEDIUM),
                       T("generator coordinate inspired method", 40, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = T("Muqing Zheng, Bo Peng, Ang Li, Xiu Yang, Karol Kowalski", 22, MUTED)
        places = T("Pacific Northwest National Laboratory · Lehigh University · University of Washington", 18, MUTED)
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
        head = header(1, "Variational search")
        eq = M('E_"VQE" = min_(bold(theta)) thin lr(chevron.l psi(bold(theta)) | H | psi(bold(theta)) chevron.r)', 1.15).move_to([-3.9, 1.8, 0])
        eq_lab = T("adjust circuit parameters, measure, repeat", 20, VQE).next_to(eq, DOWN, buff=0.35)
        ax = Axes(x_range=[0, 6, 1], y_range=[0, 1.4, 0.5], x_length=6.2, y_length=3.6, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([3.6, -0.4, 0])
        curve = ax.plot(landscape, x_range=[0, 6, 0.01], color=VQE, stroke_width=4)
        exact = DashedLine(ax.c2p(0, 0.22), ax.c2p(6, 0.22), color=INK, stroke_width=2, dash_length=0.1)
        exact_lab = T("exact ground-state energy", 17, INK).next_to(exact, DOWN, buff=0.08).align_to(exact, RIGHT)
        labels = VGroup(T("energy", 17, MUTED).next_to(ax.y_axis, UP, buff=0.1),
                        T("circuit parameters θ", 17, MUTED).next_to(ax.x_axis, DOWN, buff=0.15),
                        T("illustrative landscape", 15, MUTED).next_to(ax.x_axis, DOWN, buff=0.5).align_to(ax, RIGHT))
        theta = ValueTracker(0.25)
        ball = always_redraw(lambda: Dot(ax.c2p(theta.get_value(), landscape(theta.get_value())) + 0.1 * UP, radius=0.1, color=VQE))
        issues = VGroup(
            T("local minimum", 17, VQE).next_to(ax.c2p(1.3, landscape(1.3)), UP, buff=0.35),
            VGroup(DoubleArrow(ax.c2p(3.1, landscape(3.1)), ax.c2p(3.1, 0.22), buff=0.03, color=MUTED, stroke_width=2,
                               tip_length=0.1, max_tip_length_to_length_ratio=0.3),
                   T("inexact ansatz", 17, MUTED)).arrange(RIGHT, buff=0.1).move_to(ax.c2p(3.75, (landscape(3.1) + 0.22) / 2)),
            T("barren plateau", 17, VQE).next_to(ax.c2p(5.2, landscape(5.2)), UP, buff=0.25),
        )
        with self.voice("problem") as v:
            self.play(FadeIn(head), Write(eq), run_time=1.6)
            self.play(FadeIn(eq_lab), Create(ax), FadeIn(labels), Create(curve), run_time=1.6)
            self.add(ball)
            self.play(theta.animate.set_value(1.3), run_time=max(v.dur(0) - 3.4, 1.0), rate_func=rush_from)
            v.until(1)
            self.play(Create(exact), FadeIn(exact_lab), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(i, shift=0.1 * UP) for i in issues], lag_ratio=0.5), run_time=2.4)
        ball.clear_updaters()
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def gcm(self):
        head = header(2, "Generator coordinate methods")
        cite = card([T("Earlier paper", 20, MUTED),
                     T("Quantum algorithms for generator coordinate methods", 24, INK, weight=MEDIUM),
                     T("Zheng, Peng, Wiebe, Li, Yang, Kowalski · Phys. Rev. Research 5, 023200 (2023)", 18, MUTED)], 9.0, GCIM)
        cite.move_to([0, 2.35, 0])
        ref = M("ket(phi_0)", 1.0).move_to([-5.9, -0.4, 0])
        gens = VGroup(*[gate(f"U_{i}", 0.7, 0.5, GCIM, 0.8) for i in range(1, 5)]).arrange(DOWN, buff=0.22).move_to([-4.2, -0.4, 0])
        kets = VGroup(*[M(f"ket(psi_{i})", 0.9, GCIM) for i in range(1, 5)])
        for k, g in zip(kets, gens):
            k.next_to(g, RIGHT, buff=0.5)
        arrows = VGroup(*[Arrow(ref.get_right(), g.get_left(), buff=0.1, color=MUTED, stroke_width=2, max_tip_length_to_length_ratio=0.12) for g in gens])
        gf_lab = T("generating functions", 19, GCIM).next_to(kets, UP, buff=0.25)
        hmat, smat = grid(4), grid(4)
        hmat.move_to([-0.3, 0.6, 0])
        smat.move_to([-0.3, -1.9, 0])
        hlab = M("H_(i j) = chevron.l psi_i | H | psi_j chevron.r", 0.8, SOLVE).next_to(hmat, DOWN, buff=0.3)
        slab = M("S_(i j) = chevron.l psi_i | psi_j chevron.r", 0.8, SOLVE).next_to(smat, DOWN, buff=0.3)
        hw = M('bold(H) thin bold(f) = E thin bold(S) thin bold(f)', 1.4, SOLVE).move_to([4.3, 0.6, 0])
        hw_lab = VGroup(T("Hill–Wheeler equation", 21, SOLVE, weight=MEDIUM), T("one generalized eigenvalue solve", 18, MUTED)).arrange(DOWN, buff=0.08).next_to(hw, DOWN, buff=0.3)
        levels = VGroup(*[VGroup(Line(LEFT * 0.5, RIGHT * 0.5, color=INK, stroke_width=3), M(f"E_{i}", 0.7)).arrange(RIGHT, buff=0.15) for i in range(3)])
        for i, l in enumerate(levels):
            l.move_to([4.3, -2.9 + 0.45 * i, 0])
        lv_lab = T("ground and excited states", 17, MUTED).next_to(levels, RIGHT, buff=0.25)

        with self.voice("gcm") as v:
            self.play(FadeIn(head), FadeIn(cite, shift=0.1 * DOWN), run_time=1.2)
            v.until(1)
            self.play(FadeIn(ref), LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(g) for g in gens], lag_ratio=0.2), run_time=0.9)
            self.play(LaggedStart(*[FadeIn(k, shift=0.1 * RIGHT) for k in kets], lag_ratio=0.2), FadeIn(gf_lab), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(s, scale=0.6) for s in hmat], lag_ratio=0.03), FadeIn(hlab), run_time=1.4)
            self.play(LaggedStart(*[FadeIn(s, scale=0.6) for s in smat], lag_ratio=0.03), FadeIn(slab), run_time=1.4)
            v.until(2)
            self.play(Write(hw), FadeIn(hw_lab), run_time=1.6)
            self.play(LaggedStart(*[Create(l) for l in levels], lag_ratio=0.3), FadeIn(lv_lab), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def toy(self):
        head = header(3, "A two-electron toy model")
        panels = VGroup(config_panel((0, 1), "ket(phi_0)"), config_panel((2, 1), "ket(phi_1)"),
                        config_panel((0, 3), "ket(phi_2)"), config_panel((2, 3), "ket(phi_3)")).arrange(RIGHT, buff=0.6)
        panels.move_to([-3.5, 1.6, 0])
        conf_lab = T("four configurations, 2 electrons in 4 spin orbitals", 18, MUTED).next_to(panels, UP, buff=0.25)
        vqe = M('ket(psi_"VQE" (bold(theta))) = G_(2,4)(theta_2) thin G_(1,3)(theta_1) ket(phi_0)', 1.0, VQE).move_to([-3.5, -0.9, 0])
        vqe_lab = VGroup(T("VQE: 2 free parameters", 20, VQE, weight=MEDIUM), T("for 4 configuration amplitudes", 18, MUTED)).arrange(DOWN, buff=0.08).next_to(vqe, DOWN, buff=0.3)
        basis = VGroup(
            M("ket(psi_0) = ket(phi_0)", 0.85, GCIM),
            M("ket(psi_1) = G_(1,3) ket(phi_0)", 0.85, GCIM),
            M("ket(psi_2) = G_(2,4) ket(phi_0)", 0.85, GCIM),
            M("ket(psi_3) = G_(2,4) G_(1,3) ket(phi_0)", 0.85, GCIM),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        basis.move_to([0.3, 1.2, 0], aligned_edge=LEFT)
        spans = VGroup(*[M(s, 0.75, MUTED) for s in ("{phi_0}", "{phi_0, phi_1}", "{phi_0, phi_2}", "{phi_0, phi_1, phi_2, phi_3}")])
        for s, b in zip(spans, basis):
            s.move_to([basis.get_right()[0] + 0.45, b.get_center()[1], 0], aligned_edge=LEFT)
        gcim_lab = T("GCIM: 4 generating functions from the same rotations", 19, GCIM, weight=MEDIUM).next_to(basis, UP, buff=0.3).align_to(basis, LEFT)
        bound = M('E_"exact" lt.eq #c("' + GCIM + '", $E_"GCIM"$) lt.eq #c("' + VQE + '", $E_"VQE"$)', 1.4).move_to([3.6, -1.9, 0])
        bound_box = SurroundingRectangle(bound, color=LINE, buff=0.25, corner_radius=0.1)

        with self.voice("toy") as v:
            self.play(FadeIn(head), FadeIn(conf_lab), LaggedStart(*[FadeIn(p, shift=0.1 * UP) for p in panels], lag_ratio=0.2), run_time=1.6)
            v.until(1)
            self.play(Write(vqe), run_time=1.6)
            self.play(FadeIn(vqe_lab), run_time=0.6)
            v.until(2)
            self.play(FadeIn(gcim_lab), run_time=0.5)
            for b, s in zip(basis, spans):
                self.play(FadeIn(b, shift=0.1 * RIGHT), FadeIn(s), run_time=0.7)
            v.until(3)
            self.play(Create(bound_box), Write(bound), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def choose(self):
        head = header(4, "Which generating functions?")
        ax = Axes(x_range=[0, 12, 2], y_range=[0, 1100, 500], x_length=6.6, y_length=4.0, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-2.2, -0.4, 0])
        ks = np.arange(1, 11)
        allp = VGroup(*[Rectangle(width=0.4, height=ax.y_axis.unit_size * 2 ** k, stroke_width=0, fill_color=MUTED, fill_opacity=0.5)
                        .move_to(ax.c2p(k, 0), aligned_edge=DOWN) for k in ks])
        ticks = VGroup(*[T(str(k), 15, MUTED).next_to(ax.c2p(k, 0), DOWN, buff=0.1) for k in (2, 4, 6, 8, 10)])
        xlab = T("number of rotations K", 17, MUTED).next_to(ticks, DOWN, buff=0.1)
        ylab = T("generating functions", 17, MUTED).next_to(ax.y_axis, UP, buff=0.1)
        all_lab = M('2^K "from all products"', 0.9, MUTED).move_to(ax.c2p(4.5, 800))
        prior = card([T("original GCIM", 22, GCIM, weight=MEDIUM), T("generating functions chosen with", 19, INK),
                      T("prior knowledge of the molecule", 19, INK)], 4.2, GCIM).move_to([4.6, 0.3, 0])
        with self.voice("choose") as v:
            self.play(FadeIn(head), Create(ax), FadeIn(ticks), FadeIn(xlab), FadeIn(ylab), run_time=1.0)
            v.until(1)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in allp], lag_ratio=0.12), FadeIn(all_lab), run_time=2.4)
            self.play(FadeIn(prior, shift=0.1 * LEFT), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def adapt(self):
        head = header(5, "ADAPT-GCIM")
        steps = VGroup(
            card([T("operator pool", 21, GCIM, weight=MEDIUM), T("UCC excitations", 18, MUTED), M("G_k = e^(theta_k (A_k - A_k^dagger))", 0.7, MUTED)], 3.6, GCIM),
            card([T("select the largest gradient", 21, GCIM, weight=MEDIUM), T("on a surrogate state", 18, MUTED), T("angle fixed, not optimized", 18, MUTED)], 3.6, GCIM),
            card([T("add 2 generating functions", 21, GCIM, weight=MEDIUM), M("G_k ket(phi), quad G_k product_(i<k) G_i ket(phi)", 0.7, MUTED)], 3.6, GCIM),
            card([T("solve", 21, SOLVE, weight=MEDIUM), M('bold(H) thin bold(f) = E thin bold(S) thin bold(f)', 0.9, SOLVE), T("until E stops changing", 18, MUTED)], 3.6, SOLVE),
        )
        positions = [[-4.7, 1.3, 0], [-0.4, 1.3, 0], [-0.4, -1.4, 0], [-4.7, -1.4, 0]]
        for s, p in zip(steps, positions):
            s.move_to(p)
        arrows = VGroup(*[Arrow(steps[i].get_edge_center(d), steps[(i + 1) % 4].get_edge_center(-d), buff=0.1, color=MUTED, stroke_width=3,
                                max_tip_length_to_length_ratio=0.2) for i, d in enumerate((RIGHT, DOWN, LEFT, UP))])
        size_lab = T("basis size", 18, MUTED).move_to([4.6, 2.5, 0])
        mats = [grid(n, 0.3).move_to([4.6, 0.2, 0]) for n in (2, 4, 6, 8)]
        counts = [T(f"{n} functions", 20, SOLVE).move_to([4.6, -2.0, 0]) for n in (2, 4, 6, 8)]
        no_opt = T("no circuit parameter optimization", 26, GCIM, weight=MEDIUM).move_to([0, -3.3, 0])

        with self.voice("adapt") as v:
            self.play(FadeIn(head), FadeIn(steps[0]), run_time=1.0)
            v.until(1)
            self.play(GrowArrow(arrows[0]), FadeIn(steps[1], shift=0.1 * RIGHT), run_time=1.0)
            self.play(Indicate(steps[1], color=GCIM, scale_factor=1.04), run_time=1.2)
            v.until(2)
            self.play(GrowArrow(arrows[1]), FadeIn(steps[2], shift=0.1 * DOWN), run_time=0.9)
            self.play(GrowArrow(arrows[2]), FadeIn(steps[3], shift=0.1 * LEFT), GrowArrow(arrows[3]), run_time=1.0)
            self.play(FadeIn(size_lab), FadeIn(mats[0]), FadeIn(counts[0]), run_time=0.6)
            for i in range(1, 4):
                self.play(FadeTransform(mats[i - 1], mats[i]), FadeTransform(counts[i - 1], counts[i]), run_time=0.7)
            v.until(3)
            self.play(FadeIn(no_opt, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def results(self):
        head = header(6, "Results")
        mols = VGroup(*[card([T(m, 18, INK)], 1.0, LINE, pad=0.14) for m in
                        ("H4 linear", "H4 square", "LiH", "BeH2", "H6 1.06 Å", "H6 1.85 Å", "H6 5.00 Å")]).arrange(RIGHT, buff=0.18)
        mols.move_to([0, 2.6, 0])
        mol_lab = T("STO-3G basis, seven geometries", 17, MUTED).next_to(mols, DOWN, buff=0.15)
        ax = Axes(x_range=[0, 92, 20], y_range=[-9, 0, 3], x_length=7.2, y_length=3.9, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-2.2, -0.9, 0])
        band = Polygon(ax.c2p(0, -9), ax.c2p(92, -9), ax.c2p(92, np.log10(1.6e-3)), ax.c2p(0, np.log10(1.6e-3)),
                       stroke_width=0, fill_color=DV, fill_opacity=0.07)
        band_lab = T("chemical accuracy", 15, MUTED).next_to(ax.c2p(0, np.log10(1.6e-3)), DR, buff=0.08)

        def trace(errs, color):
            pts = [ax.c2p(i + 1, max(np.log10(e), -9)) for i, e in enumerate(errs)]
            return VMobject(stroke_color=color, stroke_width=3.5).set_points_as_corners(pts)
        g_curve, v_curve = trace(DATA["adapt_gcim"], GCIM), trace(DATA["adapt_vqe"], VQE)
        yt = VGroup(*[T(s, 15, MUTED).next_to(ax.c2p(0, p), LEFT, buff=0.1) for s, p in (("10⁰", 0), ("10⁻³", -3), ("10⁻⁶", -6), ("10⁻⁹", -9))])
        xt = VGroup(*[T(str(n), 15, MUTED).next_to(ax.c2p(n, -9), DOWN, buff=0.1) for n in (0, 20, 40, 60, 80)])
        xl = T("ADAPT iteration", 16, MUTED).next_to(xt, DOWN, buff=0.08)
        yl = T("energy error (hartree)", 16, MUTED).next_to(ax, UP, buff=0.12).align_to(ax, LEFT)
        title = T("H6 at 5.0 Å, strongly correlated", 19, INK, weight=MEDIUM).next_to(yl, RIGHT, buff=0.5)
        g37 = DATA["adapt_gcim"][36]
        v84 = DATA["adapt_vqe"][83]
        g_mark = VGroup(Dot(ax.c2p(37, np.log10(g37)), radius=0.08, color=GCIM),
                        T("ADAPT-GCIM, 37 iterations: 9.6 × 10⁻⁸", 16, GCIM))
        g_mark[1].next_to(g_mark[0], DOWN, buff=0.15)
        v_dot = Dot(ax.c2p(84, np.log10(v84)), radius=0.08, color=VQE)
        v_text = T("ADAPT-VQE, 84 iterations: 1.2 × 10⁻⁶", 16, VQE).move_to(ax.c2p(58, -1.3))
        v_mark = VGroup(v_dot, v_text, Line(v_text.get_bottom() + 1.0 * RIGHT, v_dot.get_top(), color=VQE, stroke_width=1.5))

        per = 0.55  # units per decade of seconds
        x0 = 2.2

        def tbar(seconds, y, color, label):
            bar = Rectangle(width=per * np.log10(seconds), height=0.34, stroke_width=0, fill_color=color, fill_opacity=0.9)
            bar.move_to([x0, y, 0], aligned_edge=LEFT)
            return VGroup(bar, T(label, 17, color).next_to(bar, RIGHT, buff=0.12))
        tb = VGroup(tbar(12.03, -0.2, GCIM, "12 s"), tbar(12765.16, -0.8, VQE, "12,765 s ≈ 3.5 h"))
        tb_axis = VGroup(*[VGroup(Line([x0 + per * p, -1.15, 0], [x0 + per * p, -1.25, 0], color=MUTED, stroke_width=2),
                                  T(s, 14, MUTED).next_to([x0 + per * p, -1.25, 0], DOWN, buff=0.05))
                           for p, s in ((0, "1 s"), (2, "100 s"), (4, "10⁴ s"))])
        tb_title = VGroup(T("energy evaluations, same laptop", 18, INK, weight=MEDIUM), T("log scale", 15, MUTED)).arrange(RIGHT, buff=0.2)
        tb_title.next_to(tb, UP, buff=0.3).align_to(tb, LEFT)
        rounds = VGroup(T("optimization rounds", 17, MUTED), T("ADAPT-GCIM 0", 17, GCIM), T("ADAPT-VQE 11,313", 17, VQE)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        rounds.next_to(tb_axis, DOWN, buff=0.4).align_to(tb, LEFT)

        with self.voice("results") as v:
            self.play(FadeIn(head), LaggedStart(*[FadeIn(m, shift=0.1 * DOWN) for m in mols], lag_ratio=0.12), FadeIn(mol_lab), run_time=1.8)
            v.until(1)
            self.play(Indicate(mols[-1], color=ACCENT, scale_factor=1.08), Create(ax), FadeIn(band), FadeIn(band_lab),
                      FadeIn(VGroup(yt, xt, xl, yl, title)), run_time=1.2)
            self.play(Create(v_curve), Create(g_curve), run_time=v.dur(1) * 0.45, rate_func=linear)
            self.play(FadeIn(g_mark), run_time=0.8)
            self.play(FadeIn(v_mark), run_time=0.8)
            v.until(2)
            self.play(FadeIn(tb_title), FadeIn(tb_axis), run_time=0.6)
            self.play(GrowFromEdge(tb[0][0], LEFT), FadeIn(tb[0][1]), run_time=0.8)
            self.play(GrowFromEdge(tb[1][0], LEFT), FadeIn(tb[1][1]), run_time=1.6)
            self.play(FadeIn(rounds, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def costs(self):
        head = header(7, "Costs and limits")
        meas = VGroup(T("measurements", 22, INK, weight=MEDIUM),
                      VGroup(T("ADAPT-GCIM", 19, GCIM), M('cal(O)(N_"iter"^2)', 0.9, GCIM)).arrange(RIGHT, buff=0.25),
                      VGroup(T("ADAPT-VQE", 19, VQE), M('cal(O)(tilde(N)_"opt" N_"iter")', 0.9, VQE)).arrange(RIGHT, buff=0.25),
                      T("H and S grow with the square of the basis size", 17, MUTED),
                      T("nearly singular S: keep eigenvectors with large eigenvalues", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        meas.move_to([-3.6, 1.1, 0])
        table = VGroup()
        for i, row in enumerate([(" ", "GCIM", "VQE", "GCIM(5,2)"), *[(n, str(a), str(b), str(c)) for n, a, b, c in ITERATIONS]]):
            colors = (INK, GCIM, VQE, GCIM)
            cells = VGroup(*[T(cell, 18, col, weight=MEDIUM if i == 0 else NORMAL) for cell, col in zip(row, colors)])
            for j, c in enumerate(cells):
                c.move_to([1.0 + [0, 2.4, 3.6, 4.9][j], 1.9 - 0.5 * i, 0], aligned_edge=LEFT if j == 0 else ORIGIN)
            table.add(cells)
        table_title = T("minimum ADAPT iterations, H6", 19, INK, weight=MEDIUM).next_to(table, UP, buff=0.3).align_to(table, LEFT)
        hw = card([T("first hardware test · ibm_osaka · linear H4", 20, VQE, weight=MEDIUM),
                   VGroup(T("ground-state energy error", 19, INK), M('0.046 arrow.r 3.9 times 10^(-9) "hartree"', 0.9, INK)).arrange(RIGHT, buff=0.3),
                   T("with problem-specific error mitigation", 17, MUTED)], 8.0, VQE).move_to([0, -2.3, 0])

        with self.voice("costs") as v:
            self.play(FadeIn(head), LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in meas], lag_ratio=0.35), run_time=3.0)
            v.until(1)
            self.play(FadeIn(table_title), LaggedStart(*[FadeIn(r) for r in table], lag_ratio=0.3), run_time=1.8)
            self.play(Indicate(table[2][3], color=GCIM, scale_factor=1.2), Indicate(table[1][3], color=GCIM, scale_factor=1.2), run_time=1.2)
            v.until(2)
            self.play(FadeIn(hw, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def link(self):
        head = header(8, "Used again")
        c = card([T("Coupled cluster downfolding on quantum hardware", 24, INK, weight=MEDIUM),
                  T("Phys. Rev. Research 8, 013072 (2026)", 18, MUTED),
                  T("ADAPT-GCIM solved downfolded (6e, 6o) Hamiltonians for", 20, INK),
                  T("benzene and free-base porphyrin, within 0.1 mhartree of exact diagonalization", 20, INK)], 10.0, GCIM)
        c.move_to([0, 0.3, 0])
        with self.voice("link") as v:
            self.play(FadeIn(head), FadeIn(c, shift=0.1 * UP), run_time=1.2)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("A generalized eigenvalue problem over adaptively chosen", 30, weight=MEDIUM),
                       T("generating functions takes the place of parameter optimization.", 30, weight=MEDIUM),
                       T("The cost moves to measuring the Hamiltonian and overlap matrices.", 22, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lines[2].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the papers"),
                      T("Zheng, Peng, Li, Yang, Kowalski. npj Quantum Information 10, 127 (2024)", 20),
                      T("doi.org/10.1038/s41534-024-00916-8   ·   arXiv:2312.07691", 20, ACCENT),
                      T("Earlier: Zheng et al. Phys. Rev. Research 5, 023200 (2023)   ·   arXiv:2212.09205", 20, MUTED),
                      T("Code and data: github.com/pnnl/QuGCM", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.4)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class GCIMPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Generator coordinate inspired method", size=30).to_corner(UL, buff=0.6)
        hw = M('bold(H) thin bold(f) = E thin bold(S) thin bold(f)', 3.2, SOLVE).move_to([-2.4, 0.3, 0])
        mats = VGroup(grid(6, 0.42), grid(6, 0.42)).arrange(RIGHT, buff=0.5).move_to([4.2, 0.3, 0])
        sub = T("no parameter optimization", 40, ACCENT, weight=MEDIUM).move_to([0, -2.6, 0])
        self.add(label, hw, mats, sub)
