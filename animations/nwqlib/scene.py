"""Explainer for NWQLib, the Northwest Quantum Library (Pacific Northwest National Laboratory).

One algorithm carries the video: QLS on the steady heat of a 4 x 4 plate, through plan, estimate and
solve, then the same planning and estimation on a ring of 2**100 sites. Every number comes from
data.json, recomputed with the public NWQLib workflow (see extract_data.py). The plotted polynomial,
eigenvalues and phase angles are those of the plate's Plan. The circuit drawings are schematic.
The method catalog follows README.md and `python -m nwqlib algorithms`.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

NW = ACCENT        # NWQLib's selections, estimates and results
QPU = DV           # qubits, circuits, compilation and simulators
REF = GOLD         # classical reference (numpy)
VERSION = "1.0.0"  # the release; 1.0.0.post1, which computed data.json, changed only the README
DATA = json.loads(Path(__file__).resolve().with_name("data.json").read_text())  # house_style rebinds HERE
PLATE = DATA["plate"]
SCALE = DATA["scaling"]
HEAT = [PAPER, "#e9cfae", "#c98f6c", NW, "#4b2530"]
AUTHORS = ("Muqing Zheng, Chenxu Liu, Zhixin Song, Zeguan Wu, Xiangyu Li, Mingze Li, Nicholas P. Bauman,",
           "Samuel A. Stein, Johannes Mülmenstädt, Yousu Chen, Nathan Wiebe, Ang Li, Karol Kowalski")
PLACES = ("Pacific Northwest National Laboratory · Georgia Institute of Technology · University of Pittsburgh",
          "University of Toronto · University of Washington")


def C(text, size=20, color=INK):
    """Code in Menlo, laid out at 4x size like T()."""
    saved = config.pixel_width
    config.pixel_width = 8000
    try:
        return Text(text, font="Menlo", font_size=4 * size, color=color).scale(0.25)
    finally:
        config.pixel_width = saved


def heat(t):
    t = float(np.clip(t, 0, 1)) * (len(HEAT) - 1)
    i = min(int(t), len(HEAT) - 2)
    return interpolate_color(ManimColor(HEAT[i]), ManimColor(HEAT[i + 1]), t - i)


def box(title, sub=None, color=INK, width=2.6, height=None, size=22, sub_size=17, dashed=False):
    parts = [T(title, size, color, weight=MEDIUM)]
    if sub is not None:
        parts.append(sub if isinstance(sub, Mobject) else T(sub, sub_size, MUTED))
    body = VGroup(*parts).arrange(DOWN, buff=0.1)
    h = height or body.height + 0.36
    frame = RoundedRectangle(corner_radius=0.1, width=max(width, body.width + 0.36), height=h, stroke_color=color,
                             stroke_width=2.5, fill_color=PAPER, fill_opacity=1)
    if dashed:
        frame = DashedVMobject(frame, num_dashes=44)
    return VGroup(frame, body.move_to(frame))


def arrow(a, b, color=MUTED, buff=0.1, width=3):
    return Arrow(a, b, buff=buff, color=color, stroke_width=width, max_tip_length_to_length_ratio=0.12, tip_length=0.18)


def plate_map(values=None, cell=0.75):
    """4 x 4 temperature map, grid row 0 at the bottom as in the notebook's imshow(origin='lower').
    Without values the cells are blank."""
    g = PLATE["grid"]
    vmax = max(PLATE["reference"])
    cells = VGroup()
    for r in range(g):
        for c in range(g):
            fill = PAPER if values is None else heat(values[r * g + c] / vmax)
            sq = Square(cell, stroke_color=LINE if values is None else PAPER, stroke_width=1.5, fill_color=fill, fill_opacity=1)
            cells.add(sq.move_to([(c - 1.5) * cell, (r - 1.5) * cell, 0]))
    edge = Square(g * cell + 0.14, stroke_color=INK, stroke_width=6)
    return VGroup(edge, cells)


def color_bar(height=3.0, width=0.24):
    n = 40
    bar = VGroup(*[Rectangle(width=width, height=height / n, stroke_width=0, fill_color=heat(i / (n - 1)), fill_opacity=1)
                   .move_to([0, -height / 2 + (i + 0.5) * height / n, 0]) for i in range(n)])
    vmax = max(PLATE["reference"])
    ticks = VGroup(T("0", 17, MUTED).next_to(bar, RIGHT, buff=0.1).align_to(bar, DOWN),
                   T(f"{vmax:.3f}", 17, MUTED).next_to(bar, RIGHT, buff=0.1).align_to(bar, UP))
    return VGroup(bar, ticks)


def code_panel(lines, size=22, buff=0.26):
    body = VGroup(*[C(l, size) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    panel = RoundedRectangle(corner_radius=0.12, width=body.width + 0.7, height=body.height + 0.6, stroke_width=0,
                             fill_color=WASH, fill_opacity=1)
    return VGroup(panel, body.move_to(panel))


def chip(text, color, size=18, filled=False):
    label = T(text, size, PAPER if filled else color, weight=MEDIUM)
    frame = RoundedRectangle(corner_radius=0.16, width=label.width + 0.36, height=label.height + 0.24, stroke_color=color,
                             stroke_width=2, fill_color=color if filled else PAPER, fill_opacity=1)
    return VGroup(frame, label.move_to(frame))


def circuit(width=12.0, gap=0.3):
    """Schematic of the plate's QLS circuit: five ancillas above four system qubits, the preparation of b,
    alternating block-encoding queries U and phase rotations, and the ancilla readout."""
    ys = [1.2 - gap * k for k in range(9)]
    x0, x1 = -width / 2 + 1.6, width / 2
    wires = VGroup(*[wire(y, x0, x1, QPU if k < 5 else INK, 2.2) for k, y in enumerate(ys)])
    labels = VGroup(T("5 ancillas", 19, QPU).next_to([x0, np.mean(ys[:5]), 0], LEFT, buff=0.15),
                    T("4 system qubits", 19, INK).next_to([x0, np.mean(ys[5:]), 0], LEFT, buff=0.15))
    sys_mid = np.mean(ys[5:])
    prep = box("b", None, INK, width=0.62, height=ys[5] - ys[8] + 0.3, size=20).move_to([x0 + 0.6, sys_mid, 0])
    top, bot = ys[1] + 0.14, ys[8] - 0.14
    queries, phis = VGroup(), VGroup()
    xs = [x0 + 1.75 + 0.95 * k for k in range(4)] + [x1 - 1.55]
    for k, x in enumerate(xs):
        queries.add(box("U" if k % 2 == 0 else "U†", None, QPU, width=0.56, height=top - bot, size=19).move_to([x, (top + bot) / 2, 0]))
        phis.add(box("φ", None, NW, width=0.4, height=0.36, size=16).move_to([x + 0.47, ys[0], 0]))
    dots = T("⋯", 30, MUTED).move_to([(xs[3] + xs[4]) / 2 + 0.25, (top + bot) / 2, 0])
    meters = VGroup(*[meter(QPU).scale(0.36).move_to([x1 - 0.32, y, 0]) for y in ys[:5]])
    group = VGroup(wires, labels, prep, queries, phis, dots, meters)
    group.ys, group.x0, group.x1 = ys, x0, x1
    return group


class NWQLibExplainer(Explainer):
    timing_file = BUILD / "nwqlib" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.plate()
        self.workflow()
        self.plan()
        self.estimate()
        self.solve()
        self.scale()
        self.methods()
        self.get()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        label = eyebrow(f"Scientific software · Release {VERSION}")
        title = VGroup(T("NWQLib", 66, weight=MEDIUM),
                       T("Northwest Quantum Library", 36, MUTED, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        what = T("Quantum algorithms applied to scientific problems", 27)
        authors = VGroup(*[T(a, 20, MUTED) for a in AUTHORS]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        places = VGroup(*[T(p, 17, MUTED) for p in PLACES]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        block = VGroup(label, title, what, authors, places).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        places.next_to(authors, DOWN, buff=0.18, aligned_edge=LEFT)
        block.move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(block.get_corner(UL) + 0.35 * UP, block.get_corner(UL) + 0.35 * UP + 1.2 * RIGHT, color=NW, stroke_width=4)
        self.play(Create(rule), FadeIn(label, shift=0.1 * RIGHT), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in (title, what, authors, places)], lag_ratio=0.25), run_time=1.8)
        self.wait(2.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 01
    def plate(self):
        head = header(1, "A linear system")
        g = PLATE["grid"]
        plate = plate_map(cell=0.85).move_to([-4.0, 0.15, 0])
        centers = [plate[1][r * g + c].get_center() for r in range(g) for c in range(g)]
        heaters = VGroup(*[Dot(centers[r * g + c], radius=0.11 + 0.07 * p, color=NW) for r, c, p in PLATE["heaters"]])
        heat_lab = T("two heaters", 21, NW).next_to(plate, UP, buff=0.22)
        edge_lab = T("edges held cold", 21, INK).next_to(plate, DOWN, buff=0.22)
        nodes = VGroup(*[Dot(p, radius=0.045, color=MUTED) for p in centers])
        unknowns = T("16 grid points → 16 unknown temperatures", 21, MUTED).next_to(edge_lab, DOWN, buff=0.14)

        chain = 2 * np.eye(g) - np.eye(g, k=1) - np.eye(g, k=-1)
        A = np.kron(chain, np.eye(g)) + np.kron(np.eye(g), chain)
        pitch = 0.2
        mat = VGroup(*[Dot([pitch * j, -pitch * i, 0], radius=0.06 if A[i, j] else 0.022, color=INK if A[i, j] else LINE)
                       for i in range(16) for j in range(16)]).move_to([3.4, 0.15, 0])
        brackets = VGroup(*[Line(mat.get_corner(c) + s * 0.18 * RIGHT + 0.12 * UP, mat.get_corner(c) + s * 0.18 * RIGHT
                                 + (mat.height + 0.12) * DOWN, color=INK, stroke_width=2.5) for c, s in ((UL, -1), (UR, 1))])
        eq = M("A x = b", 1.6).next_to(mat, UP, buff=0.45)
        mat_lab = T(f"A: 16 × 16, {PLATE['A_nonzeros']} nonzeros", 20, MUTED).next_to(mat, DOWN, buff=0.3)
        link = arrow(plate.get_right() + 0.3 * RIGHT, mat.get_left() + 0.45 * LEFT, color=MUTED)

        def card(title, body, color):
            frame = RoundedRectangle(corner_radius=0.12, width=2.62, height=2.35, stroke_color=color, stroke_width=2.5,
                                     fill_color=PAPER, fill_opacity=1)
            t = T(title, 20, color, weight=MEDIUM).move_to(frame.get_top() + 0.34 * DOWN)
            body.move_to(frame.get_center() + 0.22 * DOWN)
            return VGroup(frame, t, body)

        unitary = VGroup(Square(1.25, stroke_color=QPU, stroke_width=2.5),
                         Square(0.62, stroke_width=0, fill_color=WASH, fill_opacity=1).shift([-0.31, 0.31, 0]))
        unitary.add(M("A slash alpha", 0.62).move_to(unitary[1]), M("dots.c", 0.7, MUTED).move_to(unitary[0].get_center() + [0.31, -0.31, 0]))
        prep_body = VGroup(M("ket(0 dots 0) arrow ket(b)", 0.72), M("ket(b) = b slash norm(b)", 0.72)).arrange(DOWN, buff=0.22)
        ax_small = Axes(x_range=[-1, 1, 1], y_range=[-1.3, 1.3, 1], x_length=2.0, y_length=1.2, tips=False,
                        axis_config={"color": MUTED, "stroke_width": 1.5, "include_ticks": False})
        coeffs = np.array(PLATE["chebyshev"])
        mini = ax_small.plot(lambda x: np.polynomial.chebyshev.chebval(x, coeffs), x_range=[-1, 1, 0.005], color=NW, stroke_width=2.5)
        poly_body = VGroup(ax_small, mini, M("P(x) approx 1 slash (kappa x)", 0.55).next_to(ax_small, DOWN, buff=0.08))
        phase_body = VGroup(M("phi_0, phi_1, dots, phi_d", 0.8), T("d + 1 angles", 16, MUTED)).arrange(DOWN, buff=0.18)
        state_body = VGroup(M("ket(x) = x slash norm(x)", 0.8), T("length one", 16, MUTED)).arrange(DOWN, buff=0.18)
        cards = VGroup(card("state preparation", prep_body, INK), card("block encoding", unitary, QPU),
                       card("inverse polynomial", poly_body, NW), card("phase angles", phase_body, NW),
                       card("output state", state_body, QPU)).arrange(RIGHT, buff=0.2)
        cards.move_to([0, -2.05, 0])

        with self.voice("plate") as v:
            self.play(FadeIn(head), FadeIn(plate), FadeIn(edge_lab), run_time=1.0)
            pulses = [Circle(0.2, color=NW, stroke_width=3).move_to(h) for h in heaters for _ in range(2)]
            self.play(LaggedStart(*[GrowFromCenter(h) for h in heaters], lag_ratio=0.4), FadeIn(heat_lab), run_time=0.9)
            self.play(LaggedStart(*[p.animate(rate_func=rush_from).scale(4.5).set_stroke(opacity=0) for p in pulses], lag_ratio=0.25),
                      run_time=1.6)
            self.remove(*pulses)
            self.play(FadeIn(nodes, lag_ratio=0.05), FadeIn(unknowns), run_time=1.0)
            self.bring_to_front(heaters)
            v.until(0, 0.55)
            self.play(GrowArrow(link), LaggedStart(*[FadeIn(d) for d in mat], lag_ratio=0.003), FadeIn(brackets), run_time=1.8)
            self.play(Write(eq), FadeIn(mat_lab), run_time=1.0)
            v.until(1)
            top = VGroup(plate, heaters, heat_lab, edge_lab, nodes, link, mat, brackets, eq, mat_lab)
            self.play(FadeOut(unknowns), top.animate.scale(0.62).move_to([0, 1.25, 0]), run_time=1.0)
            for k, frac in enumerate((0.24, 0.35, 0.45, 0.62, 0.82)):
                v.until(1, frac)
                self.play(FadeIn(cards[k], shift=0.15 * UP), run_time=0.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def workflow(self):
        head = header(2, "One workflow")
        name = VGroup(T("NWQLib", 44, NW, weight=MEDIUM),
                      T("Northwest Quantum Library · Pacific Northwest National Laboratory", 22, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        name.next_to(head, DOWN, buff=0.4, aligned_edge=LEFT)
        inputs = VGroup(M("A, quad b", 1.3), T("your matrix and right-hand side", 18, MUTED)).arrange(DOWN, buff=0.15).move_to([-5.0, -0.6, 0])
        inside = VGroup(*[T(t, 21, INK) for t in ("state preparation", "block encoding", "inverse polynomial", "phase angles", "circuit")]).arrange(DOWN, buff=0.16)
        core = VGroup(RoundedRectangle(corner_radius=0.15, width=4.2, height=inside.height + 1.0, stroke_color=NW, stroke_width=3.5,
                                       fill_color=PAPER, fill_opacity=1), T("NWQLib", 24, NW, weight=MEDIUM))
        core[1].move_to(core[0].get_top() + 0.3 * DOWN)
        inside.move_to(core[0].get_center() + 0.2 * DOWN)
        core.add(inside)
        core.move_to([0, -0.6, 0])
        out = VGroup(M("x", 1.6, NW), T("physical scale and phase", 18, NW)).arrange(DOWN, buff=0.15).move_to([5.0, -0.6, 0])
        a_in = arrow(inputs.get_right(), core.get_left(), buff=0.25)
        a_out = arrow(core.get_right(), out.get_left(), color=NW, buff=0.25)

        code = code_panel(["problem  = LinearSystem(A=A, b=b)",
                           "method   = QLS(epsilon_inv=0.01)",
                           "selected = plan(problem, method=method)",
                           "cost     = estimate(selected)",
                           "result   = solve(selected)"], size=23)
        notes = VGroup(*[T(t, 21, NW) for t in ("your matrix and right-hand side", "quantum linear solver, ε = 0.01",
                                                "selects the construction", "counts its gates", "runs it")])
        code.move_to([-2.2, -0.85, 0])
        for line, note in zip(code[1], notes):
            note.next_to([code.get_right()[0], line.get_y(), 0], RIGHT, buff=0.35)
        bars = VGroup(*[Rectangle(width=0.08, height=line.height + 0.12, stroke_width=0, fill_color=NW, fill_opacity=1)
                        .next_to(line, LEFT, buff=0.16) for line in code[1]])

        with self.voice("workflow") as v:
            self.play(FadeIn(head), FadeIn(name, shift=0.1 * RIGHT), run_time=1.0)
            self.play(FadeIn(inputs), GrowArrow(a_in), FadeIn(core[0]), FadeIn(core[1]), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(t, shift=0.08 * DOWN) for t in inside], lag_ratio=0.3), run_time=1.6)
            v.until(0, 0.62)
            self.play(GrowArrow(a_out), FadeIn(out, shift=0.1 * RIGHT), run_time=1.0)
            v.until(1)
            self.play(FadeOut(VGroup(inputs, a_in, core, a_out, out)), FadeIn(code[0]), run_time=0.6)
            for k, frac in enumerate((0.0, 0.2, 0.54, 0.73, 0.9)):
                v.until(1, frac)
                self.play(FadeIn(code[1][k]), FadeIn(bars[k]), FadeIn(notes[k], shift=0.08 * RIGHT), run_time=0.45)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def plan(self):
        head = header(3, "Plan")
        kappa = PLATE["polynomial_kappa"]
        eig = np.array(PLATE["eigenvalues_over_alpha"])
        coeffs = np.array(PLATE["chebyshev"])
        ax = Axes(x_range=[-1, 1, 0.5], y_range=[-1.3, 1.3, 0.5], x_length=11.0, y_length=4.4, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([0, -0.85, 0])
        xt = VGroup(T("−1", 18, MUTED).next_to(ax.c2p(-1, 0), UP, buff=0.12), T("1", 18, MUTED).next_to(ax.c2p(1, 0), DOWN, buff=0.12))
        zero = T("0", 18, MUTED).next_to(ax.c2p(0, 0), DOWN + LEFT, buff=0.08)
        values, counts = np.unique(np.round(eig, 9), return_counts=True)
        stacks = VGroup(*[Dot(ax.c2p(x, 0) + (0.2 + 0.19 * k) * DOWN, radius=0.075, color=NW)
                          for x, n in zip(values, counts) for k in range(n)])
        eig_lab = T("eigenvalues of A/α", 21, NW).next_to(stacks, DOWN, buff=0.18).align_to(ax.c2p(0.45, 0), LEFT)
        enc = VGroup(T("Pauli block encoding", 26, NW, weight=MEDIUM), M(f"alpha = {PLATE['alpha']:g}", 1.0, NW)).arrange(RIGHT, buff=0.35)
        enc.next_to(head, DOWN, buff=0.35, aligned_edge=LEFT)
        lo, hi = eig.min(), eig.max()
        span = VGroup(Line(ax.c2p(lo, 0) + 0.12 * UP, ax.c2p(hi, 0) + 0.12 * UP, color=NW, stroke_width=5))
        span_lab = VGroup(T(f"{lo:.3f}", 18, NW).next_to(ax.c2p(lo, 0), UP, buff=0.22),
                          T(f"{hi:.3f}", 18, NW).next_to(ax.c2p(hi, 0), UP, buff=0.22))
        kap = M(f"kappa = alpha slash sigma_min (A) = {PLATE['kappa']:.1f}", 1.0, NW).next_to(enc, RIGHT, buff=0.8)

        gap = Rectangle(width=ax.c2p(1 / kappa, 0)[0] - ax.c2p(-1 / kappa, 0)[0], height=4.4, stroke_width=0,
                        fill_color=WASH, fill_opacity=1).move_to(ax.c2p(0, 0))
        target = VGroup(*[ax.plot(lambda x: 1 / (kappa * x), x_range=r, color=MUTED, stroke_width=3.5, use_smoothing=False)
                          for r in ([1 / kappa, 1, 0.002], [-1, -1 / kappa, 0.002])])
        target = VGroup(*[DashedVMobject(t, num_dashes=40) for t in target])
        poly = ax.plot(lambda x: np.polynomial.chebyshev.chebval(x, coeffs), x_range=[-1, 1, 0.0025], color=NW, stroke_width=4.5,
                       use_smoothing=False)
        p_lab = VGroup(M("P(x)", 0.95, NW), T(f"odd, degree {PLATE['degree']}", 20, NW)).arrange(RIGHT, buff=0.2)
        p_lab.next_to(ax.c2p(0.12, 1.12), RIGHT, buff=0.15)
        t_lab = M("1 slash (kappa x)", 0.85, MUTED).next_to(ax.c2p(0.55, 1 / (kappa * 0.55)), UP + RIGHT, buff=0.08)
        bound = M("abs(kappa x P(x) - 1) <= 0.01 \" on \" [1 slash kappa, 1]", 0.78, NW).move_to(ax.c2p(-0.98, 1.25), aligned_edge=UL)

        phases = np.array(PLATE["phases"])
        inner = phases[1:-1]
        bw, pitch, scale = 0.11, 0.165, 9.0
        x_start = -pitch * (len(inner) - 1) / 2
        base_y = 1.15
        bars = VGroup(*[Rectangle(width=bw, height=max(abs(p) * scale, 0.01), stroke_width=0, fill_color=NW, fill_opacity=0.9)
                        .move_to([x_start + pitch * k, base_y + p * scale / 2, 0]) for k, p in enumerate(inner)])
        axis_line = Line([x_start - 0.4, base_y, 0], [-x_start + 0.4, base_y, 0], color=MUTED, stroke_width=1.5)
        ph_lab = VGroup(T(f"{len(phases)} phase angles", 24, NW, weight=MEDIUM),
                        T(f"φ1 to φ{len(phases) - 2}, shown as bars", 17, MUTED),
                        T(f"φ0 = φ{len(phases) - 1} = {phases[0]:.3f}", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        ph_lab.next_to(head, DOWN, buff=0.3, aligned_edge=LEFT)
        circ = circuit().move_to([0.4, -1.85, 0])
        qubits = T(f"{PLATE['qubits']} qubits", 26, QPU, weight=MEDIUM).next_to(circ, UP, buff=0.12).align_to(circ, RIGHT)

        with self.voice("plan") as v:
            self.play(FadeIn(head), FadeIn(enc, shift=0.1 * RIGHT), run_time=0.9)
            self.play(Create(ax.x_axis), FadeIn(xt), FadeIn(zero), run_time=0.8)
            v.until(1)
            self.play(LaggedStart(*[FadeIn(d, shift=0.25 * UP) for d in stacks], lag_ratio=0.08), FadeIn(eig_lab), run_time=1.6)
            self.play(Create(span), FadeIn(span_lab), run_time=0.8)
            v.until(1, 0.45)
            self.play(Write(kap), run_time=1.0)
            v.until(2)
            self.play(FadeIn(gap), Create(ax.y_axis), FadeOut(span), FadeOut(span_lab), run_time=0.6)
            self.bring_to_front(ax.x_axis, stacks)
            self.play(Create(target), FadeIn(t_lab), run_time=1.0)
            self.play(Create(poly), run_time=max(v.dur(2) * 0.35, 2.5), rate_func=linear)
            self.play(FadeIn(p_lab), run_time=0.5)
            v.until(2, 0.62)
            self.play(FadeIn(bound, shift=0.1 * UP), run_time=0.8)
            v.until(3)
            self.clear_stage(keep=[head], run_time=0.5)
            self.play(Create(axis_line), FadeIn(ph_lab[0]), run_time=0.5)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN if p > 0 else UP) for b, p in zip(bars, inner)], lag_ratio=0.03),
                      FadeIn(ph_lab[1:]), run_time=1.6)
            v.until(3, 0.38)
            self.play(Create(circ[0]), FadeIn(circ[1:]), FadeIn(qubits), run_time=1.4)
        self.circ = circ
        self.clear_stage(keep=[circ])

    # ------------------------------------------------------------------ 04
    def estimate(self):
        head = header(4, "Estimate")
        circ = self.circ
        sub = T("a gate-count formula for each block, no circuit built", 20, NW).next_to(circ, UP, buff=0.25).align_to(circ, LEFT)
        scale = 8.0 / 8000
        x0 = -5.6
        bar_e = Rectangle(width=PLATE["cx_estimate"] * scale, height=0.5, stroke_width=0, fill_color=NW, fill_opacity=0.9)
        bar_e.move_to([x0, -0.85, 0], aligned_edge=LEFT)
        bar_c = Rectangle(width=PLATE["cx_compiled"] * scale, height=0.5, stroke_width=0, fill_color=QPU, fill_opacity=0.9)
        bar_c.move_to([x0, -2.35, 0], aligned_edge=LEFT)
        lab_e = T("predicted by estimate", 21, NW).next_to(bar_e, UP, buff=0.12).align_to(bar_e, LEFT)
        lab_c = T("compiled by Qiskit, optimization level 1", 21, QPU).next_to(bar_c, UP, buff=0.12).align_to(bar_c, LEFT)
        val_e = T(f"{PLATE['cx_estimate']:,.0f} CX", 28, NW, weight=MEDIUM).next_to(bar_e, RIGHT, buff=0.2)
        val_c = T(f"{PLATE['cx_compiled']:,} CX", 28, QPU, weight=MEDIUM).next_to(bar_c, RIGHT, buff=0.2)

        kinds = VGroup(chip("exact", INK, 24), chip("upper bound", INK, 24), chip("estimate", NW, 24), chip("unavailable", MUTED, 24))
        kinds.arrange(RIGHT, buff=0.35).move_to([0, 1.9, 0])
        rows = [("qubits", f"{PLATE['qubits']}", chip("exact", INK, 22)),
                ("CX gates", f"{PLATE['cx_estimate']:,.0f}", chip("estimate", NW, 22)),
                ("circuit depth", "—", chip("unavailable", MUTED, 22))]
        table = VGroup()
        for k, (a, b, c) in enumerate(rows):
            y = 0.45 - 0.95 * k
            table.add(VGroup(T(a, 32, INK).move_to([-4.2, y, 0], aligned_edge=LEFT),
                             T(b, 32, NW if b != "—" else MUTED, weight=MEDIUM).move_to([0.6, y, 0], aligned_edge=RIGHT),
                             c.move_to([1.6, y, 0], aligned_edge=LEFT)))

        with self.voice("estimate") as v:
            self.play(FadeIn(head), circ.animate.scale(0.82).move_to([0.5, 1.5, 0]), run_time=0.9)
            sub.next_to(circ, UP, buff=0.18).align_to(circ, LEFT)
            tags = VGroup(*[T("CX", 15, NW, weight=MEDIUM).next_to(m, DOWN, buff=0.05) for m in [circ[2], *circ[3]]])
            self.play(FadeIn(sub), LaggedStart(*[FadeIn(t, shift=0.08 * DOWN) for t in tags], lag_ratio=0.2), run_time=1.2)
            v.until(0, 0.55)
            self.play(*[t.animate.move_to(bar_e.get_left() + 0.2 * RIGHT).set_opacity(0) for t in tags],
                      GrowFromEdge(bar_e, LEFT), FadeIn(lab_e), run_time=1.2)
            self.play(FadeIn(val_e, shift=0.1 * RIGHT), run_time=0.6)
            v.until(1)
            self.play(GrowFromEdge(bar_c, LEFT), FadeIn(lab_c), FadeIn(val_c, shift=0.1 * RIGHT), run_time=1.2)
            v.until(2)
            self.play(FadeOut(VGroup(circ, sub, tags, bar_c, lab_c, val_c, bar_e, lab_e, val_e)), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(k, shift=0.08 * UP) for k in kinds], lag_ratio=0.25), run_time=1.0)
            v.until(2, 0.45)
            self.play(LaggedStart(*[FadeIn(r, shift=0.08 * RIGHT) for r in table], lag_ratio=0.35), run_time=1.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def solve(self):
        head = header(5, "Solve")
        circ = circuit().scale(0.9).move_to([0.3, 1.2, 0])
        sim = T("Aer statevector simulator · every amplitude read exactly", 21, QPU, weight=MEDIUM).next_to(circ, UP, buff=0.2).align_to(circ, LEFT)
        ys = circ.ys
        keep = VGroup(*[M("0", 0.7, NW).next_to(m, RIGHT, buff=0.2) for m in circ[6]])
        success = VGroup(T("success probability", 21, MUTED), T(f"{PLATE['success']:.2f}", 30, NW, weight=MEDIUM)).arrange(DOWN, buff=0.06)
        success.next_to(circ, DOWN, buff=0.45).align_to(circ, RIGHT)
        restore = VGroup(T("physical scale restored", 21, NW),
                         M("x = (norm(b) kappa s) / alpha dot psi_\"success\"", 0.95, NW)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        restore.next_to(circ, DOWN, buff=0.45).align_to(circ, LEFT)

        qls_map = plate_map(PLATE["x"], cell=0.78).move_to([-4.6, -0.2, 0])
        ref_map = plate_map(PLATE["reference"], cell=0.78).move_to([-0.7, -0.2, 0])
        qls_lab = T(f"QLS, {PLATE['qubits']} qubits", 23, NW, weight=MEDIUM).next_to(qls_map, UP, buff=0.22)
        ref_lab = T("NumPy direct solve", 23, REF, weight=MEDIUM).next_to(ref_map, UP, buff=0.22)
        cbar = color_bar().next_to(ref_map, RIGHT, buff=0.4)
        cbar_lab = T("temperature above the edges", 17, MUTED).rotate(PI / 2).next_to(cbar, RIGHT, buff=0.12)
        stats = VGroup(
            VGroup(T("relative error", 21, MUTED), T(f"{100 * PLATE['relative_error']:.2f} %", 32, NW, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(T("allowance of the polynomial", 21, MUTED), T(f"{100 * PLATE['method_allowance']:.0f} %", 32, INK, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([5.0, 0.3, 0])
        shots = VGroup(T("with finite shots,", 20, QPU), T("as on hardware:", 20, QPU),
                       VGroup(M("x^dagger O x", 0.9, QPU), T("and other quantities", 20, QPU)).arrange(RIGHT, buff=0.2)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        shots.next_to(stats, DOWN, buff=0.5).align_to(stats, LEFT)
        assert shots.get_right()[0] < 6.95
        record = VGroup(C("result.verify(...)", 20, NW), C("result.save(path)", 20, NW), C("load_result(path)", 20, NW)).arrange(RIGHT, buff=0.7)
        record.move_to([0, -3.15, 0])

        with self.voice("solve") as v:
            self.play(FadeIn(head), FadeIn(circ), FadeIn(sim), run_time=0.9)
            top, bot = ys[0] + 0.2, ys[-1] - 0.2
            sweep = Rectangle(width=0.35, height=(top - bot) * 0.9, stroke_width=0, fill_color=QPU, fill_opacity=0.18)
            sweep.move_to([circ[0].get_left()[0] + 0.2, circ[0].get_center()[1], 0])
            self.play(FadeIn(sweep), run_time=0.3)
            self.play(sweep.animate.move_to([circ[0].get_right()[0] - 0.2, circ[0].get_center()[1], 0]), run_time=2.2, rate_func=linear)
            self.play(FadeOut(sweep), *[m.animate.set_color(NW) for m in circ[6]], FadeIn(keep), run_time=0.7)
            v.until(0, 0.6)
            self.play(FadeIn(success, shift=0.1 * UP), run_time=0.7)
            v.until(0, 0.82)
            self.play(FadeIn(restore, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            self.play(FadeOut(VGroup(circ, sim, keep, success, restore)), run_time=0.5)
            blank = plate_map(cell=0.78).move_to(qls_map)
            self.play(FadeIn(blank), FadeIn(qls_lab), run_time=0.4)
            self.play(LaggedStart(*[Transform(b, q) for b, q in zip(blank[1], qls_map[1])], lag_ratio=0.06),
                      Transform(blank[0], qls_map[0]), run_time=1.6)
            self.play(FadeIn(ref_map), FadeIn(ref_lab), FadeIn(cbar), FadeIn(cbar_lab), run_time=0.9)
            v.until(1, 0.45)
            self.play(FadeIn(stats[0], shift=0.1 * UP), run_time=0.7)
            v.until(1, 0.7)
            self.play(FadeIn(stats[1], shift=0.1 * UP), run_time=0.7)
            v.until(2)
            self.play(FadeIn(shots, shift=0.1 * UP), run_time=0.8)
            v.until(3)
            self.play(LaggedStart(*[FadeIn(r, shift=0.08 * UP) for r in record], lag_ratio=0.3), run_time=1.2)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def scale(self):
        head = header(6, "Beyond simulation")
        n = 44
        ring = VGroup(*[Dot([1.55 * np.cos(t), 1.55 * np.sin(t), 0], radius=0.06, color=INK)
                        for t in np.linspace(PI / 2 + 0.35, PI / 2 + 2 * PI - 0.35, n)])
        gap_dots = T("⋯", 30, MUTED).move_to([0, 1.55, 0])
        ring_c = Circle(1.55, color=LINE, stroke_width=2)
        ring_g = VGroup(ring_c, ring, gap_dots).move_to([-4.6, 0.45, 0])
        sites = M("2^(100) \" sites\"", 1.0).move_to(ring_g)
        compact = VGroup(M("A = I + (2 I - S - S^dagger) slash 4", 0.85),
                         T("S shifts the ring by one site", 17, MUTED),
                         M("b = (c_0, s_0) times.o (c_1, s_1) times.o dots", 0.8),
                         T("a product of one-qubit states", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        compact.next_to(ring_g, DOWN, buff=0.35)
        store = T("stored in a form that grows at most linearly with q", 19, NW).next_to(compact, DOWN, buff=0.22).align_to(compact, LEFT)
        if store.get_left()[0] < -6.9:
            store.shift((-6.9 - store.get_left()[0]) * LEFT)

        planned = SCALE["planned"]
        ax = Axes(x_range=[0, 100, 20], y_range=[2.5, 6, 1], x_length=7.4, y_length=4.9, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([2.6, -0.15, 0])
        xt = VGroup(*[T(str(x), 17, MUTED).next_to(ax.c2p(x, 2.5), DOWN, buff=0.12) for x in (0, 20, 40, 60, 80, 100)])
        yt = VGroup(*[M(f"10^({e})", 0.7, MUTED).next_to(ax.c2p(0, e), LEFT, buff=0.12) for e in (3, 4, 5, 6)])
        grid = VGroup(*[DashedLine(ax.c2p(0, e), ax.c2p(100, e), color=LINE, stroke_width=1.2, dash_length=0.06) for e in (3, 4, 5, 6)])
        xl = T("system qubits q", 18, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = T("CX gates per attempt, predicted", 18, NW).next_to(ax.y_axis, UP, buff=0.15).align_to(ax.y_axis, LEFT)
        pts = [ax.c2p(r["q"], np.log10(r["cx"])) for r in planned]
        path = VMobject(stroke_color=NW, stroke_width=3).set_points_as_corners(pts)
        dots = VGroup(*[Dot(p, radius=0.065, color=NW) for p in pts])
        last = planned[-1]
        end = Dot(pts[-1], radius=0.11, color=NW)
        note = VGroup(T(f"{last['cx']:,.0f} CX", 26, NW, weight=MEDIUM),
                      T(f"{last['qubits']} qubits · degree {last['degree']}", 19, NW),
                      T(f"banded encoding, κ = {last['kappa']:g}", 19, NW),
                      T(f"plan + estimate: {last['seconds']:.2f} s", 19, MUTED),
                      T(f"on an {DATA['machine']} laptop", 15, MUTED)).arrange(DOWN, aligned_edge=RIGHT, buff=0.07)
        note.arrange(DOWN, aligned_edge=LEFT, buff=0.07).move_to(ax.c2p(3, 5.95), aligned_edge=UL)
        leader = DashedLine(note[0].get_right() + 0.15 * RIGHT, end.get_center() + 0.15 * LEFT, color=NW, stroke_width=2, dash_length=0.08)

        compiled = SCALE["compiled"]
        squares = VGroup(*[Square(0.2, stroke_color=QPU, stroke_width=3).move_to(ax.c2p(r["q"], np.log10(r["compiled"]))) for r in compiled])
        sq_lab = VGroup(Square(0.2, stroke_color=QPU, stroke_width=3), T("compiled by Qiskit, no optimization", 18, QPU)).arrange(RIGHT, buff=0.15)
        sq_lab.move_to(ax.c2p(100, 2.5), aligned_edge=DR).shift(0.1 * UP)
        rows = VGroup(*[VGroup(T(f"q = {r['q']}", 20, INK), T(f"{r['law']:,.0f}", 20, NW, weight=MEDIUM),
                               T(f"{r['compiled']:,}", 20, QPU, weight=MEDIUM)) for r in compiled])
        heads = VGroup(T("", 18, MUTED), T("predicted", 18, NW), T("compiled", 18, QPU))
        tab = VGroup(heads, *rows)
        for k, r in enumerate(tab):
            for part, x in zip(r, (-6.5, -3.9, -2.2)):
                part.move_to([x, 1.8 - 0.5 * k, 0], aligned_edge=RIGHT if x > -6 else LEFT)
        mem = VGroup(T("state vector on 104 qubits:", 20, MUTED), M("approx 3 times 10^(32) \" bytes\"", 0.95, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        mem.move_to([-4.7, -1.75, 0])
        logical = VGroup(T("logical counts:", 19, MUTED), T("no noise, no error correction", 19, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        logical.next_to(mem, DOWN, buff=0.3).align_to(mem, LEFT)

        with self.voice("scale") as v:
            self.play(FadeIn(head), Create(ring_c), LaggedStart(*[FadeIn(d) for d in ring], lag_ratio=0.03), FadeIn(gap_dots), run_time=1.6)
            self.play(FadeIn(sites), run_time=0.5)
            v.until(0, 0.35)
            self.play(LaggedStart(*[FadeIn(c, shift=0.08 * UP) for c in compact], lag_ratio=0.3), run_time=1.6)
            v.until(0, 0.75)
            self.play(FadeIn(store), run_time=0.6)
            v.until(1)
            self.play(Create(ax), FadeIn(grid), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=1.0)
            self.play(Create(path), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.15), run_time=3.0, rate_func=linear)
            self.play(GrowFromCenter(end), run_time=0.4)
            v.until(2)
            self.play(Create(leader), LaggedStart(*[FadeIn(t, shift=0.06 * UP) for t in note[:3]], lag_ratio=0.3), run_time=1.2)
            v.until(2, 0.55)
            self.play(FadeIn(note[3:]), run_time=0.6)
            v.until(3)
            self.play(FadeOut(VGroup(ring_g, sites, compact, store)), run_time=0.5)
            self.play(LaggedStart(*[Create(s) for s in squares], lag_ratio=0.2), FadeIn(sq_lab), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(r, shift=0.06 * RIGHT) for r in tab], lag_ratio=0.15), run_time=1.4)
            v.until(4)
            self.play(FadeIn(mem, shift=0.1 * UP), run_time=0.8)
            v.until(4, 0.55)
            self.play(FadeIn(logical), run_time=0.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def methods(self):
        head = header(7, "Methods")

        def card(problem, eq, methods, notebooks, color=LINE):
            frame = RoundedRectangle(corner_radius=0.12, width=4.45, height=2.62, stroke_color=color,
                                     stroke_width=3 if color != LINE else 2, fill_color=PAPER, fill_opacity=1)
            parts = [T(problem, 22, INK, weight=MEDIUM), M(eq, 0.85)]
            parts += [T(m, 19, NW, weight=MEDIUM) for m in methods]
            parts += [C(nb, 14, MUTED) for nb in notebooks]
            body = VGroup(*parts).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            body.move_to(frame).align_to(frame, LEFT).shift(0.24 * RIGHT)
            assert body.get_right()[0] < frame.get_right()[0] - 0.08, problem
            return VGroup(frame, body)

        cards = VGroup(
            card("Linear systems", "A x = b", ["QLS: QSVT inverse polynomial,", "Dalzell's shortcut"],
                 ["qls_linear_system_intro", "qls_scientific"], NW),
            card("Linear differential equations", "(dif u) / (dif t) = -A u + b", ["LCHS"],
                 ["lchs_linear_dynamics_intro", "lchs_scientific"]),
            card("Eigenvalues", "H v = E v", ["Chebyshev Lanczos,", "fixed and adaptive GCiM"], ["gcim_lanczos_qpe_eigenvalue_intro"]),
            card("Phase estimation", "e^(-i H t) arrow E", ["QCELS, RWPE, SPE, RFE"], ["gcim_lanczos_qpe_eigenvalue_intro"]),
            card("Optimization over a box", "min_(x in \"box\") f(x)", ["Quantum Hamiltonian descent,", "augmented Lagrangian"],
                 ["qhd_optimization_intro", "qhd_scientific"]),
            card("Expectation values", "chevron.l psi | O | psi chevron.r", ["Pauli-sum observables"], []),
        )
        cards.arrange_in_grid(rows=2, cols=3, buff=(0.3, 0.3)).move_to([0, -0.35, 0])
        scale_nb = VGroup(C("resource_estimation_at_scale", 17, NW), T("plans five method families at up to 100 qubits", 19, MUTED)).arrange(RIGHT, buff=0.3)
        scale_nb.move_to([0, -3.35, 0])

        with self.voice("methods") as v:
            self.play(FadeIn(head), run_time=0.6)
            v.until(0, 0.26)
            self.play(FadeIn(cards[0], shift=0.1 * UP), run_time=0.8)
            v.until(0, 0.62)
            self.play(FadeIn(cards[1], shift=0.1 * UP), run_time=0.8)
            v.until(1, 0.1)
            self.play(FadeIn(cards[2], shift=0.1 * UP), run_time=0.8)
            v.until(1, 0.62)
            self.play(FadeIn(cards[3], shift=0.1 * UP), run_time=0.8)
            v.until(2)
            self.play(FadeIn(cards[4], shift=0.1 * UP), run_time=0.8)
            v.until(2, 0.58)
            self.play(FadeIn(cards[5], shift=0.1 * UP), run_time=0.8)
            v.until(3)
            notebooks = [m for c in cards for m in c[1] if isinstance(m, Text) and m.font == "Menlo"]
            self.play(*[Indicate(m, color=NW, scale_factor=1.06) for m in notebooks], run_time=1.0)
            v.until(3, 0.48)
            self.play(FadeIn(scale_nb, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def get(self):
        head = header(8, "Run and install")
        local = VGroup(*[box(n_, sub, QPU, width=2.4, size=24, sub_size=18) for n_, sub in (("Aer", "simulator"), ("NWQ-Sim", "CPU simulator"))]).arrange(RIGHT, buff=0.3)
        remote = VGroup(*[box(n_, "offline checks", MUTED, width=2.4, size=24, sub_size=18, dashed=True)
                          for n_ in ("IBM Runtime", "IonQ", "Quantinuum Nexus")]).arrange(RIGHT, buff=0.3)
        local_l = T("run locally", 21, QPU, weight=MEDIUM).next_to(local, UP, buff=0.2)
        remote_l = T("provider adapters", 21, MUTED, weight=MEDIUM).next_to(remote, UP, buff=0.2)
        backends = VGroup(VGroup(local_l, local), VGroup(remote_l, remote)).arrange(RIGHT, buff=0.8).move_to([0, 1.6, 0])
        live = T("runs on live hardware: not yet qualified", 20, MUTED).next_to(backends[1], DOWN, buff=0.25)

        cmd = code_panel(['python -m pip install "nwqlib[aer]"'], size=26)
        rows = VGroup(*[VGroup(T(a, 22, MUTED), T(b, 24, NW if k < 2 else INK, weight=MEDIUM)) for k, (a, b) in enumerate(
            (("Documentation", "pnnl.github.io/NWQLib"), ("Code and examples", "github.com/pnnl/NWQLib"),
             ("License", "BSD 2-Clause"), ("Cite", "doi.org/10.5281/zenodo.23074265")))])
        for k, r in enumerate(rows):
            r[0].move_to([-6.2, -1.95 - 0.5 * k, 0], aligned_edge=LEFT)
            r[1].move_to([-2.9, -1.95 - 0.5 * k, 0], aligned_edge=LEFT)
        cmd.move_to([0, -0.95, 0]).align_to(rows, LEFT).shift(0.15 * LEFT)

        with self.voice("get") as v:
            self.play(FadeIn(head), FadeIn(backends[0], shift=0.1 * UP), run_time=0.9)
            v.until(0, 0.33)
            self.play(FadeIn(backends[1], shift=0.1 * UP), run_time=0.9)
            v.until(0, 0.8)
            self.play(FadeIn(live), run_time=0.6)
            v.until(1)
            self.play(FadeIn(cmd, shift=0.1 * UP), run_time=0.8)
            v.until(1, 0.45)
            self.play(LaggedStart(*[FadeIn(r, shift=0.08 * RIGHT) for r in rows], lag_ratio=0.25), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("State a scientific problem, see the estimated resources", 34, weight=MEDIUM),
                       T("before any circuit is built, and get the answer", 34, weight=MEDIUM),
                       T("with the evidence behind it.", 34, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cite = VGroup(eyebrow(f"NWQLib {VERSION}"),
                      T("Northwest Quantum Library, Pacific Northwest National Laboratory", 21),
                      T("github.com/pnnl/NWQLib  ·  pnnl.github.io/NWQLib  ·  pip install nwqlib", 21, NW),
                      T("Supported by PNNL's Quantum Algorithms and Architecture for Domain Science (QuAADS) LDRD Initiative", 16, MUTED),
                      T("and by the U.S. Department of Energy, Office of Science, Quantum Science Center", 16, MUTED)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        cite[4].next_to(cite[3], DOWN, buff=0.06, aligned_edge=LEFT)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=NW, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.2)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class NWQLibPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Northwest Quantum Library", size=30).to_corner(UL, buff=0.6)
        # The site draws its play button over the center of the thumbnail, so the center stays empty.
        name = T("NWQLib", 110, NW, weight=MEDIUM).move_to([-6.5, 1.65, 0], aligned_edge=LEFT)
        eq = M("A x = b", 2.4).move_to([-6.4, -1.75, 0], aligned_edge=LEFT)
        plate = plate_map(PLATE["x"], cell=1.2).move_to([4.3, -0.1, 0])
        plate[0].set_stroke(width=9)
        self.add(label, name, eq, plate)
