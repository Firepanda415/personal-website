"""Explainer for NWQLib, the Northwest Quantum Library (Pacific Northwest National Laboratory).

Two worked examples carry the video. The heat-plate solve, its compiled CX count and the ring
planning come from data.json, recomputed with the public NWQLib workflow (see extract_data.py).
The H4 ADAPT-GCIM iterations, circuit count and reanalysis are the stored outputs of
examples/gcim_lanczos_qpe_eigenvalue_intro.ipynb. Report lines quote the report() output of the
two notebooks. The circuit and construction sketches are schematic.
The title and closing cards name release 1.0.0, the version this video announces. The numbers
were computed at the commit recorded in data.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

NW = ACCENT        # NWQLib's own selections, estimates and results
QPU = DV           # qubits, circuits and quantum execution
REF = GOLD         # classical references (numpy, FCI, CCSD)
VERSION = "1.0.0"
DATA = json.loads((Path(__file__).resolve().parent / "data.json").read_text())
PLATE = DATA["plate"]
H4 = DATA["h4"]
HEAT = [PAPER, "#e9cfae", "#c98f6c", NW, "#4b2530"]


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


def box(title, sub=None, color=INK, width=2.6, height=None, size=22, sub_size=17, dashed=False, fill=PAPER):
    parts = [T(title, size, color, weight=MEDIUM)]
    if sub is not None:
        parts.append(sub if isinstance(sub, Mobject) else T(sub, sub_size, MUTED))
    body = VGroup(*parts).arrange(DOWN, buff=0.1)
    h = height or body.height + 0.36
    frame = RoundedRectangle(corner_radius=0.1, width=max(width, body.width + 0.36), height=h, stroke_color=color,
                             stroke_width=2.5, fill_color=fill, fill_opacity=1)
    if dashed:
        frame = DashedVMobject(frame, num_dashes=40)
    return VGroup(frame, body.move_to(frame))


def arrow(a, b, color=MUTED, buff=0.1, width=3):
    return Arrow(a, b, buff=buff, color=color, stroke_width=width, max_tip_length_to_length_ratio=0.12, tip_length=0.18)


def plate_map(values, cell=0.62):
    """4 x 4 temperature map, grid row 0 at the bottom as in the notebook's imshow(origin='lower')."""
    g = PLATE["grid"]
    vmax = max(PLATE["reference"])
    cells = VGroup()
    for r in range(g):
        for c in range(g):
            sq = Square(cell, stroke_color=PAPER, stroke_width=1.5, fill_color=heat(values[r * g + c] / vmax), fill_opacity=1)
            cells.add(sq.move_to([(c - 1.5) * cell, (r - 1.5) * cell, 0]))
    edge = Square(g * cell + 0.16, stroke_color=QPU, stroke_width=5)
    return VGroup(edge, cells)


def color_bar(height=2.4, width=0.22):
    n = 40
    bar = VGroup(*[Rectangle(width=width, height=height / n, stroke_width=0, fill_color=heat(i / (n - 1)), fill_opacity=1)
                   .move_to([0, -height / 2 + (i + 0.5) * height / n, 0]) for i in range(n)])
    vmax = max(PLATE["reference"])
    ticks = VGroup(T("0", 15, MUTED).next_to(bar, RIGHT, buff=0.1).align_to(bar, DOWN),
                   T(f"{vmax:.3f}", 15, MUTED).next_to(bar, RIGHT, buff=0.1).align_to(bar, UP))
    return VGroup(bar, ticks)


def code_panel(lines, size=18, buff=0.22):
    body = VGroup(*[C(l, size) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    panel = RoundedRectangle(corner_radius=0.12, width=body.width + 0.6, height=body.height + 0.5, stroke_width=0,
                             fill_color=WASH, fill_opacity=1)
    return VGroup(panel, body.move_to(panel))


class NWQLibExplainer(Explainer):
    timing_file = BUILD / "nwqlib" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.problem()
        self.workflow()
        self.plate()
        self.evidence()
        self.gcim()
        self.others()
        self.running()
        self.scope()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        label = eyebrow(f"Scientific software · Release {VERSION}")
        title = VGroup(T("NWQLib", 64, weight=MEDIUM),
                       T("Northwest Quantum Library", 36, MUTED, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        what = T("Quantum algorithms applied to scientific problems", 26)
        authors = VGroup(
            T("Yousu Chen, Karol Kowalski, Ang Li, Xiangyu Li, Chenxu Liu, Johannes Mülmenstädt,", 20, MUTED),
            T("Bo Peng, Zhixin Song, Samuel Stein, Nathan Wiebe, Zeguan Wu, Muqing Zheng", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        places = VGroup(
            T("Pacific Northwest National Laboratory · University of Washington · Georgia Institute of Technology", 17, MUTED),
            T("University of Toronto · University of Pittsburgh", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        block = VGroup(label, title, what, authors, places).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        places.next_to(authors, DOWN, buff=0.18, aligned_edge=LEFT)
        block.move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(block.get_corner(UL) + 0.35 * UP, block.get_corner(UL) + 0.35 * UP + 1.2 * RIGHT, color=NW, stroke_width=4)
        self.play(Create(rule), FadeIn(label, shift=0.1 * RIGHT), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in (title, what, authors, places)], lag_ratio=0.25), run_time=1.8)
        self.wait(2.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 01
    def problem(self):
        head = header(1, "From a paper to an answer")
        mine = box("Your problem", VGroup(M("A x = b", 1.3), T("from a heat, flow or chemistry model", 17, MUTED)).arrange(DOWN, buff=0.15),
                   INK, width=4.6).move_to([-4.3, 2.0, 0])
        paper = box("Algorithm paper", VGroup(
            M("(bra(0^a) ⊗ I) U (ket(0^a) ⊗ I) = A slash alpha", 0.8),
            M("P(x) approx 1 slash (kappa x), quad phi_0, dots, phi_d", 0.8),
            T("probability that the circuit succeeds", 17, MUTED)).arrange(DOWN, buff=0.14), QPU, width=6.2).move_to([3.5, 2.0, 0])

        steps = ["choose block encoding", "bound condition number κ", "fit polynomial", "compute phase angles",
                 "build and run circuit", "keep successful outcomes", "restore scale and phase of x"]
        boxes = VGroup(*[box(f"{k + 1}  {s}", None, INK, width=2.0, height=0.72, size=18) for k, s in enumerate(steps)])
        boxes[:4].arrange(RIGHT, buff=0.42).move_to([0, -0.55, 0])
        boxes[4:].arrange(RIGHT, buff=0.42).move_to([0, -1.85, 0])
        links = VGroup(*[arrow(boxes[k].get_right(), boxes[k + 1].get_left(), buff=0.05) for k in (0, 1, 2, 4, 5)])
        turn = VMobject(stroke_color=MUTED, stroke_width=3).set_points_as_corners([
            boxes[3].get_right() + 0.05 * RIGHT, [boxes[3].get_right()[0] + 0.3, boxes[3].get_y(), 0],
            [boxes[3].get_right()[0] + 0.3, -1.2, 0], [boxes[4].get_left()[0] - 0.3, -1.2, 0],
            [boxes[4].get_left()[0] - 0.3, boxes[4].get_y(), 0]])
        turn = VGroup(turn, arrow([boxes[4].get_left()[0] - 0.32, boxes[4].get_y(), 0], boxes[4].get_left(), buff=0.03))

        scale_note = DashedVMobject(SurroundingRectangle(boxes[6], color=NW, buff=0.1, corner_radius=0.12), num_dashes=40)
        scale_lab = T("PennyLane and CUDA-Q examples: in the example code", 16, NW).next_to(scale_note, DOWN, buff=0.12).align_to(scale_note, RIGHT)
        qiskit = VGroup(T("Qiskit 2 circuit library:", 18, QPU, weight=MEDIUM),
                        T("no block encoding, QSVT or LCHS", 18, INK)).arrange(RIGHT, buff=0.15)
        qiskit.move_to([0, -3.55, 0]).to_edge(LEFT, buff=0.9)

        with self.voice("problem") as v:
            self.play(FadeIn(head), FadeIn(mine, shift=0.15 * RIGHT), run_time=1.0)
            v.until(1)
            self.play(FadeIn(paper, shift=0.15 * LEFT), run_time=1.0)
            v.until(2)
            order = [boxes[0], links[0], boxes[1], links[1], boxes[2], links[2], boxes[3], turn, boxes[4], links[3], boxes[5], links[4], boxes[6]]
            self.play(LaggedStart(*[FadeIn(m, shift=0.08 * RIGHT) for m in order], lag_ratio=0.35), run_time=min(v.dur(2) * 0.8, 7))
            v.until(3)
            self.play(Create(scale_note), FadeIn(scale_lab), run_time=1.0)
            v.until(3, 0.62)
            self.play(FadeIn(qiskit, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def workflow(self):
        head = header(2, "One workflow")
        name = VGroup(T("NWQLib", 30, NW, weight=MEDIUM), T("Northwest Quantum Library", 22, MUTED),
                      T("·  builds Qiskit circuits", 20, QPU)).arrange(RIGHT, buff=0.3)
        name.next_to(head, DOWN, buff=0.3, aligned_edge=LEFT)

        code = code_panel(["problem = LinearSystem(A=A, b=b)", "method = QLS(epsilon_inv=0.01)",
                           "selected = plan(problem, method=method)", "cost = estimate(selected)", "result = solve(selected)",
                           "result.verify(...)", "result.save(path)", "load_result(path).analyze(...)"], size=19, buff=0.24)
        lines = code[1]
        lines[2:].shift(0.18 * DOWN)
        lines[5:].shift(0.18 * DOWN)
        code[0].stretch_to_fit_height(lines.height + 0.6).move_to(lines)
        code.move_to([-3.7, -0.75, 0])

        problem = box("Problem", "A and b", INK, width=2.3).move_to([1.6, 1.6, 0])
        method = box("Method", "QLS, ε = 0.01", INK, width=2.3).move_to([5.3, 1.6, 0])
        plan_b = box("Plan", "encoding, polynomial, phases", NW, width=3.4).move_to([3.45, 0.05, 0])
        cost_b = box("Cost", "resource estimate", NW, width=2.3).move_to([5.6, -1.55, 0])
        result = box("Result", "x, data, evidence", NW, width=2.5).move_to([1.6, -1.55, 0])
        after = VGroup(*[box(s, None, INK, width=1.55, height=0.62, size=17) for s in ("verify", "save", "reanalyze")])
        after.arrange(RIGHT, buff=0.18).move_to([2.0, -3.2, 0])
        a_plan = VGroup(arrow(problem.get_bottom(), plan_b.get_top() + 0.35 * LEFT), arrow(method.get_bottom(), plan_b.get_top() + 0.35 * RIGHT))
        a_cost = arrow(plan_b.get_bottom() + 0.9 * RIGHT, cost_b.get_top())
        a_solve = arrow(plan_b.get_bottom() + 0.9 * LEFT, result.get_top())
        a_after = VGroup(*[arrow(result.get_bottom(), b.get_top(), buff=0.06) for b in after])
        lab_plan = C("plan", 17, NW).next_to(plan_b, UP, buff=0.12)
        lab_cost = C("estimate", 17, NW).next_to(a_cost, RIGHT, buff=0.1)
        lab_solve = C("solve", 17, NW).next_to(a_solve, LEFT, buff=0.1)
        same = DashedVMobject(SurroundingRectangle(VGroup(result, after), color=NW, buff=0.15, corner_radius=0.15), num_dashes=60)
        same_lab = T("one record", 17, NW).next_to(same, RIGHT, buff=0.12).align_to(same, DOWN)

        with self.voice("workflow") as v:
            self.play(FadeIn(head), FadeIn(name, shift=0.1 * RIGHT), run_time=1.0)
            v.until(1)
            self.play(FadeIn(code[0]), FadeIn(lines[:2]), FadeIn(problem), FadeIn(method), run_time=1.0)
            v.until(1, 0.3)
            self.play(FadeIn(lines[2]), GrowArrow(a_plan[0]), GrowArrow(a_plan[1]), FadeIn(lab_plan), FadeIn(plan_b), run_time=1.0)
            v.until(1, 0.55)
            self.play(FadeIn(lines[3]), GrowArrow(a_cost), FadeIn(lab_cost), FadeIn(cost_b), run_time=1.0)
            v.until(1, 0.75)
            self.play(FadeIn(lines[4]), GrowArrow(a_solve), FadeIn(lab_solve), FadeIn(result), run_time=1.0)
            v.until(2)
            self.play(FadeIn(lines[5:]), *[GrowArrow(a) for a in a_after], FadeIn(after), run_time=1.2)
            self.play(Create(same), FadeIn(same_lab), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def plate(self):
        head = header(3, "Example 1 · Heat in a plate")
        g = PLATE["grid"]
        blank = plate_map([0.0] * g * g, cell=0.7).move_to([-4.2, 0.1, 0])
        heaters = VGroup(*[Dot(blank[1][r * g + c].get_center(), radius=0.1 + 0.08 * p, color=NW) for r, c, p in PLATE["heaters"]])
        heat_lab = T("two heaters", 18, NW).next_to(blank, UP, buff=0.18)
        edge_lab = T("edges held cold, u = 0", 18, QPU).next_to(blank, DOWN, buff=0.18)
        grid_lab = T("4 × 4 interior grid → 16 unknowns", 18, MUTED).next_to(edge_lab, DOWN, buff=0.1)

        chain = 2 * np.eye(g) - np.eye(g, k=1) - np.eye(g, k=-1)
        A = np.kron(chain, np.eye(g)) + np.kron(np.eye(g), chain)
        dots = VGroup(*[Dot([0.19 * j, -0.19 * i, 0], radius=0.055 if A[i, j] else 0.02, color=INK if A[i, j] else LINE)
                        for i in range(16) for j in range(16)]).move_to([3.4, 0.5, 0])
        a_lab = VGroup(M("A x = b", 1.1), T(f"A: 16 × 16, {np.count_nonzero(A)} nonzeros, five-point Laplacian", 17, MUTED)).arrange(DOWN, buff=0.12).next_to(dots, DOWN, buff=0.3)

        def row(key, value, color=NW):
            return VGroup(T(key, 18, MUTED), value if isinstance(value, Mobject) else T(value, 20, color, weight=MEDIUM)).arrange(RIGHT, buff=0.25)
        chosen = VGroup(
            eyebrow("plan selected", NW, 15),
            row("block encoding", f"Pauli, α = {PLATE['alpha']:g}"),
            row("encoded condition number", M(f"kappa = alpha slash sigma_min (A) = {PLATE['kappa']:.1f}", 0.8, NW)),
            row("polynomial", f"odd, degree {PLATE['degree']}, ε = 0.01"),
            row("phase angles", "computed"),
            row("circuit", f"{PLATE['qubits']} qubits = {PLATE['system_qubits']} system + {PLATE['qubits'] - PLATE['system_qubits']} ancilla"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.3, 1.6, 0])

        # schematic circuit: 5 ancilla wires above 4 system wires
        x0, x1 = 0.3, 6.9
        ys = [-1.15 - 0.26 * k for k in range(9)]
        wires = VGroup(*[wire(y, x0 + 0.9, x1 - 0.2, QPU if k < 5 else INK, 2) for k, y in enumerate(ys)])
        wlab = VGroup(T("5 ancillas", 15, QPU).next_to([x0 + 0.85, np.mean(ys[:5]), 0], LEFT, buff=0.05),
                      T("4 system", 15, INK).next_to([x0 + 0.85, np.mean(ys[5:]), 0], LEFT, buff=0.05))
        top, bot = ys[0] + 0.15, ys[-1] - 0.15
        prep = box("PREP b", None, INK, width=0.9, height=abs(ys[5] - ys[-1]) + 0.3, size=14).move_to([x0 + 1.45, np.mean(ys[5:]), 0])
        blocks = VGroup()
        for k in range(4):
            xb = x0 + 2.55 + 0.95 * k
            blocks.add(box("U", None, QPU, width=0.55, height=top - bot, size=17).move_to([xb, (top + bot) / 2, 0]))
            blocks.add(box("φ", None, NW, width=0.36, height=0.4, size=15).move_to([xb + 0.46, ys[0], 0]))
        more = T("⋯ 59 queries in total", 15, MUTED).move_to([x0 + 3.2, top + 0.5, 0])
        meters = VGroup(*[meter(QPU).scale(0.38).move_to([x1 - 0.35, y, 0]) for y in ys[:5]])
        circuit = VGroup(wires, wlab, prep, blocks, more, meters)
        laws = VGroup(*[T("CX law", 13, NW).next_to(b, DOWN, buff=0.06) for b in (prep, blocks[0], blocks[2], blocks[4], blocks[6])])

        scale = 5.4 / 8000
        bx = 1.0
        bar_e = Rectangle(width=PLATE["cx_estimate"] * scale, height=0.42, stroke_width=0, fill_color=NW, fill_opacity=0.9).move_to([bx, 1.55, 0], aligned_edge=LEFT)
        bar_c = Rectangle(width=PLATE["cx_compiled"] * scale, height=0.42, stroke_width=0, fill_color=QPU, fill_opacity=0.9).move_to([bx, 0.35, 0], aligned_edge=LEFT)
        lab_e = T("estimate: resource laws, no circuit built", 17, NW).next_to(bar_e, UP, buff=0.1).align_to(bar_e, LEFT)
        lab_c = T("compiled circuit: Qiskit, optimization level 1", 17, QPU).next_to(bar_c, UP, buff=0.1).align_to(bar_c, LEFT)
        val_e = T(f"{PLATE['cx_estimate']:,.0f} CX", 20, NW, weight=MEDIUM).next_to(bar_e, RIGHT, buff=0.15)
        val_c = T(f"{PLATE['cx_compiled']:,} CX", 20, QPU, weight=MEDIUM).next_to(bar_c, RIGHT, buff=0.15)
        bars = VGroup(bar_e, bar_c, lab_e, lab_c, val_e, val_c)

        sim = T("Aer statevector simulator", 17, QPU, weight=MEDIUM).next_to(wires, DOWN, buff=0.35).align_to(wires, LEFT)
        keep = T("keep: ancillas = 0…0", 17, QPU).next_to(meters, UP, buff=0.12).align_to(meters, RIGHT)
        restore = VGroup(T("scale restored:", 16, NW), M("x = norm(x) dot hat(x)", 0.8, NW)).arrange(RIGHT, buff=0.15).next_to(sim, RIGHT, buff=0.5)

        qls_map = plate_map(PLATE["x"], cell=0.62).move_to([-4.0, 0.3, 0])
        ref_map = plate_map(PLATE["reference"], cell=0.62).move_to([0.0, 0.3, 0])
        qls_lab = T(f"QLS, {PLATE['qubits']} qubits", 20, NW, weight=MEDIUM).next_to(qls_map, UP, buff=0.2)
        ref_lab = T("numpy.linalg.solve", 20, REF, weight=MEDIUM).next_to(ref_map, UP, buff=0.2)
        cbar = color_bar().next_to(ref_map, RIGHT, buff=0.35)
        cbar_lab = T("temperature above edge", 15, MUTED).rotate(PI / 2).next_to(cbar, RIGHT, buff=0.1)
        stats = VGroup(
            VGroup(T("relative error", 19, MUTED), T(f"{100 * PLATE['relative_error']:.2f} %", 26, NW, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(T("success probability per shot", 19, MUTED), T(f"{PLATE['success']:.2f}", 26, NW, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(C("result.x", 18, MUTED), T("physical temperatures,", 19, INK), T("not a unit vector", 19, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([5.6, 0.4, 0])
        readout = VGroup(T("all 16 amplitudes: simulator readout only", 19, MUTED),
                         VGroup(T("on hardware: request a quantity such as", 19, INK), M("x^T A x", 0.85, NW), T("from shots", 19, INK)).arrange(RIGHT, buff=0.15)
                         ).arrange(DOWN, buff=0.12).move_to([0, -2.9, 0])

        with self.voice("plate") as v:
            self.play(FadeIn(head), FadeIn(blank), FadeIn(edge_lab), run_time=1.0)
            self.play(LaggedStart(*[GrowFromCenter(h) for h in heaters], lag_ratio=0.4), FadeIn(heat_lab), run_time=1.0)
            v.until(0, 0.5)
            self.play(FadeIn(grid_lab), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.004), FadeIn(a_lab), run_time=2.0)
            v.until(1)
            self.play(FadeOut(dots), FadeOut(a_lab), run_time=0.5)
            self.play(FadeIn(chosen[0]), FadeIn(chosen[1]), run_time=0.7)
            v.until(1, 0.35)
            self.play(FadeIn(chosen[2]), run_time=0.7)
            v.until(1, 0.62)
            self.play(FadeIn(chosen[3]), run_time=0.6)
            v.until(2)
            self.play(FadeIn(chosen[4]), run_time=0.5)
            v.until(2, 0.4)
            self.play(FadeIn(chosen[5]), Create(wires), FadeIn(wlab), FadeIn(prep), FadeIn(blocks), FadeIn(more), FadeIn(meters), run_time=1.2)
            v.until(3)
            self.play(FadeOut(chosen), LaggedStart(*[FadeIn(l, shift=0.05 * UP) for l in laws], lag_ratio=0.2), run_time=1.0)
            self.play(GrowFromEdge(bar_e, LEFT), FadeIn(lab_e), FadeIn(val_e), run_time=1.0)
            v.until(3, 0.7)
            self.play(GrowFromEdge(bar_c, LEFT), FadeIn(lab_c), FadeIn(val_c), run_time=1.0)
            v.until(4)
            self.play(FadeOut(bars), FadeOut(laws), run_time=0.5)
            sweep = Rectangle(width=0.3, height=top - bot + 0.2, stroke_width=0, fill_color=QPU, fill_opacity=0.18).move_to([x0 + 1.0, (top + bot) / 2, 0])
            self.play(FadeIn(sim), FadeIn(sweep), run_time=0.5)
            self.play(sweep.animate.move_to([x1 - 0.35, (top + bot) / 2, 0]), run_time=2.0, rate_func=linear)
            self.play(FadeOut(sweep), FadeIn(keep), *[m.animate.set_color(NW) for m in meters], run_time=0.8)
            self.play(FadeIn(restore), run_time=0.7)
            v.until(5)
            self.play(FadeOut(VGroup(circuit, sim, keep, restore, heaters, heat_lab, edge_lab, grid_lab)), run_time=0.6)
            self.play(ReplacementTransform(blank, qls_map), FadeIn(qls_lab), run_time=1.2)
            self.play(FadeIn(ref_map), FadeIn(ref_lab), FadeIn(cbar), FadeIn(cbar_lab), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(s, shift=0.1 * UP) for s in stats], lag_ratio=0.5), run_time=2.0)
            v.until(6)
            self.play(FadeIn(readout, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def evidence(self):
        head = header(4, "Example 1 · Cost and evidence")
        t_head = T("estimate of the plate construction", 17, MUTED)
        known = [("qubits", "9", "exact"), ("CX gates", f"{PLATE['cx_estimate']:,.0f}", "estimate"), ("block invocations", "364", "exact")]
        unknown = ["circuit depth", "single-qubit gates", "T gates"]
        table = VGroup(*[VGroup(T(a, 19, INK), T(b, 19, NW, weight=MEDIUM), T(c, 17, MUTED)) for a, b, c in known],
                       *[VGroup(T(a, 19, INK), T("unknown", 19, MUTED, weight=MEDIUM), T("not zero", 17, NW)) for a in unknown])
        for k, r in enumerate(table):
            y = 1.9 - 0.52 * k - (0.22 if k >= len(known) else 0)
            for part, x in zip(r, (-5.4, -2.3, -0.6)):
                part.move_to([x, y, 0], aligned_edge=LEFT)
        t_head.next_to(table, UP, buff=0.3).align_to(table, LEFT)
        split = Line([-5.4, table[3].get_top()[1] + 0.13, 0], [0.6, table[3].get_top()[1] + 0.13, 0], color=LINE, stroke_width=2)
        est = VGroup(t_head, table, split)

        ring = VGroup(*[Dot([np.cos(t), np.sin(t), 0], radius=0.05, color=INK) for t in np.linspace(0, 2 * PI, 24, endpoint=False)])
        ring.add(Circle(0.8, color=MUTED, stroke_width=2).move_to(ORIGIN))
        ring[:-1].scale(0.8)
        ring.move_to([2.6, 1.3, 0])
        heads = ["unknowns", "qubits", "CX, estimate"]
        xs = [4.2, 5.6, 6.7]
        rows = VGroup()
        hrow = VGroup(*[T(h, 16, MUTED).move_to([x, 2.25, 0]) for h, x in zip(heads, xs)])
        for k, r in enumerate(DATA["ring"]):
            color = NW if r["q"] == 40 else INK
            cells = [M(f"2^({r['q']})", 0.75, color), T(str(r["qubits"]), 19, color), T(f"{r['cx']:,.0f}", 19, color)]
            rows.add(VGroup(*[c.move_to([x, 1.6 - 0.55 * k, 0]) for c, x in zip(cells, xs)]))
        ring_lab = VGroup(T("periodic stencil, product-state b", 16, MUTED), T("planned and estimated, nothing solved", 16, NW)).arrange(DOWN, buff=0.06)
        ring_lab.next_to(VGroup(ring, rows), DOWN, buff=0.3)
        planning = VGroup(ring, hrow, rows, ring_lab)

        report = VGroup(C("QLS solver: qsvt_inverse; selected finite polynomial model", 15, INK),
                        C("accuracy not assessed", 15, NW)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        rpanel = RoundedRectangle(corner_radius=0.1, width=report.width + 0.5, height=report.height + 0.8, stroke_width=0, fill_color=WASH, fill_opacity=1)
        rtitle = C("result.report()", 14, MUTED)
        rep = VGroup(rpanel, report.move_to(rpanel).shift(0.15 * DOWN))
        rtitle.move_to(rpanel.get_corner(UL) + [0.2 + rtitle.width / 2, -0.22, 0])
        rep.add(rtitle)
        rep.move_to([0, 2.2, 0])

        total_w, poly_w = 8.0, 3.2
        seg_poly = Rectangle(width=poly_w, height=0.5, stroke_width=0, fill_color=NW, fill_opacity=0.85).move_to([-4.0, 0.0, 0], aligned_edge=LEFT)
        seg_rest = DashedVMobject(Rectangle(width=total_w - poly_w, height=0.5, stroke_color=MUTED, stroke_width=2), num_dashes=26)
        seg_rest.next_to(seg_poly, RIGHT, buff=0)
        lab_poly = T("polynomial", 16, PAPER, weight=MEDIUM).move_to(seg_poly)
        lab_rest = T("other parts of the error", 16, MUTED).move_to(seg_rest)
        poly_val = M(f"abs(kappa x P(x) - 1) <= {PLATE['polynomial_bound']:.4f}", 0.66, NW).next_to(seg_poly, DOWN, buff=0.12).align_to(seg_poly, LEFT)
        brace = Brace(VGroup(seg_poly, seg_rest), UP, color=MUTED, buff=0.08)
        brace_lab = T("total error of x: not bounded by this", 16, MUTED).next_to(brace, UP, buff=0.04)

        track = RoundedRectangle(corner_radius=0.12, width=8.0, height=0.34, stroke_color=LINE, stroke_width=2, fill_color=WASH, fill_opacity=1)
        track.move_to([-4.0, -2.5, 0], aligned_edge=LEFT)
        fill = RoundedRectangle(corner_radius=0.12, width=8.0 * PLATE["relative_error"] / 0.01, height=0.34, stroke_width=0, fill_color=REF, fill_opacity=0.9)
        fill.move_to(track.get_left(), aligned_edge=LEFT)
        end = Line(track.get_right() + 0.28 * UP, track.get_right() + 0.28 * DOWN, color=INK, stroke_width=3)
        g_lab = VGroup(C("result.verify", 15, REF), T("reference solve, on request", 16, REF)).arrange(RIGHT, buff=0.2).next_to(track, UP, buff=0.12).align_to(track, LEFT)
        g_val = T(f"relative error {100 * PLATE['relative_error']:.2f} %", 17, REF, weight=MEDIUM).next_to(track, DOWN, buff=0.1).align_to(track, LEFT)
        g_all = T("allowance 1 %", 17, INK).next_to(end, DOWN, buff=0.04)

        with self.voice("evidence") as v:
            self.play(FadeIn(head), FadeIn(t_head), LaggedStart(*[FadeIn(r) for r in table[:3]], lag_ratio=0.3), run_time=1.2)
            v.until(0, 0.35)
            self.play(Create(split), LaggedStart(*[FadeIn(r, shift=0.05 * RIGHT) for r in table[3:]], lag_ratio=0.3), run_time=1.4)
            v.until(1)
            self.play(FadeIn(ring), FadeIn(hrow), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(r, shift=0.05 * UP) for r in rows], lag_ratio=0.4), run_time=1.4)
            self.play(FadeIn(ring_lab), run_time=0.6)
            v.until(2)
            self.clear_stage(keep=[head], run_time=0.5)
            self.play(FadeIn(rep), run_time=0.8)
            self.play(Indicate(report[1], color=NW, scale_factor=1.05), run_time=0.8)
            v.until(2, 0.4)
            self.play(GrowFromEdge(seg_poly, LEFT), FadeIn(lab_poly), FadeIn(poly_val), run_time=0.9)
            self.play(Create(seg_rest), FadeIn(lab_rest), GrowFromCenter(brace), FadeIn(brace_lab), run_time=1.0)
            v.until(3)
            self.play(FadeIn(track), FadeIn(end), FadeIn(g_lab), FadeIn(g_all), run_time=0.8)
            v.until(3, 0.45)
            self.play(GrowFromEdge(fill, LEFT), FadeIn(g_val), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 05
    def gcim(self):
        head = header(5, "Example 2 · A hydrogen chain")
        name = VGroup(T("ADAPT-GCIM", 34, NW, weight=MEDIUM), T("generator-coordinate-inspired eigensolver", 22, MUTED)).arrange(RIGHT, buff=0.35)
        name.next_to(head, DOWN, buff=0.35, aligned_edge=LEFT)
        only = T("no other package checked in September 2026 implements it  ·  research code from its authors", 17, NW)
        only.next_to(name, DOWN, buff=0.18, aligned_edge=LEFT)

        hf = M("ket(phi_\"HF\")", 1.0).move_to([-5.6, -0.6, 0])
        gens = VGroup(*[M(f"e^(theta A_{k})", 0.85, NW) for k in (1, 2, 3)]).arrange(DOWN, buff=0.35).move_to([-3.3, -0.6, 0])
        g_lab = VGroup(T("excitation with the largest", 16, MUTED), T("energy gradient", 16, MUTED), M("theta = pi slash 4 \"fixed\"", 0.6, MUTED)).arrange(DOWN, buff=0.06).next_to(gens, DOWN, buff=0.25)
        basis = VGroup(*[M(f"ket(psi_{k})", 0.85) for k in range(5)]).arrange(DOWN, buff=0.14).move_to([-0.6, -0.6, 0])
        b_lab = VGroup(T("basis grows by two", 16, MUTED), T("states per iteration", 16, MUTED)).arrange(DOWN, buff=0.04).next_to(basis, DOWN, buff=0.2)
        hs = M("bold(H) c = E bold(S) c", 1.2, NW).move_to([3.6, -0.3, 0])
        hs_lab = VGroup(M("H_(i j) = chevron.l psi_i | H | psi_j chevron.r, quad S_(i j) = chevron.l psi_i | psi_j chevron.r", 0.65, MUTED),
                        T("no angle optimized", 17, NW)).arrange(DOWN, buff=0.12).next_to(hs, DOWN, buff=0.3)
        a1 = arrow(hf.get_right(), gens.get_left())
        a2 = arrow(gens.get_right(), basis.get_left())
        a3 = arrow(basis.get_right(), hs.get_left())

        ax = Axes(x_range=[0, 8, 1], y_range=[-10, 3, 1], x_length=6.2, y_length=4.9, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-2.9, -0.35, 0])
        xt = VGroup(*[T(str(i), 15, MUTED).next_to(ax.c2p(i, -10), DOWN, buff=0.12) for i in range(9)])
        yt = VGroup(*[M(f"10^({e})" if e else "1", 0.58, MUTED).next_to(ax.c2p(0, e), LEFT, buff=0.12) for e in (-9, -6, -3, 0, 3)])
        xl = T("ADAPT-GCIM iteration", 17, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = T("energy error against full CI (mHa)", 17, MUTED).next_to(ax.y_axis, UP, buff=0.15).shift(1.4 * RIGHT)
        errs = [it["error"] for it in H4["iterations"]]
        pts = [ax.c2p(i, np.log10(e)) for i, e in enumerate(errs)]
        corners = [pts[0]]
        for q in pts[1:]:
            corners += [[q[0], corners[-1][1], 0], q]
        stair = VMobject(stroke_color=NW, stroke_width=4).set_points_as_corners(corners)
        dots = VGroup(*[Dot(q, radius=0.07, color=NW) for q in pts])
        refs = VGroup()
        for label, val, color in (("MP2", H4["mp2"], REF), ("CCSD, 18 mHa below", abs(H4["ccsd"]), REF), ("chemical accuracy", 1.6, MUTED)):
            y = np.log10(val)
            line = DashedLine(ax.c2p(0, y), ax.c2p(8, y), color=color, stroke_width=2.5, dash_length=0.1)
            refs.add(VGroup(line, T(label, 15, color).next_to(line, RIGHT, buff=0.12)))
        hf_lab = T("Hartree–Fock", 15, REF).next_to(dots[0], RIGHT, buff=0.1).shift(0.15 * UP)
        last = VGroup(T("1.9", 15, NW), M("times 10^(-10)", 0.55, NW), T("mHa", 15, NW)).arrange(RIGHT, buff=0.06)
        last.next_to(dots[-1], RIGHT, buff=0.15)
        setup = VGroup(T("stretched H4 chain", 19, INK, weight=MEDIUM), T("STO-3G, 8 qubits, 185 Pauli terms", 16, MUTED)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([5.0, 2.3, 0])
        exact = VGroup(T("matrix elements computed exactly", 18, NW, weight=MEDIUM), T("from state vectors, no circuits", 16, MUTED),
                       T("as circuits, exact outcome probabilities:", 16, MUTED),
                       T(f"{H4['circuits']:,} circuits", 19, QPU, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        exact.move_to([5.0, -0.8, 0]).align_to(setup, LEFT)

        rh = VGroup(*[T(h, 15, MUTED) for h in ("overlap cutoff", "kept", "error, mHa")])
        rrows = [rh] + [VGroup(M(f"10^({int(round(np.log10(r['cutoff'])))})", 0.55, INK), T(str(r["kept"]), 16, INK),
                               T("1.9e−10" if r["error"] < 1e-6 else f"{r['error']:g}", 16, NW)) for r in H4["reanalysis"]]
        cx = [3.6, 5.3, 6.2]
        re_tab = VGroup()
        for k, r in enumerate(rrows):
            for part, x in zip(r, cx):
                part.move_to([x, -0.2 - 0.42 * k, 0], aligned_edge=LEFT)
            re_tab.add(r)
        re_lab = VGroup(C("result.analyze(overlap_cutoff=...)", 14, NW), T("stored matrix elements, no new evaluations", 15, MUTED)
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06).next_to(re_tab, UP, buff=0.2).align_to(re_tab, LEFT)
        rep = VGroup(C("processed-input projected estimate;", 13, MUTED), C("ground identity not established", 13, MUTED),
                     T("full CI reference confirms it here", 16, REF)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        rep.next_to(re_tab, DOWN, buff=0.35, aligned_edge=LEFT)
        rep[2].shift(0.08 * DOWN)

        with self.voice("gcim") as v:
            self.play(FadeIn(head), FadeIn(name, shift=0.1 * RIGHT), run_time=1.0)
            v.until(0, 0.35)
            self.play(FadeIn(only), run_time=0.8)
            v.until(1)
            self.play(FadeIn(hf), GrowArrow(a1), LaggedStart(*[FadeIn(gm) for gm in gens], lag_ratio=0.3), FadeIn(g_lab), run_time=1.4)
            self.play(GrowArrow(a2), LaggedStart(*[FadeIn(b) for b in basis], lag_ratio=0.2), FadeIn(b_lab), run_time=1.3)
            v.until(1, 0.55)
            self.play(GrowArrow(a3), FadeIn(hs), FadeIn(hs_lab), run_time=1.0)
            v.until(2)
            self.clear_stage(keep=[head], run_time=0.5)
            self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), FadeIn(refs), FadeIn(setup), run_time=1.1)
            self.play(FadeIn(dots[0]), FadeIn(hf_lab), run_time=0.4)
            self.play(Create(stair), LaggedStart(*[FadeIn(d) for d in dots[1:]], lag_ratio=0.6), run_time=max(v.dur(2) * 0.5, 3))
            self.play(FadeIn(last), run_time=0.5)
            v.until(3)
            self.play(FadeIn(exact[:2]), run_time=0.8)
            v.until(3, 0.45)
            self.play(FadeIn(exact[2:]), run_time=0.8)
            v.until(4)
            self.play(FadeOut(exact), run_time=0.4)
            self.play(FadeIn(re_lab), LaggedStart(*[FadeIn(r) for r in re_tab], lag_ratio=0.25), run_time=1.6)
            v.until(5)
            self.play(FadeIn(rep[:2]), run_time=0.8)
            v.until(5, 0.6)
            self.play(FadeIn(rep[2]), run_time=0.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def others(self):
        head = header(6, "More methods and examples")

        def card(methods, eq, examples, unique=None):
            parts = [VGroup(*[T(m, 20, NW, weight=MEDIUM) for m in methods]).arrange(DOWN, aligned_edge=LEFT, buff=0.06), M(eq, 0.85)]
            parts += [T(e, 16, MUTED) for e in examples]
            if unique:
                parts.append(T(unique, 15, NW))
            body = VGroup(*parts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            frame = RoundedRectangle(corner_radius=0.1, width=4.4, height=2.75, stroke_color=LINE, stroke_width=2, fill_color=PAPER, fill_opacity=1)
            body.move_to(frame).align_to(frame, LEFT).shift(0.25 * RIGHT)
            return VGroup(frame, body)
        cards = VGroup(
            card(["LCHS"], "(dif u)/(dif t) = -A u + b", ["constant A and b", "pulse carried by a flow", "heated rod, ends held cold by a penalty,", "after Schleich, Kharazi, Li et al."]),
            card(["QSVT, Dalzell shortcut"], "A x = b", ["heat in a plate (example 1)", "two-step collision history of a lattice", "Boltzmann fluid model, after Li et al."]),
            card(["Chebyshev Lanczos", "QCELS, SPE, RFE, RWPE"], "H v = E v", ["molecular, spin, lattice Hamiltonians", "initial state must overlap ground state"], "QCELS: not in the other packages checked"),
            card(["Quantum Hamiltonian descent"], "min_(x in \"box\") f(x)", ["a few variables", "a function with two valleys"]),
            card(["Expectation values"], "psi^dagger O psi slash psi^dagger psi", ["observables as Pauli sums"]),
        )
        pos = [[-4.6, 1.35, 0], [0.0, 1.35, 0], [4.6, 1.35, 0], [-2.3, -1.55, 0], [2.3, -1.55, 0]]
        for c, p in zip(cards, pos):
            c.move_to(p)
        nb = T("each example notebook solves a complete problem and shows how to substitute your own", 16, MUTED).move_to([0, -3.35, 0])

        caps = [("QSVT, phase-angle solvers", "PennyLane, pyqsp, QSPPACK"),
                ("block encodings", "PennyLane, Qrisp, CUDA-Q Algorithms, Qualtran"),
                ("LCHS", "Classiq notebook"),
                ("Dalzell shortcut", "Qrisp"),
                ("Chebyshev Lanczos, Krylov methods", "Qrisp, IBM tutorial, CUDA-Q Algorithms"),
                ("quantum Hamiltonian descent", "QHDOPT")]
        ctab = VGroup(*[VGroup(T(a, 19, INK), T(b, 18, MUTED)) for a, b in caps])
        for k, r in enumerate(ctab):
            r[0].move_to([-6.2, 2.3 - 0.52 * k, 0], aligned_edge=LEFT)
            r[1].move_to([-1.3, 2.3 - 0.52 * k, 0], aligned_edge=LEFT)
        c_head = T("also available in other packages, checked September 2026", 17, MUTED).next_to(ctab, UP, buff=0.22).align_to(ctab, LEFT)
        chain = VGroup(*[box(t, None, NW, width=0.5, height=0.62, size=18) for t in ("your inputs", "plan", "cost estimate", "result", "reported evidence")]).arrange(RIGHT, buff=0.45)
        chain_links = VGroup(*[arrow(chain[i].get_right(), chain[i + 1].get_left(), color=NW, buff=0.05) for i in range(4)])
        flow = VGroup(chain, chain_links).move_to([0, -2.4, 0])
        flow_lab = T("NWQLib: the workflow around them", 19, NW, weight=MEDIUM).next_to(flow, UP, buff=0.25)

        with self.voice("others") as v:
            self.play(FadeIn(head), run_time=0.6)
            v.until(0, 0.25)
            self.play(FadeIn(cards[0], shift=0.1 * UP), run_time=1.0)
            v.until(1)
            self.play(FadeIn(cards[1], shift=0.1 * UP), run_time=1.0)
            v.until(2)
            self.play(FadeIn(cards[2], shift=0.1 * UP), run_time=1.0)
            v.until(3)
            self.play(FadeIn(cards[3], shift=0.1 * UP), run_time=0.9)
            v.until(3, 0.55)
            self.play(FadeIn(cards[4], shift=0.1 * UP), FadeIn(nb), run_time=0.9)
            v.until(4)
            self.clear_stage(keep=[head], run_time=0.5)
            self.play(FadeIn(c_head), LaggedStart(*[FadeIn(r) for r in ctab], lag_ratio=0.3), run_time=2.4)
            v.until(4, 0.7)
            self.play(FadeIn(flow_lab), LaggedStart(*[FadeIn(m) for m in [chain[0], chain_links[0], chain[1], chain_links[1], chain[2],
                                                                            chain_links[2], chain[3], chain_links[3], chain[4]]], lag_ratio=0.25), run_time=1.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def running(self):
        head = header(7, "Running circuits")
        local = VGroup(*[box(n, sub, QPU, width=2.2, size=24, sub_size=18) for n, sub in (("Aer", "local"), ("NWQ-Sim", "local, CPU"))]).arrange(RIGHT, buff=0.3)
        remote = VGroup(*[box(n, "offline checks", MUTED, width=2.2, size=24, sub_size=18, dashed=True) for n in ("IBM Runtime", "IonQ", "Quantinuum Nexus")]).arrange(RIGHT, buff=0.3)
        local_l = T("run circuits", 19, QPU, weight=MEDIUM).next_to(local, UP, buff=0.18)
        remote_l = T("provider adapters", 19, MUTED, weight=MEDIUM).next_to(remote, UP, buff=0.18)
        backends = VGroup(VGroup(local_l, local), VGroup(remote_l, remote)).arrange(RIGHT, buff=0.7).move_to([0, 1.9, 0])
        live = T("runs on live hardware have not been qualified", 19, MUTED).next_to(backends[1], DOWN, buff=0.22)

        cols = ["step", "source", "location", "code owner"]
        cx = [-6.7, -3.4, 0.3, 3.5]
        smap = [("Wx to reflection phases", "Martyn et al., arXiv:2105.02859v5", "Eq. (14), App. A.2", "subroutines/qsp/phases.py"),
                ("QSVT sequence", "Gilyén et al., arXiv:1806.01838v1", "Theorem 17, Lemma 19", "subroutines/qsp/evolution.py"),
                ("kernel-reflection polynomial", "Dalzell, arXiv:2406.12086v2", "Eqs. (6), (22)", "subroutines/qsp/shortcut.py")]
        y0 = -0.9
        shead = VGroup(*[T(c, 17, MUTED).move_to([x, y0, 0], aligned_edge=LEFT) for c, x in zip(cols, cx)])
        srows = VGroup(*[VGroup(T(a, 17, INK).move_to([cx[0], y0 - 0.6 - 0.55 * k, 0], aligned_edge=LEFT),
                                T(b, 17, INK).move_to([cx[1], y0 - 0.6 - 0.55 * k, 0], aligned_edge=LEFT),
                                T(c, 17, NW).move_to([cx[2], y0 - 0.6 - 0.55 * k, 0], aligned_edge=LEFT),
                                C(d, 15, MUTED).move_to([cx[3], y0 - 0.6 - 0.55 * k, 0], aligned_edge=LEFT)) for k, (a, b, c, d) in enumerate(smap)])
        srule = Line([cx[0], y0 - 0.28, 0], [6.9, y0 - 0.28, 0], color=LINE, stroke_width=2)
        s_lab = T("source map of the QLS guide, excerpt", 18, NW, weight=MEDIUM).next_to(shead, UP, buff=0.3).align_to(shead, LEFT)

        with self.voice("running") as v:
            self.play(FadeIn(head), FadeIn(backends[0]), run_time=1.0)
            v.until(0, 0.4)
            self.play(FadeIn(backends[1]), run_time=1.0)
            v.until(0, 0.75)
            self.play(FadeIn(live), run_time=0.6)
            v.until(1)
            self.play(FadeIn(s_lab), FadeIn(shead), Create(srule), LaggedStart(*[FadeIn(r) for r in srows], lag_ratio=0.3), run_time=1.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def scope(self):
        head = header(8, "Scope")

        def block(label, color, items):
            return VGroup(eyebrow(label, color, 17), *[T(t, 26, INK) for t in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        now = block("examples", INK, ["at most 12 simulated qubits", "dense matrices for small systems only"])
        needs = VGroup(eyebrow("QLS inputs from you", QPU, 17),
                       VGroup(T("Pauli-sum A:", 26, INK), T("a bound on the condition number", 26, MUTED)).arrange(RIGHT, buff=0.2),
                       VGroup(T("Dalzell shortcut:", 26, INK), T("an estimate of the solution norm", 26, MUTED)).arrange(RIGHT, buff=0.2)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        open_ = block("open work", NW, ["time-dependent LCHS", "error bounds for the physical output of GCIM", "validation on hardware"])
        col = VGroup(now, needs, open_).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0, -0.3, 0]).to_edge(LEFT, buff=1.2)
        with self.voice("scope") as v:
            self.play(FadeIn(head), LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in now], lag_ratio=0.3), run_time=1.4)
            v.until(1)
            self.play(LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in needs], lag_ratio=0.3), run_time=1.4)
            v.until(2)
            self.play(LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in open_], lag_ratio=0.3), run_time=1.4)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("State a scientific problem, get a quantum algorithm's result", 34, weight=MEDIUM),
                       T("with its estimated circuit cost and the evidence behind it.", 34, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        cite = VGroup(eyebrow(f"NWQLib {VERSION}"),
                      T("Northwest Quantum Library, Pacific Northwest National Laboratory", 21),
                      T("Supported by PNNL's Quantum Algorithms and Architecture for Domain Science (QuAADS) LDRD Initiative", 17, MUTED),
                      T("mqzh.science/projects", 21, NW)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
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
        name = T("NWQLib", 110, NW, weight=MEDIUM).move_to([0, 1.3, 0])
        steps = VGroup(*[box(s, None, INK, width=0.5, height=1.0, size=40) for s in ("problem", "plan", "estimate", "solve")]).arrange(RIGHT, buff=0.7)
        links = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.08, color=MUTED, stroke_width=7,
                               max_tip_length_to_length_ratio=0.35) for i in range(3)])
        flow = VGroup(steps, links).move_to([0, -1.6, 0])
        for b in steps:
            b[0].set_stroke(width=4)
        self.add(label, name, flow)
