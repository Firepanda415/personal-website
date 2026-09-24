"""Explainer for "Gate-level quantum simulation of nonunitary linear dynamics with
hybrid oscillator-qubit architecture" (Das, Zheng, Dutta, Li, Stavenger, Liu, 2026).

Plotted kernel data come from data.json (see extract_data.py). Table values are
quoted from arXiv:2605.10708v3, Tables 4, 6, 7 and 8.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *
from kernel import C, DATA, g_beta, phi_r, psi_N, overlap_scale

# Heat equation on [0, 1] with Dirichlet ends, as a sine series of a bump.
_X = np.linspace(0, 1, 401)
_MODES = np.arange(1, 80)
_B = 2 * np.trapezoid(np.exp(-((_X - 0.32) / 0.07) ** 2) * np.sin(np.pi * _MODES[:, None] * _X), _X, axis=1)


def heat(x, t):
    x = np.atleast_1d(x)
    return (_B[:, None] * np.sin(np.pi * _MODES[:, None] * x) * np.exp(-(np.pi * _MODES[:, None]) ** 2 * t)).sum(0)


# Quadrature grid for the scalar LCHS identity  int g(k) e^{-ik y} dk = e^{-y}.
_K = np.linspace(-150, 150, 6001)
_W = g_beta(_K) * (_K[1] - _K[0])

# Fixed-scale map errors (percent), Tables 4, 6 and 8.
ROWS = [
    ("Heat 1D, M = 4, Dirichlet", 0.70, 12.82),
    ("Heat 1D, M = 4, Neumann", 0.56, 16.48),
    ("Heat 1D, M = 4, periodic", 0.47, 4.38),
    ("Heat 1D, M = 8", 1.04, 8.14),
    ("Heat 1D, M = 16", 1.46, 7.92),
    ("Heat 1D, M = 32", 1.46, 7.98),
    ("Advection–diffusion, M = 8", 1.15, 8.10),
    ("Advection–diffusion, M = 16", 1.48, 7.94),
    ("Advection–diffusion, M = 32", 1.47, 7.99),
    ("Heat 2D, 4 × 4", 7.40, 9.87),
]


class LCHSExplainer(Explainer):
    timing_file = BUILD / "lchs" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.lchs()
        self.qubits()
        self.oscillator()
        self.kernel_loading()
        self.finite_resources()
        self.gates()
        self.postselection()
        self.results()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("Quantum Science and Technology · 2026")
        title = VGroup(T("Gate-level quantum simulation of", 44, weight=MEDIUM),
                       T("nonunitary linear dynamics with hybrid", 44, weight=MEDIUM),
                       T("oscillator–qubit architecture", 44, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = T("Elin Ranjan Das, Muqing Zheng, Rishab Dutta, Ang Li, Timothy Stavenger, Yuan Liu", 22, color=MUTED)
        places = T("North Carolina State University · Pacific Northwest National Laboratory · University of Washington", 18, color=MUTED)
        block = VGroup(venue, title, authors, places).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        authors.shift(0.15 * DOWN)
        places.next_to(authors, DOWN, buff=0.15, aligned_edge=LEFT)
        block.move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(block.get_corner(UL) + 0.35 * UP, block.get_corner(UL) + 0.35 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        self.play(Create(rule), FadeIn(venue, shift=0.1 * RIGHT), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in (title, authors, places)], lag_ratio=0.25), run_time=1.6)
        self.wait(2.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 01
    def problem(self):
        head = header(1, "Decaying linear dynamics")
        axes = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.05, 0.5], x_length=6.6, y_length=3.0, tips=False,
                    axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-2.6, 0.55, 0])
        ulab = M("u(x, t)", 0.8, MUTED).next_to(axes.y_axis, UP, buff=0.15)
        t = ValueTracker(0.0)
        curve = always_redraw(lambda: axes.plot(lambda x: float(heat(x, t.get_value())[0]), x_range=[0, 1, 0.005],
                                                color=ACCENT, stroke_width=4))

        def rod():
            xs = np.linspace(0, 1, 70)
            u = np.clip(heat(xs, t.get_value()), 0, 1)
            w = axes.x_length / len(xs)
            strips = VGroup(*[Rectangle(width=w * 1.02, height=0.34, stroke_width=0,
                                        fill_color=interpolate_color(ManimColor(WASH), ManimColor(ACCENT), ui), fill_opacity=1)
                              .move_to(axes.c2p(x, 0) + 0.62 * DOWN) for x, ui in zip(xs, u)])
            return VGroup(strips, SurroundingRectangle(strips, buff=0, color=MUTED, stroke_width=1.5))
        bar = always_redraw(rod)
        grid = np.arange(1, 9) / 9
        # Fade the samples in through their own opacity, so they follow the curve on every frame.
        shown = ValueTracker(0.0)
        dots = always_redraw(lambda: VGroup(*[
            VGroup(Line(axes.c2p(x, 0), axes.c2p(x, float(heat(x, t.get_value())[0])), color=MUTED, stroke_width=1.5,
                        stroke_opacity=0.7 * shown.get_value()),
                   Dot(axes.c2p(x, float(heat(x, t.get_value())[0])), radius=0.07, color=INK, fill_opacity=shown.get_value()))
            for x in grid]))
        vec = M("u = vec(u_1, u_2, dots.v, u_8)", 1.1).move_to([3.4, 1.1, 0])
        ode = M("(dif u)/(dif t) = -A u", 1.4).move_to([3.4, -1.5, 0])

        with self.voice("problem") as v:
            self.play(FadeIn(head), Create(axes), FadeIn(ulab), FadeIn(bar), Create(curve), run_time=1.0)
            self.play(t.animate.set_value(0.0045), run_time=v.dur(0) - 0.7, rate_func=linear)
            v.until(1)
            self.add(dots)
            self.play(shown.animate.set_value(1), t.animate.set_value(0.0065), run_time=1.6, rate_func=linear)
            self.play(Write(vec), t.animate.set_value(0.0085), run_time=2.0, rate_func=linear)
            self.play(Write(ode), t.animate.set_value(0.011), run_time=v.left() - 0.2, rate_func=linear)

        for m in (curve, bar, dots):
            m.clear_updaters()
        split = M('A = #c("' + ACCENT + '", $L$) + i #c("' + DV + '", $H$)', 1.6).move_to([0, 1.6, 0])
        l_lab = VGroup(T("dissipative", 26, ACCENT), M("L = L^dagger succ.eq 0", 0.95)).arrange(DOWN, buff=0.15)
        h_lab = VGroup(T("Hermitian", 26, DV), M("H = H^dagger", 0.95)).arrange(DOWN, buff=0.15)
        l_lab.next_to(part(split, ACCENT), DOWN, buff=0.55).shift(1.3 * LEFT)
        h_lab.next_to(part(split, DV), DOWN, buff=0.55).shift(1.3 * RIGHT)
        l_arrow = Arrow(part(split, ACCENT).get_bottom(), l_lab.get_top(), buff=0.1, color=ACCENT, stroke_width=3)
        h_arrow = Arrow(part(split, DV).get_bottom(), h_lab.get_top(), buff=0.1, color=DV, stroke_width=3)
        norm = M("dif / (dif t) norm(u)^2 = -2 thin u^dagger #c(\"" + ACCENT + "\", $L$) thin u lt.eq 0", 1.2).move_to([0, -2.4, 0])
        with self.voice("split") as v:
            self.play(FadeOut(VGroup(axes, ulab, curve, bar, dots, vec)), ode.animate.scale(0.8).to_corner(UR, buff=0.6), run_time=0.8)
            self.play(Write(split), run_time=1.2)
            self.play(GrowArrow(l_arrow), FadeIn(l_lab, shift=0.1 * DOWN), run_time=0.9)
            self.play(GrowArrow(h_arrow), FadeIn(h_lab, shift=0.1 * DOWN), run_time=0.9)
            v.until(1)
            self.play(Write(norm), run_time=1.6)
        self.clear_stage(keep=[head])

        left_c, right_c = np.array([-3.4, 0.2, 0]), np.array([3.4, 0.2, 0])
        circ = Circle(radius=1.6, color=LINE, stroke_width=2).move_to(left_c)
        ang = ValueTracker(0.3)
        uvec = always_redraw(lambda: Arrow(left_c, left_c + 1.6 * np.array([np.cos(ang.get_value()), np.sin(ang.get_value()), 0]),
                                           buff=0, color=DV, stroke_width=6, max_tip_length_to_length_ratio=0.14))
        u_lab = VGroup(T("unitary evolution", 28, DV), M("norm(U v) = norm(v)", 1.0)).arrange(DOWN, buff=0.2).next_to(circ, DOWN, buff=0.45)
        circ2 = Circle(radius=1.6, color=LINE, stroke_width=2).move_to(right_c)
        th = ValueTracker(0.3)
        spiral = lambda s: right_c + 1.6 * np.exp(-0.22 * (s - 0.3)) * np.array([np.cos(s), np.sin(s), 0])
        svec = always_redraw(lambda: Arrow(right_c, spiral(th.get_value()), buff=0, color=ACCENT, stroke_width=6,
                                           max_tip_length_to_length_ratio=0.14))
        trail = always_redraw(lambda: ParametricFunction(spiral, t_range=[0.3, max(th.get_value(), 0.31)], color=ACCENT,
                                                         stroke_width=2, stroke_opacity=0.5))
        s_lab = VGroup(T("the solution", 28, ACCENT), M("norm(e^(-A t) u_0) arrow.b", 1.0)).arrange(DOWN, buff=0.2).next_to(circ2, DOWN, buff=0.45)
        verdict = T("not a unitary on the system alone", 26, ACCENT).next_to(s_lab, DOWN, buff=0.3)
        with self.voice("unitary") as v:
            self.play(Create(circ), GrowArrow(uvec), FadeIn(u_lab), run_time=1.0)
            self.play(ang.animate.set_value(0.3 + 2 * PI), run_time=v.dur(0) - 1.0, rate_func=linear)
            v.until(1)
            self.add(trail)
            self.play(Create(circ2), GrowArrow(svec), FadeIn(s_lab), run_time=0.8)
            self.play(th.animate.set_value(0.3 + 3.2 * PI), ang.animate.set_value(0.3 + 5 * PI), run_time=v.dur(1) - 1.2, rate_func=linear)
            self.play(FadeIn(verdict, shift=0.1 * UP), run_time=0.5)
        for m in (uvec, svec, trail):
            m.clear_updaters()
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def lchs(self):
        head = header(2, "Linear combination of Hamiltonian simulation")
        eq = M('e^(-A t) = integral_RR #c("' + ACCENT + '", $g(k)$) thin #c("' + DV + '", $e^(-i t (k L + H))$) dif k', 1.45).move_to([0, 2.3, 0])
        wlab = T("weight", 24, ACCENT).next_to(part(eq, ACCENT), DOWN, buff=0.45)
        ulab = T("unitary for each k", 24, DV).next_to(part(eq, DV), DOWN, buff=0.45)
        wbr = Line(part(eq, ACCENT).get_corner(DL) + 0.12 * DOWN, part(eq, ACCENT).get_corner(DR) + 0.12 * DOWN, color=ACCENT, stroke_width=3)
        ubr = Line(part(eq, DV).get_corner(DL) + 0.12 * DOWN, part(eq, DV).get_corner(DR) + 0.12 * DOWN, color=DV, stroke_width=3)

        gax = Axes(x_range=[-6, 6, 2], y_range=[-0.1, 0.27, 0.1], x_length=5.6, y_length=2.6, tips=False,
                   axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-3.5, -1.6, 0])
        re_g = gax.plot(lambda k: float(g_beta(k).real), x_range=[-6, 6, 0.02], color=ACCENT, stroke_width=4)
        im_g = DashedVMobject(gax.plot(lambda k: float(g_beta(k).imag), x_range=[-6, 6, 0.02], color=GOLD, stroke_width=3), num_dashes=60)
        glabs = VGroup(M("op(\"Re\") g(k)", 0.75, ACCENT), M("op(\"Im\") g(k)", 0.75, GOLD)).arrange(RIGHT, buff=0.5).next_to(gax, UP, buff=0.1)
        klab = M("k", 0.8, MUTED).next_to(gax.x_axis, RIGHT, buff=0.1)

        plane = Axes(x_range=[-0.1, 1.05, 0.5], y_range=[-0.1, 0.25, 0.1], x_length=5.6, y_length=5.6 * 0.35 / 1.15, tips=False,
                     axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([3.4, -1.45, 0])
        y = ValueTracker(0.0)

        def chain():
            z = np.concatenate([[0], np.cumsum(_W * np.exp(-1j * _K * y.get_value()))])
            pts = [plane.c2p(p.real, p.imag) for p in z[::2]]
            return VMobject(stroke_color=DV, stroke_width=2.5).set_points_as_corners(pts)
        path = always_redraw(chain)
        tip = always_redraw(lambda: Dot(plane.c2p(float(np.exp(-y.get_value())), 0), radius=0.08, color=ACCENT))
        one = VGroup(Line(plane.c2p(1, -0.03), plane.c2p(1, 0.03), color=MUTED, stroke_width=2),
                     M("1", 0.7, MUTED).next_to(plane.c2p(1, -0.03), DOWN, buff=0.1))
        pl_title = VGroup(T("single decay rate", 22, MUTED), M("L = lambda, H = 0", 0.8, MUTED)).arrange(RIGHT, buff=0.25).next_to(plane, UP, buff=0.35)
        rd_eq = M('#c("' + ACCENT + '", $sum$) = e^(-lambda t), quad lambda t =', 0.85)
        rd_eq.next_to(plane, DOWN, buff=0.35).shift(0.4 * LEFT)
        rd_val = always_redraw(lambda: T(f"{y.get_value():.2f}", 26).next_to(rd_eq, RIGHT, buff=0.15))
        readout = VGroup(rd_eq, rd_val)
        phasor_lab = T("each branch: a pure rotation", 20, DV).next_to(pl_title, UP, buff=0.12)

        with self.voice("lchs") as v:
            self.play(FadeIn(head), run_time=0.5)
            self.play(Write(eq), run_time=2.4)
            v.until(1)
            self.play(Create(wbr), FadeIn(wlab), run_time=0.8)
            self.play(Create(ubr), FadeIn(ulab), run_time=0.8)
            self.play(Create(gax), FadeIn(klab), Create(re_g), Create(im_g), FadeIn(glabs), run_time=2.0)
            v.until(2)
            self.play(Create(plane), FadeIn(pl_title), FadeIn(one), Create(path), FadeIn(tip), FadeIn(readout), FadeIn(phasor_lab), run_time=1.2)
            self.play(y.animate.set_value(2.4), run_time=v.dur(2) - 1.2, rate_func=smooth)
        for m in (path, tip):
            m.clear_updaters()
        rd_val.clear_updaters()
        self.lchs_mobs = dict(head=head, eq=eq, gax=gax, re_g=re_g, rest=VGroup(wbr, ubr, wlab, ulab, im_g, glabs, klab, plane, path, tip, one, pl_title, readout, phasor_lab))

    # ------------------------------------------------------------------ 03
    def qubits(self):
        o = self.lchs_mobs
        head = header(3, "LCHS on qubits")
        eq = M('e^(-A t) approx sum_(j=1)^(M) #c("' + ACCENT + '", $c_j$) thin #c("' + DV + '", $e^(-i t (k_j L + H))$)', 1.45).move_to(o["eq"])
        nodes = np.linspace(-5.5, 5.5, 23)
        stems = VGroup(*[VGroup(Line(o["gax"].c2p(k, 0), o["gax"].c2p(k, float(g_beta(k).real)), color=ACCENT, stroke_width=3),
                                Dot(o["gax"].c2p(k, float(g_beta(k).real)), radius=0.05, color=ACCENT)) for k in nodes])

        x0, x1 = 0.6, 6.6
        anc_y = [0.9, 0.55, 0.2, -0.15, -0.5]
        sys_y = [-1.35, -1.7, -2.05]
        anc = VGroup(*[wire(yy, x0, x1, DV) for yy in anc_y])
        syst = VGroup(*[wire(yy, x0, x1) for yy in sys_y])
        anc_lab = M("ket(0)^(times.o m_c)", 0.8, DV).next_to(anc, LEFT, buff=0.15)
        sys_lab = M("ket(u_0)", 0.85).next_to(syst, LEFT, buff=0.15)
        prep = gate('"PREP"', 1.0, 1.55, DV, 0.7).move_to([1.6, np.mean(anc_y), 0])
        unprep = gate('"PREP"^dagger', 1.0, 1.55, DV, 0.7).move_to([5.0, np.mean(anc_y), 0])
        sel = gate('e^(-i t (k_j L + H))', 1.5, 1.05, INK, 0.75).move_to([3.3, np.mean(sys_y), 0])
        ctrl = VGroup(*[Dot([3.3, yy, 0], radius=0.07, color=DV) for yy in anc_y],
                      Line([3.3, anc_y[0], 0], sel.get_top(), color=DV, stroke_width=2.5))
        meas = VGroup(*[meter(DV).scale(0.48).move_to([6.1, yy, 0]) for yy in anc_y])
        circuit = VGroup(anc, syst, anc_lab, sys_lab, ctrl, sel, prep, unprep, meas)
        size_card = card([T("standard sizing rule, ε = 0.1", 20, MUTED),
                          T("192–632 quadrature terms", 26, DV, weight=MEDIUM),
                          T("8–10 ancilla qubits", 26, DV, weight=MEDIUM)], 4.0, DV).move_to([3.6, -3.05, 0])

        with self.voice("dv") as v:
            self.play(FadeOut(o["rest"]), ReplacementTransform(o["head"], head), ReplacementTransform(o["eq"], eq), run_time=1.0)
            self.play(LaggedStart(*[GrowFromEdge(s, DOWN) for s in stems], lag_ratio=0.06), o["re_g"].animate.set_stroke(opacity=0.35), run_time=1.6)
            v.until(1)
            self.play(Create(anc), Create(syst), FadeIn(anc_lab), FadeIn(sys_lab), run_time=1.0)
            self.play(FadeIn(prep), run_time=0.5)
            self.play(Create(ctrl), FadeIn(sel), run_time=0.9)
            self.play(FadeIn(unprep), FadeIn(meas), run_time=0.6)
            v.until(2)
            self.play(Circumscribe(anc, color=DV, buff=0.12, run_time=1.4), FadeIn(size_card, shift=0.1 * UP), run_time=1.4)
        self.dv_mobs = dict(head=head, eq=eq, circuit=circuit, anc=anc, prep=prep, unprep=unprep, sel=sel, ctrl=ctrl, meas=meas,
                            anc_lab=anc_lab, sys_lab=sys_lab, syst=syst, rest=VGroup(stems, o["gax"], o["re_g"], size_card))

    # ------------------------------------------------------------------ 04
    def oscillator(self):
        o = self.dv_mobs
        head = header(4, "One oscillator in place of the register")
        well_ax = Axes(x_range=[-3, 3, 1], y_range=[0, 2.4, 1], x_length=4.8, y_length=2.4, tips=False,
                       axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-3.9, 0.6, 0])
        well = well_ax.plot(lambda x: 0.22 * x**2, x_range=[-3, 3], color=MUTED, stroke_width=2.5)
        wave = well_ax.plot(lambda x: 0.35 + 1.2 * np.exp(-x**2 / 1.4), x_range=[-3, 3], color=CV, stroke_width=4)
        xlab = VGroup(T("position", 22, CV), M("x in RR", 0.8, CV)).arrange(RIGHT, buff=0.15).next_to(well_ax, DOWN, buff=0.15)
        osc_title = T("harmonic oscillator", 24, CV, weight=MEDIUM).next_to(well_ax, UP, buff=0.2)

        x0, x1 = 0.6, 6.6
        cv_y = np.mean([0.9, -0.5])
        cv_wire = wire(cv_y, x0, x1, CV, 7)
        cv_lab = M("ket(psi)", 0.85, CV).next_to(cv_wire, LEFT, buff=0.15)
        joint = gate('e^(-i t (hat(x) times.o L + I times.o H))', 3.2, cv_y + 2.05 + 0.8, INK, 0.8).move_to([3.4, (cv_y - 2.05) / 2, 0])
        mode_lab = T("one oscillator mode", 22, CV).next_to(joint, UP, buff=0.15)

        pos_ax = NumberLine(x_range=[-3, 3, 1], length=5.2, color=MUTED, stroke_width=2, include_ticks=False).move_to([-3.9, -2.6, 0])
        xv = ValueTracker(-2.2)
        pdot = always_redraw(lambda: Dot(pos_ax.n2p(xv.get_value()), radius=0.1, color=CV))
        plab = always_redraw(lambda: M("x", 0.8, CV).next_to(pdot, UP, buff=0.12))
        branch = M('e^(-i t (#c("' + CV + '", $x$) L + H)) = "LCHS branch at" k = #c("' + CV + '", $x$)', 0.95).move_to([2.6, -3.35, 0])

        with self.voice("idea") as v:
            self.play(FadeOut(o["rest"]), ReplacementTransform(o["head"], head), o["eq"].animate.scale(0.75).to_edge(UP, buff=0.95), run_time=0.9)
            self.play(Create(well_ax), Create(well), Create(wave), FadeIn(osc_title), FadeIn(xlab), run_time=1.6)
            v.until(1)
            self.play(ReplacementTransform(o["anc"], cv_wire), ReplacementTransform(o["anc_lab"], cv_lab),
                      FadeOut(VGroup(o["prep"], o["unprep"], o["meas"], o["ctrl"])),
                      ReplacementTransform(o["sel"], joint), run_time=1.6)
            self.play(FadeIn(mode_lab), run_time=0.6)
            v.until(2)
            self.play(Create(pos_ax), FadeIn(pdot), FadeIn(plab), FadeIn(branch), run_time=0.9)
            self.play(xv.animate.set_value(2.2), run_time=max(v.dur(2) - 1.2, 1.0), rate_func=there_and_back_with_pause)
        for m in (pdot, plab):
            m.clear_updaters()

        prior = card([T("Same one-mode dilation", 28, INK, weight=MEDIUM),
                      T("Schrödingerisation  ·  Jin, Liu, Yu, Phys. Rev. Lett. 133 (2024)", 23, MUTED),
                      T("Qumodisation  ·  Hu, Jin, Liu, Zhang, Stud. Appl. Math. 154 (2025)", 23, MUTED)], 10.0)
        ours = card([T("This paper", 28, ACCENT, weight=MEDIUM),
                     T("A finite-resource oscillator realization of the LCHS kernel,", 23, INK),
                     T("with an error and cost analysis for each block of the circuit:", 23, INK),
                     T("kernel truncation  ·  state synthesis  ·  product formula  ·  postselection", 23, ACCENT)], 10.0, ACCENT)
        VGroup(prior, ours).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, -0.2, 0])
        head5 = header(5, "Prior work and this paper")
        with self.voice("credit") as v:
            self.play(FadeOut(VGroup(well_ax, well, wave, osc_title, xlab, pos_ax, pdot, plab, branch, mode_lab, cv_wire, cv_lab, joint,
                                     o["syst"], o["sys_lab"], o["eq"])), ReplacementTransform(head, head5), run_time=0.8)
            self.play(FadeIn(prior, shift=0.15 * UP), run_time=1.0)
            v.until(1)
            self.play(FadeIn(ours, shift=0.15 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def kernel_loading(self):
        head = header(6, "Loading the kernel")
        eq = M('#c("' + INK + '", $g(x)$) = alpha thin #c("' + CV + '", $phi.alt_r^*(x)$) thin #c("' + ACCENT + '", $psi(x)$)', 1.45).move_to([0, 2.3, 0])
        xs = np.linspace(-10, 10, 801)
        grid = np.linspace(-80, 80, 64001)
        alpha = overlap_scale(grid)
        g_fin = np.abs(alpha * phi_r(xs) * psi_N(xs))

        def mini(ys, color, top, label, dashed=None):
            ax = Axes(x_range=[-10, 10, 5], y_range=[0, top, top], x_length=3.4, y_length=1.9, tips=False,
                      axis_config={"color": MUTED, "stroke_width": 1.5, "include_ticks": False})
            curve = VMobject(stroke_color=color, stroke_width=4).set_points_smoothly([ax.c2p(a, b) for a, b in zip(xs[::4], ys[::4])])
            grp = VGroup(ax, curve)
            if dashed is not None:
                d = VMobject(stroke_color=ACCENT, stroke_width=3).set_points_smoothly([ax.c2p(a, b) for a, b in zip(xs[::4], dashed[::4])])
                grp.add(DashedVMobject(d, num_dashes=40))
            grp.add(label.next_to(ax, DOWN, buff=0.15))
            return grp
        p1 = mini(phi_r(xs), CV, 0.7, M("phi.alt_r (x)", 0.8, CV))
        p2 = mini(np.abs(psi_N(xs)), ACCENT, 0.7, M("abs(psi(x))", 0.8, ACCENT))
        p3 = mini(np.abs(g_beta(xs)), INK, 0.28, M("abs(g(x))", 0.8), dashed=g_fin)
        times = M("times", 1.2, MUTED)
        prop = M("prop", 1.2, MUTED)
        row = VGroup(p1, times, p2, prop, p3).arrange(RIGHT, buff=0.45).move_to([0, -0.6, 0])
        note = T("solid: exact kernel    dashed: finite construction used in the paper", 19, MUTED).next_to(row, DOWN, buff=0.35)
        wide = T("squeezed vacuum: wide in x", 19, CV).next_to(p1, UP, buff=0.1)

        with self.voice("kernel") as v:
            self.play(FadeIn(head), Write(eq), run_time=1.8)
            self.play(LaggedStart(FadeIn(p1), FadeIn(times), FadeIn(p2), FadeIn(prop), FadeIn(p3), lag_ratio=0.3), run_time=2.4)
            self.play(FadeIn(wide), FadeIn(note), run_time=0.8)
            v.until(1)
            self.play(FadeOut(VGroup(row, note, wide)), eq.animate.scale(0.75).to_edge(UP, buff=0.95), run_time=0.8)

            cv_y, q_y = 0.6, -1.0
            x0, x1 = -6.0, 4.4
            w_cv = wire(cv_y, x0, x1, CV, 6)
            w_q = VGroup(wire(q_y - 0.1, x0, x1 + 0.6), wire(q_y + 0.1, x0, x1 + 0.6))
            l_cv = M("ket(0)", 0.85, CV).next_to(w_cv, LEFT, buff=0.15)
            l_q = M("ket(u_0)", 0.85).next_to(w_q, LEFT, buff=0.15)
            uprep = gate("U_psi", 1.1, 0.8, CV).move_to([-4.6, cv_y, 0])
            joint = gate('e^(-i t (hat(x) times.o L + I times.o H))', 3.9, 2.4, INK, 0.85).move_to([-1.3, (cv_y + q_y) / 2, 0])
            sq = gate("S^dagger (r)", 1.3, 0.8, CV).move_to([2.0, cv_y, 0])
            ms = meter(CV).move_to([3.6, cv_y, 0])
            keep = VGroup(T("keep", 20, CV), M("n = 0", 0.75, CV)).arrange(RIGHT, buff=0.12).next_to(ms, UP, buff=0.15)
            out = M("prop e^(-A t) u_0", 0.95).next_to(w_q, RIGHT, buff=0.15)
            self.play(Create(w_cv), Create(w_q), FadeIn(l_cv), FadeIn(l_q), run_time=0.8)
            steps = [(uprep, 0.1), (joint, 0.3), (sq, 0.58), (VGroup(ms, keep), 0.75)]
            for mob, frac in steps:
                v.until(1, frac)
                self.play(FadeIn(mob, scale=0.9), run_time=0.6)
                self.play(Indicate(mob, color=ACCENT, scale_factor=1.05), run_time=0.6)
            v.until(2)
            ident = M('(bra(phi.alt_r) times.o I) thin e^(-i t (hat(x) times.o L + I times.o H)) (ket(psi) times.o I) = integral_RR phi.alt_r^*(x) psi(x) thin e^(-i t (x L + H)) dif x = 1/alpha e^(-A t)', 0.82).move_to([0, -2.6, 0])
            ident.scale_to_fit_width(min(ident.width, 13.2))
            self.play(Write(ident), run_time=2.6)
            self.play(FadeIn(out, shift=0.1 * LEFT), Indicate(out, color=ACCENT), run_time=1.2)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def finite_resources(self):
        head = header(7, "Finite resources")
        eq = M("ket(psi_N) = S(r') sum_(n=0)^(N-1) C_n ket(n), quad N = 32", 1.15).to_edge(UP, buff=1.0).to_edge(LEFT, buff=0.8)
        bax = Axes(x_range=[0, 32, 8], y_range=[0, 1, 0.5], x_length=5.8, y_length=3.2, tips=False,
                   axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-3.5, -0.9, 0])
        mags = np.abs(C)
        bars = VGroup(*[Rectangle(width=5.8 / 32 * 0.72, height=max(bax.y_axis.unit_size * m, 0.01), stroke_width=0,
                                  fill_color=ACCENT, fill_opacity=0.85).move_to(bax.c2p(n + 0.5, 0), aligned_edge=DOWN)
                        for n, m in enumerate(mags)])
        blab = VGroup(M("abs(C_n)", 0.8, ACCENT).next_to(bax, UP, buff=0.1).align_to(bax, LEFT),
                      T("Fock level n", 20, MUTED).next_to(bax, DOWN, buff=0.45))
        ticks = VGroup(*[M(str(n), 0.6, MUTED).next_to(bax.c2p(n + 0.5, 0), DOWN, buff=0.1) for n in (0, 31)])

        tail = DATA["epsilon_tail"]
        eax = Axes(x_range=[0, 200, 50], y_range=[-3, 0, 1], x_length=5.4, y_length=3.2, tips=False,
                   axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([3.4, -0.9, 0])
        ecurve = VMobject(stroke_color=INK, stroke_width=3.5).set_points_as_corners([eax.c2p(n, np.log10(e)) for n, e in tail])
        e32 = dict(tail)[32]
        mark = VGroup(DashedLine(eax.c2p(32, -3), eax.c2p(32, np.log10(e32)), color=ACCENT, stroke_width=2),
                      Dot(eax.c2p(32, np.log10(e32)), radius=0.08, color=ACCENT))
        mark_lab = M('epsilon_"tr" (32) = 2.27 times 10^(-2)', 0.8, ACCENT).next_to(mark[1], UR, buff=0.12)
        elab = VGroup(T("truncation error of the ideal kernel state", 20, MUTED).next_to(eax, UP, buff=0.1).align_to(eax, LEFT),
                      T("cutoff N", 20, MUTED).next_to(eax, DOWN, buff=0.45))
        eticks = VGroup(*[M(f"10^({p})", 0.6, MUTED).next_to(eax.c2p(0, p), LEFT, buff=0.1) for p in (0, -1, -2, -3)],
                        *[M(str(n), 0.6, MUTED).next_to(eax.c2p(n, -3), DOWN, buff=0.1) for n in (100, 200)])
        fast = T("faster than any power of N", 22, INK, weight=MEDIUM).next_to(eax.c2p(110, -0.8), UP, buff=0)

        rank = VGroup(T("stellar rank", 22, INK), M("r^star = 31", 0.9)).arrange(RIGHT, buff=0.2).move_to(bax.c2p(19, 0.58))
        ng = T("non-Gaussian resource of the state", 19, MUTED).next_to(rank, UP, buff=0.1)
        rank_arrow = Arrow(rank.get_bottom() + 0.6 * RIGHT, bars[31].get_top() + 0.05 * UP, buff=0.08, color=INK, stroke_width=3)

        with self.voice("finite") as v:
            self.play(FadeIn(head), Write(eq), run_time=1.6)
            self.play(Create(bax), FadeIn(blab), FadeIn(ticks), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.05), run_time=2.6)
            v.until(1)
            self.play(Create(eax), FadeIn(elab), FadeIn(eticks), run_time=0.8)
            self.play(Create(ecurve), run_time=2.6)
            self.play(Create(mark), FadeIn(mark_lab), FadeIn(fast), run_time=1.2)
            v.until(2)
            self.play(bars[31].animate.set_fill(INK, 1), GrowArrow(rank_arrow), FadeIn(rank), FadeIn(ng), run_time=1.2)
            v.until(3)
            le_y, q_y = -0.4, -1.5
            x0, x1 = 0.9, 6.7
            w_cv = wire(le_y, x0, x1, CV, 6)
            w_q = wire(q_y, x0, x1, DV)
            labs = VGroup(M("ket(0)", 0.8, CV).next_to(w_cv, LEFT, buff=0.12), M("ket(g)", 0.8, DV).next_to(w_q, LEFT, buff=0.12))
            seq = VGroup()
            xpos = np.linspace(1.55, 6.1, 7)
            names = ["R_0", "S_1", "R_1", "S_2", "dots.c", "R_30", "S_31"]
            for xx, nm in zip(xpos, names):
                if nm.startswith("R"):
                    seq.add(gate(nm, 0.62, 0.55, DV, 0.7).move_to([xx, q_y, 0]))
                elif nm.startswith("S"):
                    seq.add(gate(nm, 0.62, abs(le_y - q_y) + 0.55, CV, 0.7).move_to([xx, (le_y + q_y) / 2, 0]))
                else:
                    seq.add(M(nm, 1.0, MUTED).move_to([xx, (le_y + q_y) / 2, 0]))
            le_title = T("Law–Eberly synthesis", 24, INK, weight=MEDIUM).move_to([3.8, 1.0, 0])
            le_count = VGroup(T("31 Jaynes–Cummings pulses + 31 qubit rotations", 21, INK),
                              T("plus one outer squeezing S(r′)", 19, MUTED)).arrange(DOWN, buff=0.1).next_to(w_q, DOWN, buff=0.45)
            self.play(FadeOut(VGroup(eax, ecurve, mark, mark_lab, elab, eticks, fast)), run_time=0.6)
            self.play(FadeIn(le_title), Create(w_cv), Create(w_q), FadeIn(labs), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(g, shift=0.1 * RIGHT) for g in seq], lag_ratio=0.2), run_time=1.8)
            self.play(FadeIn(le_count, shift=0.1 * UP), run_time=0.7)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def gates(self):
        head = header(8, "Gate-level compilation")
        eq = M('e^(-i Delta t thin a_i hat(x) times.o P_i) = V_i^dagger W_i^dagger thin #c("' + CV + '", $"cD"(-i Delta t thin a_i)$) thin W_i V_i', 1.1).to_edge(UP, buff=1.0)
        cv_y = 0.6
        qy = [-0.4, -1.0, -1.6]
        x0, x1 = -5.0, 5.0
        w_cv = wire(cv_y, x0, x1, CV, 6)
        w_q = VGroup(*[wire(yy, x0, x1) for yy in qy])
        labs = VGroup(M('"osc"', 0.75, CV).next_to(w_cv, LEFT, buff=0.15),
                      *[M(f"q_{i + 1}", 0.75).next_to(w, LEFT, buff=0.15) for i, w in enumerate(w_q)])
        v_in = VGroup(*[gate("V", 0.55, 0.45, INK, 0.7).move_to([-3.6, yy, 0]) for yy in qy])
        cx = VGroup()
        for i, xx in enumerate([-2.5, -1.8]):
            tgt = qy[-1]
            cx.add(Line([xx, qy[i], 0], [xx, tgt, 0], color=INK, stroke_width=2.5), Dot([xx, qy[i], 0], radius=0.07, color=INK),
                   Circle(radius=0.13, color=INK, stroke_width=2.5).move_to([xx, tgt, 0]),
                   Line([xx, tgt - 0.13, 0], [xx, tgt + 0.13, 0], color=INK, stroke_width=2.5))
        cdisp = VGroup(Line([0, qy[-1], 0], [0, cv_y, 0], color=CV, stroke_width=3), Dot([0, qy[-1], 0], radius=0.09, color=CV),
                       gate('D(minus.plus i Delta t thin a_i)', 2.0, 0.6, CV, 0.7).move_to([0, cv_y, 0]))
        cx2 = cx.copy().flip(UP, about_point=ORIGIN)
        v_out = VGroup(*[gate("V^dagger", 0.55, 0.45, INK, 0.7).move_to([3.6, yy, 0]) for yy in qy])
        cd_lab = T("controlled displacement", 21, CV).next_to(cdisp[2], UP, buff=0.12)
        par_lab = T("parity", 19, MUTED).next_to(cx, DOWN, buff=0.2)

        with self.voice("gates") as v:
            self.play(FadeIn(head), Write(eq), run_time=1.6)
            self.play(Create(w_cv), Create(w_q), FadeIn(labs), run_time=0.8)
            self.play(FadeIn(v_in), FadeIn(cx), FadeIn(par_lab), run_time=0.8)
            self.play(Create(cdisp[0]), FadeIn(cdisp[1]), FadeIn(cdisp[2], scale=0.9), FadeIn(cd_lab), run_time=0.9)
            self.play(FadeIn(cx2), FadeIn(v_out), run_time=0.7)
            v.until(1)
            core = VGroup(w_cv, w_q, v_in, cx, cdisp, cx2, v_out)
            target = core.copy().scale(0.3)
            copies = VGroup(*[target.copy() for _ in range(2)])
            dots = M("dots.c", 1.2, MUTED)
            rep = M("times n_t", 1.0)
            VGroup(target, copies, dots, rep).arrange(RIGHT, buff=0.25).move_to([0, -0.3, 0])
            layer_lab = T("one product-formula layer", 20, MUTED).next_to(target, UP, buff=0.2)
            self.play(FadeOut(VGroup(labs, cd_lab, par_lab)), Transform(core, target), run_time=1.0)
            self.play(FadeIn(layer_lab), LaggedStart(*[FadeIn(m, shift=0.2 * RIGHT) for m in copies], lag_ratio=0.3), FadeIn(dots), FadeIn(rep), run_time=1.4)
            bound = M('n_t = cal(O)(t^(1 + 1 slash p) N_"Fock"^((p + 1) slash (2 p)) epsilon_t^(-1 slash p))', 1.25).move_to([0, -2.5, 0])
            note = VGroup(T("worst case, up to commutator factors  ·  benchmarks: first order,", 19, MUTED),
                          M("n_t = 100", 0.72, MUTED)).arrange(RIGHT, buff=0.12).next_to(bound, DOWN, buff=0.2)
            self.play(Write(bound), run_time=1.8)
            self.play(FadeIn(note), run_time=0.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def postselection(self):
        head = header(9, "Postselection")
        rng = np.random.default_rng(3)
        shots = VGroup(*[Dot(radius=0.09, color=LINE) for _ in range(100)]).arrange_in_grid(10, 10, buff=0.2).move_to([-3.6, 0.1, 0])
        accept = rng.choice(100, 10, replace=False)
        glab = T("100 runs, Dirichlet benchmark", 20, MUTED).next_to(shots, UP, buff=0.3)
        rows = [("Dirichlet", 10.47), ("Neumann", 16.48), ("periodic", 15.36)]
        bars = VGroup()
        for i, (name, p) in enumerate(rows):
            yy = 1.0 - 0.8 * i
            lab = T(name, 22).move_to([1.6, yy, 0], aligned_edge=RIGHT)
            bar = Rectangle(width=p * 0.22, height=0.4, stroke_width=0, fill_color=CV, fill_opacity=0.9).move_to([1.8, yy, 0], aligned_edge=LEFT)
            val = T(f"{p:.2f}%", 22, CV).next_to(bar, RIGHT, buff=0.15)
            bars.add(VGroup(lab, bar, val))
        btitle = VGroup(T("success probability", 22, INK, weight=MEDIUM), M("p_\"succ\"", 0.85)).arrange(RIGHT, buff=0.2).next_to(bars, UP, buff=0.35).align_to(bars, LEFT)
        bnote = T("M = 4 heat benchmarks, benchmark input", 19, MUTED).next_to(bars, DOWN, buff=0.3).align_to(bars, LEFT)
        bound = M('abs(p_"succ" - p_"ref") lt.eq (2 norm(e^(-A t) u_0) thin epsilon_"tot" + epsilon_"tot"^2) / abs(alpha_(N, r))^2', 1.15).move_to([0, -2.55, 0])
        bnote2 = VGroup(M('epsilon_"tot"', 0.72, MUTED), T("total error of the implemented map", 19, MUTED)).arrange(RIGHT, buff=0.15).next_to(bound, DOWN, buff=0.2)

        with self.voice("postselect") as v:
            self.play(FadeIn(head), FadeIn(glab), LaggedStart(*[FadeIn(d, scale=0.5) for d in shots], lag_ratio=0.01), run_time=1.4)
            self.play(LaggedStart(*[shots[i].animate.set_color(CV).scale(1.5) for i in accept], lag_ratio=0.15), run_time=1.4)
            self.play(FadeIn(btitle), LaggedStart(*[GrowFromEdge(b[1], LEFT) for b in bars], lag_ratio=0.3),
                      FadeIn(VGroup(*[b[0] for b in bars])), FadeIn(VGroup(*[b[2] for b in bars])), FadeIn(bnote), run_time=1.6)
            v.until(1)
            self.play(Write(bound), run_time=2.0)
            self.play(FadeIn(bnote2), run_time=0.5)
        self.clear_stage()

    # ------------------------------------------------------------------ 09
    def results(self):
        head = header(10, "Circuit-level results")
        lab_x, bar_x0, per = -2.9, -2.75, 0.28
        top = 1.8
        step = 0.5
        labels, cvbars, cvvals, dvbars, dvvals = VGroup(), VGroup(), VGroup(), VGroup(), VGroup()
        for i, (name, cv, dv) in enumerate(ROWS):
            yy = top - i * step - (0.12 if i >= 3 else 0) - (0.12 if i >= 6 else 0) - (0.12 if i >= 9 else 0)
            labels.add(T(name, 19, INK if i < 9 else ACCENT).move_to([lab_x, yy, 0], aligned_edge=RIGHT))
            cb = Rectangle(width=cv * per, height=0.15, stroke_width=0, fill_color=ACCENT, fill_opacity=1).move_to([bar_x0, yy + 0.1, 0], aligned_edge=LEFT)
            db = Rectangle(width=dv * per, height=0.15, stroke_width=0, fill_color=DV, fill_opacity=0.85).move_to([bar_x0, yy - 0.1, 0], aligned_edge=LEFT)
            cvbars.add(cb)
            dvbars.add(db)
            cvvals.add(T(f"{cv:.2f}%", 14, ACCENT).next_to(cb, RIGHT, buff=0.08))
            dvvals.add(T(f"{dv:.2f}%", 14, DV).next_to(db, RIGHT, buff=0.08))
        base_y0, base_y1 = labels.get_top()[1] + 0.2, labels.get_bottom()[1] - 0.2
        axis = Line([bar_x0, base_y0, 0], [bar_x0, base_y1, 0], color=MUTED, stroke_width=2)
        ticks = VGroup(*[VGroup(Line([bar_x0 + p * per, base_y1, 0], [bar_x0 + p * per, base_y1 - 0.08, 0], color=MUTED, stroke_width=2),
                                T(f"{p}%", 16, MUTED).next_to([bar_x0 + p * per, base_y1 - 0.08, 0], DOWN, buff=0.06)) for p in (0, 5, 10, 15)])
        xtitle = VGroup(T("fixed-scale map error", 19, MUTED), M("epsilon_F", 0.72, MUTED)).arrange(RIGHT, buff=0.12).next_to(ticks, DOWN, buff=0.12)
        cap = DashedLine([bar_x0 + 1.48 * per, base_y0, 0], [bar_x0 + 1.48 * per, labels[8].get_bottom()[1] - 0.1, 0], color=ACCENT, stroke_width=2)
        cap_lab = T("≤ 1.48% in 1D", 19, ACCENT).next_to(cap, UP, buff=0.08)
        legend_cv = VGroup(Square(0.22, stroke_width=0, fill_color=ACCENT, fill_opacity=1), T("hybrid oscillator–qubit", 21, ACCENT)).arrange(RIGHT, buff=0.15)
        legend_dv = VGroup(Square(0.22, stroke_width=0, fill_color=DV, fill_opacity=0.85), T("qubit-only LCHS", 21, DV)).arrange(RIGHT, buff=0.15)
        legend = VGroup(legend_cv, legend_dv).arrange(RIGHT, buff=0.5).next_to(axis, UP, buff=0.35).align_to(labels, LEFT)
        note2d = T("kernel parameters chosen on the 1D family", 18, MUTED).next_to(cvvals[9], RIGHT, buff=0.2)

        with self.voice("results") as v:
            self.play(FadeIn(head), Create(axis), FadeIn(ticks), FadeIn(xtitle), FadeIn(legend_cv), run_time=0.9)
            groups = [range(0, 3), range(3, 6), range(6, 9)]
            span = (v.dur(0) - 1.2) / 3
            for gidx, g in enumerate(groups):
                v.until(0, [0.05, 0.35, 0.62][gidx])
                self.play(*[FadeIn(labels[i], shift=0.1 * RIGHT) for i in g], *[GrowFromEdge(cvbars[i], LEFT) for i in g],
                          *[FadeIn(cvvals[i]) for i in g], run_time=min(span, 1.4))
            v.until(1)
            self.play(Create(cap), FadeIn(cap_lab), run_time=1.0)
            self.play(Indicate(VGroup(*cvvals[:9]), color=ACCENT, scale_factor=1.1), run_time=1.2)
            v.until(2)
            self.play(FadeIn(labels[9], shift=0.1 * RIGHT), GrowFromEdge(cvbars[9], LEFT), FadeIn(cvvals[9]), run_time=1.4)
            self.play(FadeIn(note2d), run_time=0.6)

        cards = VGroup(
            card([T("qubit-only LCHS, ε = 0.1 rule", 22, DV, weight=MEDIUM), T("192–632 quadrature terms", 20, INK), T("8–10 ancilla qubits", 20, INK)], 3.7, DV),
            card([T("hybrid oscillator–qubit", 22, ACCENT, weight=MEDIUM), T("32 squeezed-Fock coefficients", 20, INK), T("1 oscillator mode", 20, INK)], 3.7, ACCENT),
        ).arrange(DOWN, buff=0.25).move_to([4.75, 0.9, 0])
        attempts = card([T("expected attempts, 1D inputs", 19, MUTED),
                         T("qubit-only  3.8–4.3", 21, DV), T("hybrid  6.07–9.55", 21, ACCENT)], 3.7).next_to(cards, DOWN, buff=0.25)
        head11 = header(11, "Against qubit-only LCHS")
        with self.voice("compare") as v:
            self.play(ReplacementTransform(head, head11), FadeOut(note2d), FadeOut(cap_lab), FadeIn(legend_dv), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(c, shift=0.15 * LEFT) for c in cards], lag_ratio=0.4), run_time=1.6)
            v.until(1)
            self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in dvbars], lag_ratio=0.08), run_time=2.4)
            self.play(FadeIn(dvvals), run_time=0.6)
            v.until(1, 0.55)
            self.play(FadeIn(attempts, shift=0.1 * UP), run_time=0.9)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("When quadrature cost dominates, one oscillator mode", 34, weight=MEDIUM),
                       T("can replace a discretized ancilla register.", 34, weight=MEDIUM),
                       T("The price: oscillator operations and extra postselection repetitions.", 26, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lines[2].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the paper"),
                      T("Das, Zheng, Dutta, Li, Stavenger, Liu. Quantum Science and Technology (2026)", 21),
                      T("doi.org/10.1088/2058-9565/aea2c6   ·   arXiv:2605.10708", 21, ACCENT),
                      T("Code and data: github.com/Firepanda415/CV-DV-LCHS", 21, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.9).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.4)
            v.until(0, 0.6)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class LCHSPoster(Scene):
    """Still image for the website thumbnail, with larger elements than the video frames."""

    def construct(self):
        label = eyebrow("LCHS on one oscillator", size=30).to_corner(UL, buff=0.6)
        eq = M('e^(-A t) = integral_RR #c("' + ACCENT + '", $g(k)$) thin #c("' + DV + '", $e^(-i t (k L + H))$) dif k', 2.3).move_to([0, 1.55, 0])
        cv_y, q_y = -1.35, -2.75
        w_cv = wire(cv_y, -6.4, 6.4, CV, 14)
        w_q = VGroup(wire(q_y - 0.16, -6.4, 6.4, INK, 5), wire(q_y + 0.16, -6.4, 6.4, INK, 5))
        uprep = gate("U_psi", 1.7, 1.15, CV, 1.4).move_to([-4.7, cv_y, 0])
        joint = gate('e^(-i t (hat(x) times.o L + I times.o H))', 5.2, 2.6, INK, 1.25).move_to([-0.6, (cv_y + q_y) / 2, 0])
        for g in (uprep, joint):
            g[0].set_stroke(width=5)
        ms = meter(CV).scale(1.7).move_to([4.6, cv_y, 0])
        ms[0].set_stroke(width=5)
        self.add(label, eq, w_cv, w_q, uprep, joint, ms)
