"""Explainer for "A Bayesian Approach for Characterizing and Mitigating Gate and Measurement Errors"
(Zheng, Li, Terlaky, Yang, ACM Trans. Quantum Comput. 4(2), 11, 2023; arXiv:2010.09188v6).

Device values are copied from Tables 1-7 of the paper. The sensitivity curves evaluate the
paper's forward model, Eq. (13) with x = 1 and m = 200. The consistent Bayesian demonstration
in section 04 uses the ibm_perth tutorial data of the paper's code repository (data.json, built
by extract_data.py), and the screen says so.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

POST = ACCENT      # the paper's posterior filters (consistent Bayesian)
RAW = MUTED        # unfiltered device data
QISKIT = DV        # Qiskit CompleteMeasFitter
QDT = CV           # detector tomography filter
VENDOR = GOLD      # vendor calibration values

# Table 1, consistent Bayesian posterior means of (1 - m0, 1 - m1), qubits 1-4 of ibmqx2.
T1 = [(0.9354, 0.9009), (0.9537, 0.8184), (0.9457, 0.8976), (0.8272, 0.9492)]
# Table 2, three-qubit state tomography fidelity: raw, Qiskit filter, consistent mean.
T2 = [(("000", "111"), 0.7389, 0.9227, 0.9390), (("010", "101"), 0.6719, 0.8970, 0.9203),
      (("100", "011"), 0.7006, 0.9121, 0.9254), (("110", "001"), 0.6974, 0.8863, 0.9443)]
# Table 3, Grover search, probability of measuring |11>, at hours 0-16.
HOURS = [0, 2, 4, 8, 12, 16]
T3 = {"raw": [0.6727, 0.6930, 0.6724, 0.6740, 0.6917, 0.6841],
      "Qiskit": [0.7097, 0.7335, 0.7104, 0.7120, 0.7323, 0.7241],
      "QDT": [0.7107, 0.7332, 0.7087, 0.7108, 0.7305, 0.7224],
      "standard": [0.9099, 0.9324, 0.9063, 0.9088, 0.9290, 0.9192],
      "consistent": [0.9128, 0.9351, 0.9088, 0.9114, 0.9316, 0.9219]}
# Table 5, QAOA, probability of measuring an optimal cut at hour 0.
T5 = {"simulator": 0.8930, "raw": 0.5784, "Qiskit": 0.5968, "QDT": 0.6400, "standard": 0.6952, "consistent": 0.6975}
# Table 6, posterior mean gate error rate for qubits 1 and 2.
T6 = {"consistent": (0.004934, 0.003804), "standard": (0.004683, 0.002982)}
# Table 7, Grover Pr(|11>) at hour 0 with readout rates from the 200-NOT circuit (consistent mean).
T7 = 0.8434

COLORS = {"raw": RAW, "Qiskit": QISKIT, "QDT": QDT, "standard": POST, "consistent": POST}


def q200(g, m0, m1):
    """Probability of measuring 0 after 200 NOT gates on |0>, Eq. (13) with x = 1 and m = 200."""
    d = (1 - 2 * g) ** 200
    return (0.5 + 0.5 * d) * (1 - m0) + (0.5 - 0.5 * d) * m1


DEMO = json.loads((Path(__file__).resolve().parent / "data.json").read_text())
SAMPLES = [(a, b, k) for a, b, k in DEMO["dots"] if a < 0.3 and b < 0.3]


def bar(ax, xc, val, color, half=0.28, opacity=0.85, fmt="{:.2f}", size=15):
    lo, hi = ax.c2p(xc - half, 0), ax.c2p(xc + half, val)
    r = Rectangle(width=hi[0] - lo[0], height=hi[1] - lo[1], stroke_width=0, fill_color=color, fill_opacity=opacity)
    r.move_to((lo + hi) / 2)
    return VGroup(r, T(fmt.format(val), size, color).next_to(r, UP, buff=0.07))


def plain_axes(xr, yr, xl, yl, **kw):
    return Axes(x_range=xr, y_range=yr, x_length=xl, y_length=yl, tips=False,
                axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}, **kw)


def arrow(a, b, color=MUTED, buff=0.12):
    return Arrow(a, b, buff=buff, color=color, stroke_width=2.5, tip_length=0.16, max_tip_length_to_length_ratio=0.2)


def legend(items, size=16):
    return VGroup(*[VGroup(Square(0.2, stroke_width=0, fill_color=c, fill_opacity=o), T(t, size)).arrange(RIGHT, buff=0.1)
                    for t, c, o in items]).arrange(RIGHT, buff=0.35)


class BayesianExplainer(Explainer):
    timing_file = BUILD / "bayesian" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.readout()
        self.gate()
        self.bayes()
        self.calibrate()
        self.apply()
        self.gates()
        self.limits()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("ACM Transactions on Quantum Computing 4(2), 11 · 2023")
        title = VGroup(T("A Bayesian Approach for Characterizing", 42, weight=MEDIUM),
                       T("and Mitigating Gate and Measurement Errors", 42, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = T("Muqing Zheng, Ang Li, Tamás Terlaky, Xiu Yang", 22, MUTED)
        places = T("Lehigh University · Pacific Northwest National Laboratory", 18, MUTED)
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
        head = header(1, "Noisy outputs")
        ax_i = plain_axes([0, 4, 1], [0, 1, 0.5], 3.4, 2.6).move_to([-4.6, 0.3, 0])
        ax_m = plain_axes([0, 2, 1], [0, 1, 0.5], 2.4, 2.6).move_to([4.6, 0.3, 0])
        ideal = bar(ax_i, 3.5, 1.0, INK, half=0.3, opacity=0.8)
        kets = VGroup(*[M(f"ket({s})", 0.7).next_to(ax_i.c2p(0.5 + i, 0), DOWN, buff=0.15) for i, s in enumerate(["00", "01", "10", "11"])])
        meas = VGroup(bar(ax_m, 0.5, T3["raw"][0], QISKIT, half=0.3), bar(ax_m, 1.5, 1 - T3["raw"][0], RAW, half=0.3))
        meas_lab = VGroup(M("ket(11)", 0.7).next_to(ax_m.c2p(0.5, 0), DOWN, buff=0.15),
                          T("other outcomes", 15, MUTED).next_to(ax_m.c2p(1.5, 0), DOWN, buff=0.2))
        t_i = T("ideal output, 2-qubit Grover search", 18, INK, weight=MEDIUM).next_to(ax_i, UP, buff=0.3)
        t_m = T("measured on ibmqx2", 18, QISKIT, weight=MEDIUM).next_to(ax_m, UP, buff=0.3)
        noise = VGroup(T("gate bit flips", 20, ACCENT), T("readout errors", 20, ACCENT)).arrange(DOWN, buff=0.25).move_to([0, 0.6, 0])
        arr = arrow(ax_i.get_right() + 0.2 * RIGHT, ax_m.get_left() + 0.2 * LEFT, INK)
        arr.move_to([0, -0.3, 0])
        back = CurvedArrow(ax_m.get_bottom() + 1.3 * DOWN, ax_i.get_bottom() + 1.3 * DOWN, angle=-TAU / 12, color=POST, stroke_width=3)
        back_lab = VGroup(T("the paper's mitigation inverts a noise model, which needs the error rates", 18, POST),
                          M("epsilon_g, quad m_0, quad m_1", 0.8, POST)).arrange(RIGHT, buff=0.3).move_to([0, -3.35, 0])
        note = T("raw value from Table 3", 14, MUTED).next_to(meas_lab, DOWN, buff=0.15)
        with self.voice("problem") as v:
            self.play(FadeIn(head), Create(ax_i), FadeIn(t_i), FadeIn(kets), run_time=1.0)
            self.play(GrowFromEdge(ideal[0], DOWN), FadeIn(ideal[1]), run_time=0.8)
            self.play(GrowArrow(arr), FadeIn(noise), run_time=1.0)
            self.play(Create(ax_m), FadeIn(t_m), FadeIn(meas_lab), run_time=0.8)
            self.play(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in meas], FadeIn(note), run_time=1.2)
            v.until(1)
            self.play(Create(back), run_time=1.0)
            self.play(FadeIn(back_lab, shift=0.1 * UP), run_time=0.8)
            v.until(2)
            self.clear_stage(keep=[head], run_time=0.6)
            a1 = plain_axes([0, 1, 0.5], [0, 1, 0.5], 3.6, 2.0)
            a2 = plain_axes([0, 1, 0.5], [0, 1, 0.5], 3.6, 2.0)
            a1.move_to([-3.4, 0.2, 0])
            a2.move_to([3.4, 0.2, 0])
            spike = Line(a1.c2p(0.45, 0), a1.c2p(0.45, 0.95), color=VENDOR, stroke_width=5)
            bell = a2.plot(lambda t: 0.9 * np.exp(-(t - 0.45) ** 2 / (2 * 0.08 ** 2)), x_range=[0.05, 0.95, 0.01], color=POST, stroke_width=4)
            fill = a2.get_area(bell, x_range=[0.05, 0.95], color=POST, opacity=0.18)
            l1 = VGroup(T("fixed value", 20, VENDOR, weight=MEDIUM), T("for example, vendor calibration", 17, MUTED)).arrange(DOWN, buff=0.08).next_to(a1, DOWN, buff=0.3)
            l2 = VGroup(T("probability distribution", 20, POST, weight=MEDIUM), T("Bayesian inference, this paper", 17, MUTED)).arrange(DOWN, buff=0.08).next_to(a2, DOWN, buff=0.3)
            xl = VGroup(T("error rate", 15, MUTED).next_to(a1.x_axis, DOWN, buff=0.08).align_to(a1, RIGHT),
                        T("error rate", 15, MUTED).next_to(a2.x_axis, DOWN, buff=0.08).align_to(a2, RIGHT))
            mid = arrow(a1.get_right() + 0.3 * RIGHT, a2.get_left() + 0.3 * LEFT, INK)
            sch = T("schematic", 14, MUTED).to_corner(DR, buff=0.5)
            self.play(Create(a1), Create(spike), FadeIn(l1), FadeIn(xl[0]), run_time=1.0)
            self.play(GrowArrow(mid), Create(a2), FadeIn(xl[1]), FadeIn(sch), run_time=0.8)
            self.play(Create(bell), FadeIn(fill), FadeIn(l2), run_time=1.2)
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def readout(self):
        head = header(2, "Measurement error model")
        nodes = {"s0": [-5.9, 1.3], "s1": [-5.9, -0.7], "r0": [-2.6, 1.3], "r1": [-2.6, -0.7]}
        labels = {"s0": ("state", "ket(0)"), "s1": ("state", "ket(1)"), "r0": ("read", "0"), "r1": ("read", "1")}
        dots = VGroup()
        for k, (x, y) in nodes.items():
            dots.add(VGroup(T(labels[k][0], 16, MUTED), M(labels[k][1], 0.9)).arrange(RIGHT, buff=0.12).move_to([x, y, 0]))
        edges = VGroup(arrow(dots[0].get_right(), dots[2].get_left(), INK), arrow(dots[1].get_right(), dots[3].get_left(), INK),
                       arrow(dots[0].get_right(), dots[3].get_left(), ACCENT), arrow(dots[1].get_right(), dots[2].get_left(), ACCENT))
        elabs = VGroup(M("1 - m_0", 0.75).next_to(edges[0], UP, buff=0.08), M("1 - m_1", 0.75).next_to(edges[1], DOWN, buff=0.08),
                       M("m_0", 0.8, ACCENT).move_to(edges[2].point_from_proportion(0.22) + 0.34 * LEFT + 0.08 * DOWN),
                       M("m_1", 0.8, ACCENT).move_to(edges[3].point_from_proportion(0.22) + 0.34 * LEFT + 0.08 * UP))
        eq1 = M("mat(1 - m_0, m_1; m_0, 1 - m_1) mat(p_0; p_1) = mat(tilde(p)_0; tilde(p)_1)", 1.0).move_to([3.3, 1.5, 0])
        eq1_lab = VGroup(T("ideal", 15, MUTED), T("observed", 15, MUTED))
        eqn = M("A = times.o.big_(i=1)^n mat(1 - m_(0,i), m_(1,i); m_(0,i), 1 - m_(1,i))", 0.9).move_to([3.3, -0.4, 0])
        eqn_lab = VGroup(T("independent readout errors, A is", 16, MUTED), M("2^n times 2^n", 0.65, MUTED)).arrange(RIGHT, buff=0.12).next_to(eqn, DOWN, buff=0.2)
        ls = M('bold(r)^* = op("arg min", limits: #true)_(sum_i r_i = 1, thin r_i >= 0) norm(A bold(r) - tilde(bold(r)))_2', 1.0, POST).move_to([-1.6, -2.75, 0])
        ls_lab = VGroup(T("constrained least squares", 18, POST, weight=MEDIUM),
                        VGroup(T("a plain inverse", 16, MUTED), M("A^(-1) tilde(bold(r))", 0.65, MUTED), T("can give negative entries", 16, MUTED)).arrange(RIGHT, buff=0.1)
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(ls, RIGHT, buff=0.5)
        with self.voice("readout") as v:
            self.play(FadeIn(head), FadeIn(dots), run_time=0.9)
            self.play(GrowArrow(edges[0]), GrowArrow(edges[1]), FadeIn(elabs[:2]), run_time=0.9)
            v.until(0, 0.35)
            self.play(GrowArrow(edges[2]), FadeIn(elabs[2]), run_time=0.8)
            v.until(0, 0.7)
            self.play(GrowArrow(edges[3]), FadeIn(elabs[3]), run_time=0.8)
            v.until(1)
            self.play(Write(eq1), run_time=1.4)
            v.until(1, 0.6)
            self.play(FadeIn(eqn, shift=0.1 * DOWN), FadeIn(eqn_lab), run_time=1.2)
            v.until(2)
            self.play(Write(ls), run_time=1.2)
            self.play(FadeIn(ls_lab, shift=0.1 * LEFT), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def gate(self):
        head = header(3, "Bit-flip gate error model")
        ys = [2.1, 1.45, 0.8]
        wires = VGroup(*[wire(y, -6.2, 0.2) for y in ys])
        phi = M("ket(phi)", 0.9).next_to(wires, LEFT, buff=0.15)

        def ubox(x, label):
            r = RoundedRectangle(corner_radius=0.08, width=0.8, height=ys[0] - ys[-1] + 0.55, stroke_color=INK, stroke_width=2.5,
                                 fill_color=PAPER, fill_opacity=1).move_to([x, (ys[0] + ys[-1]) / 2, 0])
            return VGroup(r, M(label, 0.8).move_to(r))

        def flips(x):
            return VGroup(*[gate("X_(epsilon_g)", 0.72, 0.42, ACCENT, 0.62).move_to([x, y, 0]) for y in ys])

        gap = VGroup(Rectangle(width=0.55, height=ys[0] - ys[-1] + 0.3, stroke_width=0, fill_color=PAPER, fill_opacity=1).move_to([-3.05, ys[1], 0]),
                     T("···", 28, MUTED).move_to([-3.05, ys[1], 0]))
        layers = VGroup(ubox(-5.1, "U_1"), flips(-4.0), gap, ubox(-2.1, "U_m"), flips(-1.0))
        brace = Brace(VGroup(layers[1], layers[4]), DOWN, buff=0.15, color=ACCENT)
        b_lab = VGroup(T("each qubit flips with probability", 16, ACCENT), M("epsilon_g", 0.65, ACCENT), T("after every gate", 16, ACCENT)
                       ).arrange(RIGHT, buff=0.1).next_to(brace, DOWN, buff=0.1)
        ax = plain_axes([0, 200, 50], [0, 1, 0.5], 4.4, 2.2).move_to([4.2, 1.2, 0])
        curves = VGroup(*[ax.plot(lambda m, k=k: (1 - 2 * 0.005) ** (k * m), x_range=[0, 200, 1], color=ACCENT, stroke_width=3.5,
                                  stroke_opacity=1.0 - 0.3 * (k - 1)) for k in (1, 2, 3)])
        c_labs = VGroup(*[VGroup(Line(ORIGIN, 0.35 * RIGHT, color=ACCENT, stroke_width=3.5, stroke_opacity=1.0 - 0.3 * (k - 1)),
                                 M(f"|s| = {k}", 0.6, ACCENT)).arrange(RIGHT, buff=0.1) for k in (1, 2, 3)]
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to(ax.c2p(130, 0.78))
        ax_lab = VGroup(T("damping factor", 15, MUTED).next_to(ax, UP, buff=0.1).align_to(ax, LEFT),
                        VGroup(T("gates m, with", 15, MUTED), M("epsilon_g = 0.005", 0.55, MUTED)).arrange(RIGHT, buff=0.1).next_to(ax.x_axis, DOWN, buff=0.12),
                        T("0", 14, MUTED).next_to(ax.c2p(0, 0), LEFT, buff=0.1), T("1", 14, MUTED).next_to(ax.c2p(0, 1), LEFT, buff=0.1))
        eq6 = M("tilde(p)(x) = sum_(s in {0,1}^n) (1 - 2 epsilon_g)^(|s| m) thin hat(p)(s) (-1)^(s dot x)", 1.05).move_to([0, -1.35, 0])
        origin = T("model from earlier work, proved here for one gate and extended to m gates", 18, MUTED).move_to([0, -1.35, 0])
        gsys = VGroup(M("G hat(bold(rho)) = tilde(bold(rho))", 1.0, POST),
                      T("G has full rank whenever", 18, INK), M("epsilon_g != 1/2", 0.85),
                      T("(Lemma 2.1)", 16, MUTED), T("then constrained least squares keeps it valid", 18, POST)).arrange(RIGHT, buff=0.25).move_to([0, -3.0, 0])
        with self.voice("gate") as v:
            self.play(FadeIn(head), Create(wires), FadeIn(phi), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(l) for l in layers], lag_ratio=0.3), run_time=2.0)
            self.play(GrowFromCenter(brace), FadeIn(b_lab), run_time=0.8)
            v.until(1)
            self.play(FadeIn(origin, shift=0.1 * UP), run_time=0.8)
            v.until(2)
            self.play(FadeOut(origin), Write(eq6), run_time=1.6)
            v.until(2, 0.55)
            self.play(Create(ax), FadeIn(ax_lab), run_time=0.8)
            self.play(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.3), FadeIn(c_labs), run_time=1.8)
            v.until(3)
            self.play(LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in gsys], lag_ratio=0.2), run_time=2.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def bayes(self):
        head = header(4, "Consistent Bayesian inference")
        src = DEMO["source"]
        circ = VGroup(wire(2.45, -6.5, -4.3), M("ket(0)", 0.8).move_to([-6.85, 2.45, 0]),
                      gate("H", 0.55, 0.45, size=0.7).move_to([-5.7, 2.45, 0]), meter().scale(0.7).move_to([-4.8, 2.45, 0]))
        qdef = M('Q = Pr("measure" 0)', 0.9).next_to(circ, RIGHT, buff=0.4)
        sc = plain_axes([0, 0.3, 0.1], [0, 0.3, 0.1], 3.6, 3.2).move_to([-3.5, -1.05, 0])
        sc_lab = VGroup(M("m_0", 0.8).next_to(sc.x_axis, DOWN, buff=0.1).align_to(sc, RIGHT),
                        M("m_1", 0.8).next_to(sc.y_axis, LEFT, buff=0.1).align_to(sc, UP),
                        T("prior samples of the readout error rates", 16, MUTED).next_to(sc, UP, buff=0.12))
        dots = VGroup(*[Dot(sc.c2p(a, b), 0.03, color=MUTED) for a, b, _ in SAMPLES])
        accept = [k for _, _, k in SAMPLES]
        vend = VGroup(Cross(scale_factor=0.09, stroke_color=VENDOR, stroke_width=5).move_to(sc.c2p(DEMO["vendor"]["m0"], DEMO["vendor"]["m1"])))
        vend.add(VGroup(Cross(scale_factor=0.09, stroke_color=VENDOR, stroke_width=5), T("vendor calibration, the prior center", 15, VENDOR)
                        ).arrange(RIGHT, buff=0.15).next_to(sc, DOWN, buff=0.45).align_to(sc, LEFT))
        grid = np.array(DEMO["grid"])
        dens = {k: np.array(v) for k, v in DEMO["density"].items()}
        top = 1.12 * dens["data"].max()
        da = plain_axes([0.3, 0.7, 0.1], [0, top, top], 5.0, 3.2).move_to([3.5, -1.05, 0])
        curve = lambda k, color: da.plot_line_graph(grid, dens[k], add_vertex_dots=False, line_color=color, stroke_width=3.5)
        c_obs = curve("data", INK)
        c_pushed = DashedVMobject(da.plot_line_graph(grid, dens["prior"], add_vertex_dots=False, line_color=MUTED, stroke_width=3)["line_graph"], num_dashes=40)
        c_post = curve("kept", POST)
        da_lab = VGroup(M("Q", 0.8).next_to(da.x_axis, RIGHT, buff=0.15),
                        T("density", 15, MUTED).next_to(da, UP, buff=0.12).align_to(da, LEFT),
                        *[T(f"{t:.1f}", 14, MUTED).next_to(da.c2p(t, 0), DOWN, buff=0.1) for t in (0.3, 0.5, 0.7)])
        key = VGroup(VGroup(Line(ORIGIN, 0.35 * RIGHT, color=INK, stroke_width=3.5), T(f"data, {len(DEMO['estimates'])} estimates", 15)).arrange(RIGHT, buff=0.1),
                     VGroup(DashedLine(ORIGIN, 0.35 * RIGHT, color=MUTED, stroke_width=3, dash_length=0.06), T("prior predictions", 15)).arrange(RIGHT, buff=0.1),
                     VGroup(Line(ORIGIN, 0.35 * RIGHT, color=POST, stroke_width=3.5), T("kept-sample predictions", 15, POST)).arrange(RIGHT, buff=0.1)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(da.c2p(0.56, 0.72 * top), aligned_edge=LEFT)
        post = M('pi^"post" (lambda) = pi^"prior" (lambda) thin (pi^"obs" (Q(lambda))) / (pi^(Q("prior")) (Q(lambda)))', 0.95).move_to([2.9, 2.4, 0])
        std = card([T("standard Bayesian, for comparison", 17, INK, weight=MEDIUM),
                    VGroup(M("y_j tilde cal(N)(Q(lambda; x_j), sigma_epsilon^2)", 0.7), T("sampled with Stan", 16, MUTED)).arrange(RIGHT, buff=0.25)],
                   5.6, LINE, pad=0.2).move_to([-3.5, 2.4, 0])
        note = T(f"device data: {src['device']}, qubit {src['qubit']}, {src['calibration_date'][:10]}, tutorial in the paper's code repository",
                 14, MUTED).move_to([0, -3.65, 0])
        with self.voice("bayes") as v:
            self.play(FadeIn(head), FadeIn(circ), FadeIn(qdef), run_time=1.0)
            self.play(Create(da), FadeIn(da_lab), FadeIn(note), run_time=0.8)
            self.play(Create(c_obs), FadeIn(key[0]), run_time=1.0)
            v.until(1)
            self.play(Create(sc), FadeIn(sc_lab), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.004), FadeIn(vend), run_time=2.0)
            self.play(Create(c_pushed), FadeIn(key[1]), run_time=1.2)
            v.until(2)
            self.play(Write(post), run_time=1.4)
            self.play(*[d.animate.set_color(POST).scale(1.3) for d, a in zip(dots, accept) if a],
                      *[d.animate.set_opacity(0.12) for d, a in zip(dots, accept) if not a], run_time=1.6)
            self.play(Create(c_post), FadeIn(key[2]), run_time=1.2)
            v.until(3)
            self.play(FadeOut(VGroup(circ, qdef)), FadeIn(std, shift=0.1 * UP), run_time=0.9)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def calibrate(self):
        head = header(5, "Readout test on ibmqx2")
        ys = [2.2, 1.6, 1.0, 0.4]
        circ = VGroup(*[VGroup(wire(y, -6.2, -3.4), T(f"q{i + 1}", 16, MUTED).move_to([-6.95, y, 0]), M("ket(0)", 0.7).move_to([-6.5, y, 0]),
                               gate("H", 0.5, 0.42, size=0.7).move_to([-5.2, y, 0]), meter().scale(0.62).move_to([-4.1, y, 0]))
                        for i, y in enumerate(ys)])
        facts = VGroup(VGroup(T("ideal", 19), M('Pr("measure" 0) = 1/2', 0.85), T("on every qubit", 19)).arrange(RIGHT, buff=0.18),
                       T("unchanged by bit flips and phase flips after H", 17, MUTED),
                       T("one circuit characterizes all four qubits", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([2.0, 1.75, 0], aligned_edge=LEFT)
        facts.align_to(np.array([-2.4, 0, 0]), LEFT)
        runs = VGroup(M("128 times 1024", 0.8), T("shots  →  128 estimates per qubit", 19)).arrange(RIGHT, buff=0.15).next_to(facts, DOWN, buff=0.35, aligned_edge=LEFT)
        ax = plain_axes([0, 4, 1], [0, 0.2, 0.05], 6.0, 2.6).move_to([-3.2, -2.05, 0])
        grid = VGroup(*[DashedLine(ax.c2p(0, t), ax.c2p(4, t), color=LINE, stroke_width=1.5, dash_length=0.08) for t in (0.05, 0.1, 0.15, 0.2)])
        ticks = VGroup(*[T(f"{round(100 * t)}%", 14, MUTED).next_to(ax.c2p(0, t), LEFT, buff=0.1) for t in (0, 0.1, 0.2)])
        bars = VGroup()
        for i, (a, b) in enumerate(T1):
            bars.add(bar(ax, 0.5 + i - 0.17, 1 - a, POST, half=0.15, fmt="{:.1%}", size=13),
                     bar(ax, 0.5 + i + 0.17, 1 - b, POST, half=0.15, opacity=0.4, fmt="{:.1%}", size=13))
        qlab = VGroup(*[T(f"qubit {i + 1}", 15).next_to(ax.c2p(0.5 + i, 0), DOWN, buff=0.12) for i in range(4)])
        leg = VGroup(VGroup(Square(0.2, stroke_width=0, fill_color=POST, fill_opacity=0.85), M("m_0", 0.65)).arrange(RIGHT, buff=0.1),
                     VGroup(Square(0.2, stroke_width=0, fill_color=POST, fill_opacity=0.4), M("m_1", 0.65)).arrange(RIGHT, buff=0.1)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(ax, RIGHT, buff=0.3)
        ttl = T("posterior mean readout error rates (Table 1)", 16, MUTED).next_to(ax, UP, buff=0.15).align_to(ax, LEFT)
        filt = card([T("filters applied to the same 128 estimates", 17, MUTED),
                     VGroup(T("vendor calibration:", 18, VENDOR, weight=MEDIUM), T("rarely returns 1/2", 18)).arrange(RIGHT, buff=0.15),
                     VGroup(T("posterior:", 18, POST, weight=MEDIUM), T("centered on 1/2", 18)).arrange(RIGHT, buff=0.15)],
                    5.0, LINE, pad=0.25).move_to([4.2, -2.2, 0])
        with self.voice("calibrate") as v:
            self.play(FadeIn(head), LaggedStart(*[FadeIn(c) for c in circ], lag_ratio=0.15), run_time=1.4)
            self.play(FadeIn(facts[0]), run_time=0.8)
            v.until(0, 0.6)
            self.play(FadeIn(facts[1:]), run_time=0.8)
            v.until(1)
            self.play(FadeIn(runs, shift=0.1 * UP), run_time=0.8)
            v.until(2)
            self.play(Create(ax), FadeIn(grid), FadeIn(ticks), FadeIn(qlab), FadeIn(leg), FadeIn(ttl), run_time=0.9)
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in bars], lag_ratio=0.12), run_time=2.2)
            v.until(2, 0.7)
            self.play(*[Indicate(bars[2 * i + 1], color=POST, scale_factor=1.08) for i in range(3)], run_time=1.0)
            v.until(3)
            self.play(FadeIn(filt, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def apply(self):
        head = header(6, "Filtering other circuits")
        # left panel: three-qubit tomography fidelity (Table 2) as a dot plot
        ax = plain_axes([0.6, 1.0, 0.1], [0, 4, 1], 3.6, 3.0).move_to([-2.4, 0.4, 0])
        rows = [3.5 - i for i in range(4)]
        guides = VGroup(*[DashedLine(ax.c2p(0.6, y), ax.c2p(1.0, y), color=LINE, stroke_width=1.5, dash_length=0.06) for y in rows])
        states = VGroup(*[M(f"(ket({a}) + ket({b})) \\/ sqrt(2)", 0.55).next_to(ax.c2p(0.6, y), LEFT, buff=0.25) for ((a, b), *_), y in zip(T2, rows)])
        xt = VGroup(*[T(f"{t:.1f}", 14, MUTED).next_to(ax.c2p(t, 0), DOWN, buff=0.1) for t in (0.6, 0.8, 1.0)])
        marks = VGroup()
        for (_, raw, qk, cons), y in zip(T2, rows):
            marks.add(VGroup(Circle(0.08, color=RAW, stroke_width=2.5).move_to(ax.c2p(raw, y)),
                             Square(0.15, stroke_width=0, fill_color=QISKIT, fill_opacity=1).move_to(ax.c2p(qk, y)),
                             Dot(ax.c2p(cons, y), 0.09, color=POST)))
        t_left = T("three-qubit state tomography, fidelity", 17, INK, weight=MEDIUM).move_to([-3.5, 2.55, 0])
        key_l = VGroup(VGroup(Circle(0.08, color=RAW, stroke_width=2.5), T("raw", 15)).arrange(RIGHT, buff=0.1),
                       VGroup(Square(0.15, stroke_width=0, fill_color=QISKIT, fill_opacity=1), T("Qiskit filter", 15)).arrange(RIGHT, buff=0.1),
                       VGroup(Dot(radius=0.09, color=POST), T("consistent Bayesian", 15)).arrange(RIGHT, buff=0.1)
                       ).arrange(RIGHT, buff=0.3).move_to([-3.5, -1.6, 0])
        notes_l = VGroup(T("Qiskit's filter models correlated readout, with more parameters", 14, MUTED),
                         T("two-qubit states: all filters 0.978–0.981", 14, MUTED)).arrange(DOWN, buff=0.08).next_to(key_l, DOWN, buff=0.2)
        left = VGroup(ax, guides, states, xt, marks, t_left, key_l, notes_l)

        # right panel: Grover Pr(|11>) at hour 0, then over 16 hours (Table 3)
        order = ["raw", "Qiskit", "QDT", "standard", "consistent"]
        gx = plain_axes([0, 5, 1], [0, 1, 0.5], 5.0, 3.0).move_to([3.7, 0.2, 0])
        gbars = VGroup(*[bar(gx, 0.5 + i, T3[k][0], COLORS[k], half=0.3, opacity=0.45 if k == "standard" else 0.85) for i, k in enumerate(order)])
        glabs = VGroup(*[T(k, 14).next_to(gx.c2p(0.5 + i, 0), DOWN, buff=0.12) for i, k in enumerate(order)])
        g_ideal = VGroup(DashedLine(gx.c2p(0, 1), gx.c2p(5, 1), color=INK, stroke_width=2, dash_length=0.08),
                         T("ideal", 14, INK).next_to(gx.c2p(5, 1), RIGHT, buff=0.08))
        t_right = VGroup(T("Grover search, hour 0,", 17, INK, weight=MEDIUM), M("Pr(ket(11))", 0.7)).arrange(RIGHT, buff=0.15).move_to([3.7, 2.55, 0])
        grover = VGroup(gx, gbars, glabs, g_ideal)
        hx = plain_axes([0, 16, 4], [0.6, 1.0, 0.1], 5.0, 3.0).move_to([3.3, 0.2, 0])
        lines = VGroup(*[hx.plot_line_graph(HOURS, T3[k], line_color=COLORS[k], stroke_width=3.5, vertex_dot_radius=0.05,
                                            vertex_dot_style={"color": COLORS[k]}) for k in ("raw", "Qiskit", "QDT", "consistent")])
        l_labs = VGroup(T("consistent", 15, POST).next_to(hx.c2p(16, T3["consistent"][-1]), RIGHT, buff=0.1),
                        VGroup(T("Qiskit", 15, QISKIT), T("and", 15, MUTED), T("QDT", 15, QDT)).arrange(RIGHT, buff=0.08)
                        .next_to(hx.c2p(16, T3["Qiskit"][-1]), RIGHT, buff=0.1).shift(0.1 * UP),
                        T("raw", 15, RAW).next_to(hx.c2p(16, T3["raw"][-1]), RIGHT, buff=0.1).shift(0.1 * DOWN))
        h_ticks = VGroup(*[T(str(h), 14, MUTED).next_to(hx.c2p(h, 0.6), DOWN, buff=0.1) for h in (0, 4, 8, 12, 16)],
                         T("hours after the filter data", 14, MUTED).next_to(hx.c2p(8, 0.6), DOWN, buff=0.4),
                         *[T(f"{t:.1f}", 14, MUTED).next_to(hx.c2p(0, t), LEFT, buff=0.1) for t in (0.6, 0.8, 1.0)])
        t_hours = VGroup(T("Grover search, same filters,", 17, INK, weight=MEDIUM), M("Pr(ket(11))", 0.7)).arrange(RIGHT, buff=0.15).move_to(t_right)

        # left panel, second: QAOA optimal-cut probability at hour 0 (Table 5)
        qx = plain_axes([0, 5, 1], [0, 1, 0.5], 5.0, 3.0).move_to([-3.6, 0.2, 0])
        qbars = VGroup(*[bar(qx, 0.5 + i, T5[k], COLORS[k], half=0.3, opacity=0.45 if k == "standard" else 0.85) for i, k in enumerate(order)])
        qlabs = VGroup(*[T(k, 14).next_to(qx.c2p(0.5 + i, 0), DOWN, buff=0.12) for i, k in enumerate(order)])
        q_sim = VGroup(DashedLine(qx.c2p(0, T5["simulator"]), qx.c2p(5, T5["simulator"]), color=INK, stroke_width=2, dash_length=0.08),
                       T(f"noiseless simulator {T5['simulator']:.2f}", 14, INK).next_to(qx.c2p(0, T5["simulator"]), UP, buff=0.08).align_to(qx, LEFT).shift(0.15 * RIGHT))
        t_qaoa = T("QAOA Max-Cut, hour 0, probability of an optimal cut", 17, INK, weight=MEDIUM).move_to([-3.6, 2.55, 0])
        foot = T("consistent above standard at all six times for Grover and QAOA, nearly equal on random two-qubit Clifford circuits",
                 15, MUTED).move_to([0, -3.3, 0])
        qdt_note = T("filters from posterior means · QDT: filter from quantum detector tomography", 14, MUTED).move_to([0, -2.75, 0])
        with self.voice("apply") as v:
            self.play(FadeIn(head), run_time=0.6)
            v.until(1)
            self.play(Create(ax), FadeIn(guides), FadeIn(states), FadeIn(xt), FadeIn(t_left), FadeIn(key_l), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(m[0]) for m in marks], lag_ratio=0.1), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(m[1]) for m in marks], lag_ratio=0.1), run_time=0.8)
            self.play(LaggedStart(*[GrowFromCenter(m[2]) for m in marks], lag_ratio=0.1), run_time=0.8)
            self.play(FadeIn(notes_l), run_time=0.7)
            v.until(2)
            self.play(Create(gx), FadeIn(glabs), FadeIn(g_ideal), FadeIn(t_right), FadeIn(qdt_note), run_time=0.9)
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in gbars], lag_ratio=0.25), run_time=2.4)
            v.until(3)
            self.play(FadeOut(grover), FadeTransform(t_right, t_hours), run_time=0.7)
            self.play(Create(hx), FadeIn(h_ticks), run_time=0.7)
            self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.2), FadeIn(l_labs), run_time=1.6)
            v.until(4)
            self.play(FadeOut(left), run_time=0.6)
            self.play(Create(qx), FadeIn(qlabs), FadeIn(q_sim), FadeIn(t_qaoa), run_time=0.9)
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in qbars], lag_ratio=0.25), run_time=2.4)
            v.until(5)
            self.play(FadeIn(foot, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def gates(self):
        head = header(7, "Gate errors from 200 NOT gates")
        y = 2.35
        circ = VGroup(wire(y, -6.3, -1.4), M("ket(0)", 0.9).move_to([-6.7, y, 0]),
                      *[gate("X", 0.6, 0.55, size=0.8).move_to([x, y, 0]) for x in (-5.4, -4.6, -2.9)],
                      VGroup(Rectangle(width=0.6, height=0.3, stroke_width=0, fill_color=PAPER, fill_opacity=1).move_to([-3.75, y, 0]),
                             T("···", 28, MUTED).move_to([-3.75, y, 0])),
                      meter().scale(0.85).move_to([-1.95, y, 0]))
        brace = Brace(VGroup(circ[2], circ[4]), DOWN, buff=0.12, color=INK)
        b_lab = VGroup(T("200 times, on qubit 1 or 2 of ibmqx2", 15, MUTED),
                       VGroup(T("ideal", 15, MUTED), M('Pr("measure" 0) = 1', 0.6, MUTED)).arrange(RIGHT, buff=0.12)).arrange(DOWN, buff=0.06).next_to(brace, DOWN, buff=0.08)
        tbl = VGroup()
        for i, row in enumerate([("", "qubit 1", "qubit 2"), ("consistent", *[f"{g:.4f}" for g in T6["consistent"]]),
                                 ("standard", *[f"{g:.4f}" for g in T6["standard"]])]):
            cells = VGroup(*[T(c, 19, POST if (i == 1 and j) else INK, weight=MEDIUM if i == 0 or (i == 1 and j) else NORMAL) for j, c in enumerate(row)])
            for j, c in enumerate(cells):
                c.move_to([1.2 + [0, 2.4, 4.1][j], 2.3 - 0.5 * i, 0], aligned_edge=LEFT if j == 0 else ORIGIN)
            tbl.add(cells)
        tbl_t = VGroup(T("posterior mean gate error rate", 16, MUTED), M("epsilon_g", 0.65, MUTED), T("(Table 6)", 14, MUTED)).arrange(RIGHT, buff=0.1).next_to(tbl, UP, buff=0.2).align_to(tbl, LEFT)
        c1 = card([VGroup(T("consistent posterior:", 19, POST, weight=MEDIUM), T("predictions match the shape of the data distribution", 19)).arrange(RIGHT, buff=0.15),
                   VGroup(T("standard posterior:", 19, INK, weight=MEDIUM), T("predictions match only the mean", 19)).arrange(RIGHT, buff=0.15)],
                  11.5, LINE).move_to([0, -0.5, 0])
        c2 = VGroup(T("after filtering gate and readout errors, the consistent parameters", 17, MUTED),
                    T("recover exactly 1 more often, most clearly on qubit 2", 17, MUTED)).arrange(DOWN, buff=0.06).next_to(c1, DOWN, buff=0.3)
        sx = plain_axes([0, 0.01, 0.005], [0.4, 1.0, 0.2], 3.6, 2.5).move_to([-4.4, -1.35, 0])
        mx = plain_axes([0, 0.2, 0.1], [0.4, 1.0, 0.2], 3.6, 2.5).move_to([-0.1, -1.35, 0])
        s_curve = sx.plot(lambda g: q200(g, 0, 0), x_range=[0, 0.01, 0.0001], color=ACCENT, stroke_width=4)
        m_curve = mx.plot(lambda m: q200(0.005, m, 0), x_range=[0, 0.2, 0.002], color=QISKIT, stroke_width=4)
        s_labs = VGroup(M("epsilon_g", 0.8, ACCENT).next_to(sx.x_axis, DOWN, buff=0.12),
                        T("0", 13, MUTED).next_to(sx.c2p(0, 0.4), DOWN, buff=0.08), T("0.01", 13, MUTED).next_to(sx.c2p(0.01, 0.4), DOWN, buff=0.08),
                        M("m_0 = m_1 = 0", 0.55, MUTED).next_to(sx, UP, buff=0.08).align_to(sx, RIGHT),
                        T("Pr(0)", 14, MUTED).next_to(sx, UP, buff=0.08).align_to(sx, LEFT),
                        *[T(f"{t:.1f}", 13, MUTED).next_to(sx.c2p(0, t), LEFT, buff=0.08) for t in (0.4, 0.7, 1.0)])
        m_labs = VGroup(M("m_0", 0.8, QISKIT).next_to(mx.x_axis, DOWN, buff=0.12),
                        T("0", 13, MUTED).next_to(mx.c2p(0, 0.4), DOWN, buff=0.08), T("0.2", 13, MUTED).next_to(mx.c2p(0.2, 0.4), DOWN, buff=0.08),
                        M("epsilon_g = 0.005, thin m_1 = 0", 0.55, MUTED).next_to(mx, UP, buff=0.08).align_to(mx, RIGHT))
        model = T("forward model, Eq. (13), 200 gates", 14, MUTED).next_to(VGroup(sx, mx), DOWN, buff=0.45)
        grov = card([T("Grover search, hour 0, consistent mean", 16, MUTED),
                     VGroup(T("readout rates from the H-gate circuit", 17), T(f"{T3['consistent'][0]:.2f}", 17, POST, weight=MEDIUM)).arrange(RIGHT, buff=0.25),
                     VGroup(T("readout rates from the 200-NOT circuit", 17), T(f"{T7:.2f}", 17, POST, weight=MEDIUM)).arrange(RIGHT, buff=0.25),
                     VGroup(T("Qiskit filter and QDT", 17, MUTED), T(f"{T3['Qiskit'][0]:.2f}", 17, MUTED)).arrange(RIGHT, buff=0.25)],
                    4.6, LINE, pad=0.22).move_to([4.6, -1.35, 0])
        with self.voice("gates") as v:
            self.play(FadeIn(head), FadeIn(circ), run_time=1.0)
            self.play(GrowFromCenter(brace), FadeIn(b_lab), run_time=0.8)
            v.until(1)
            self.play(FadeIn(tbl_t), LaggedStart(*[FadeIn(r) for r in tbl], lag_ratio=0.3), run_time=1.4)
            v.until(2)
            self.play(FadeIn(c1, shift=0.1 * UP), run_time=1.0)
            v.until(3)
            self.play(FadeIn(c2), run_time=0.8)
            v.until(4)
            self.play(FadeOut(c1), FadeOut(c2), run_time=0.6)
            self.play(Create(sx), FadeIn(s_labs), Create(s_curve), run_time=1.4)
            self.play(Create(mx), FadeIn(m_labs), Create(m_curve), FadeIn(model), run_time=1.4)
            v.until(4, 0.6)
            self.play(FadeIn(grov, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def limits(self):
        head = header(8, "Limits")
        rows = VGroup(
            VGroup(T("Filter matrices have", 24), M("2^n times 2^n", 0.95), T("entries for n measured qubits.", 24)).arrange(RIGHT, buff=0.15),
            T("The multi-gate model covers bit flips on gates that commute with X up to a phase.", 24),
            T("Gate errors were inferred only in simple test circuits, all on one 5-qubit device.", 24),
            T("Readout errors are assumed independent across qubits.", 24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to([0.2, 0.2, 0])
        marks = VGroup(*[Line(r.get_left() + 0.35 * LEFT + 0.2 * UP, r.get_left() + 0.35 * LEFT + 0.2 * DOWN, color=ACCENT, stroke_width=5) for r in rows])
        with self.voice("limits") as v:
            self.play(FadeIn(head), FadeIn(rows[0], shift=0.1 * UP), FadeIn(marks[0]), run_time=1.0)
            v.until(1)
            self.play(FadeIn(rows[1], shift=0.1 * UP), FadeIn(marks[1]), run_time=0.8)
            v.until(1, 0.55)
            self.play(FadeIn(rows[2], shift=0.1 * UP), FadeIn(marks[2]), run_time=0.8)
            v.until(2)
            self.play(FadeIn(rows[3], shift=0.1 * UP), FadeIn(marks[3]), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("Error rates inferred as distributions from a few test circuits", 30, weight=MEDIUM),
                       T("gave posterior-mean readout filters that outperformed Qiskit's", 30, weight=MEDIUM),
                       T("filter and detector tomography in Grover and QAOA tests on ibmqx2.", 30, weight=MEDIUM),
                       T("The number of test circuits is constant or linear in the number of qubits.", 21, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        lines[3].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the paper"),
                      T("Zheng, Li, Terlaky, Yang. ACM Transactions on Quantum Computing 4(2), 11 (2023)", 20),
                      T("doi.org/10.1145/3563397   ·   arXiv:2010.09188", 20, ACCENT),
                      T("Code: github.com/QCOL-LU/Bayesian-Error-Characterization-and-Mitigation", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.3), run_time=2.6)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class BayesianPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Bayesian error characterization", size=30).to_corner(UL, buff=0.6)
        ax = plain_axes([0, 0.3, 0.1], [0, 0.3, 0.1], 5.2, 4.4).move_to([-3.0, -0.3, 0])
        dots = VGroup(*[Dot(ax.c2p(a, b), 0.05 if k else 0.04, color=POST if k else MUTED).set_opacity(1 if k else 0.3)
                        for a, b, k in SAMPLES])
        labs = VGroup(M("m_0", 1.4).next_to(ax.x_axis, DOWN, buff=0.15).align_to(ax, RIGHT),
                      M("m_1", 1.4).next_to(ax.y_axis, LEFT, buff=0.15).align_to(ax, UP))
        sub = VGroup(T("error rates", 44, INK, weight=MEDIUM), T("as distributions", 44, POST, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.6, -0.3, 0])
        self.add(label, ax, dots, labs, sub)
