"""Explainer for "Quantum DeepONet: Neural operators accelerated by quantum computing"
(Xiao, Zheng, Jiao, Yang, Lu, Quantum 9, 1761, 2025).

Quoted values come from Tables 1-4, Sections 2.1-2.4 and 4.3, and Figs. 7-8 of the paper.
The gate order of the pyramid follows W() in src/quantum_layer_ideal.py of
github.com/lu-group/quantum-deeponet. The input functions, the loaded vector, and the pyramid
angles are illustrative values chosen for this video.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import numpy as np
from house_style import *

QUANTUM = DV       # qubits, loaders, amplitudes
METHOD = ACCENT    # the orthogonal pyramid and quantum DeepONet results
CLASSICAL = GOLD   # classical computation and classical DeepONet


# ------------------------------------------------------------------ data
def grf_sample(seed, length=0.2, n=240):
    """Gaussian random field with an RBF kernel on [0, 1] and its antiderivative u(0) = 0."""
    x = np.linspace(0, 1, n)
    k = np.exp(-(x[:, None] - x[None, :]) ** 2 / (2 * length ** 2))
    w, q = np.linalg.eigh(k)
    v = q @ (np.sqrt(np.clip(w, 0, None)) * np.random.default_rng(seed).standard_normal(n))
    v *= 2 / np.abs(v).max()   # common plotting scale; the integral scales with v
    u = np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(x))])
    return x, v, u


SAMPLES = [grf_sample(s) for s in (3, 11, 29)]


def pyramid_columns(n):
    """Pairs (j, j+1) acted on in each column of the n-by-n pyramid, in the order of
    W(n, n, thetas) in the quantum-deeponet code. The k-th pair overall carries theta_k."""
    small = n - 1
    ends = np.concatenate([np.arange(2, n + 1), n + 1 - np.arange(2, small + 1)])
    starts = np.concatenate([np.arange(ends.size + small - n) % 2, np.arange(n - small)])
    return [list(range(s, e - 1, 2)) for s, e in zip(starts, ends)]


X_IN = np.array([0.62, 0.48, -0.36, 0.50])
X_IN = X_IN / np.linalg.norm(X_IN)
THETAS = [0.9, -0.6, 0.5, 1.1, -0.8, 0.4]


def rotate(a, j, t):
    """One RBS gate on the unary amplitudes of neighboring states j and j+1."""
    a = a.copy()
    a[j], a[j + 1] = np.cos(t) * a[j] + np.sin(t) * a[j + 1], -np.sin(t) * a[j] + np.cos(t) * a[j + 1]
    return a


def pyramid_steps(x):
    """Amplitudes after each column of the 4-qubit pyramid."""
    steps, a, k = [], x.copy(), 0
    for col in pyramid_columns(len(x)):
        for j in col:
            a = rotate(a, j, THETAS[k])
            k += 1
        steps.append(a)
    return steps


def loader_steps(x):
    """Amplitudes after each gate of the unary data loader, starting from |10...0>."""
    steps = []
    for k in range(1, len(x)):
        a = np.zeros(len(x))
        a[:k] = x[:k]
        a[k] = np.sqrt(max(1 - np.sum(x[:k] ** 2), 0)) if k < len(x) - 1 else x[k]
        steps.append(a)
    return steps


Y_OUT = pyramid_steps(X_IN)[-1]
PR0 = (Y_OUT + 1 / 2) ** 2 / 4   # ancilla 0, unary state j, with 1/sqrt(n) = 1/2
PR1 = (Y_OUT - 1 / 2) ** 2 / 4   # ancilla 1


# ------------------------------------------------------------------ drawing helpers
def rbs(x, y_top, y_bot, label=None, color=QUANTUM, size=0.62):
    bar = Line([x, y_top, 0], [x, y_bot, 0], color=color, stroke_width=5)
    ends = VGroup(Dot([x, y_top, 0], 0.075, color=color), Dot([x, y_bot, 0], 0.075, color=color))
    g = VGroup(bar, ends)
    if label:
        g.add(M(label, size, color).next_to(bar, RIGHT, buff=0.07))
    return g


def amp_bars(amps, x0, base, gap=1.1, scale=1.5, width=0.5, color=QUANTUM):
    return VGroup(*[Rectangle(width=width, height=max(abs(a) * scale, 1e-3), stroke_width=0, fill_color=color,
                              fill_opacity=0.85).move_to([x0 + i * gap, base + a * scale / 2, 0]) for i, a in enumerate(amps)])


def box(label, width, height, color, fill=0.08, size=20):
    frame = RoundedRectangle(corner_radius=0.1, width=width, height=height, stroke_color=color, stroke_width=2.5,
                             fill_color=color, fill_opacity=fill)
    lab = T(label, size, color) if isinstance(label, str) else label
    return VGroup(frame, lab.move_to(frame))


def arrow(a, b, color=MUTED, buff=0.12):
    return Arrow(a, b, buff=buff, color=color, stroke_width=2.5, tip_length=0.16, max_tip_length_to_length_ratio=0.2)


def cnot(x, y_ctrl, y_tgt, color=INK):
    dot = Dot([x, y_ctrl, 0], 0.08, color=color)
    ring = Circle(0.15, color=color, stroke_width=2.5).move_to([x, y_tgt, 0])
    cross = VGroup(Line([x - 0.15, y_tgt, 0], [x + 0.15, y_tgt, 0], color=color, stroke_width=2.5),
                   Line([x, y_tgt - 0.15, 0], [x, y_tgt + 0.15, 0], color=color, stroke_width=2.5))
    stem = Line([x, y_ctrl, 0], [x, y_tgt + 0.15, 0], color=color, stroke_width=2.5)
    return VGroup(stem, dot, ring, cross)


def network_icon(columns, rows, color=INK, dx=0.32, dy=0.24):
    nodes = [[Dot([c * dx, (r - (rows - 1) / 2) * dy, 0], 0.045, color=color) for r in range(rows)] for c in range(columns)]
    edges = VGroup(*[Line(a.get_center(), b.get_center(), color=LINE, stroke_width=1.2)
                     for c in range(columns - 1) for a in nodes[c] for b in nodes[c + 1]])
    return VGroup(edges, VGroup(*[d for col in nodes for d in col]))


class DeepONetExplainer(Explainer):
    timing_file = BUILD / "deeponet" / "audio" / "timing.json"

    def construct(self):
        self.title_card()
        self.operator()
        self.deeponet()
        self.cost()
        self.encode()
        self.pyramid()
        self.readout()
        self.network()
        self.results()
        self.noise()
        self.limits()
        self.closing()

    # ------------------------------------------------------------------ title
    def title_card(self):
        venue = eyebrow("Quantum 9, 1761 · 2025")
        title = VGroup(T("Quantum DeepONet:", 42, weight=MEDIUM),
                       T("Neural operators accelerated by quantum computing", 42, weight=MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        authors = T("Pengpeng Xiao, Muqing Zheng, Anran Jiao, Xiu Yang, Lu Lu", 22, MUTED)
        places = T("Yale University · Lehigh University", 18, MUTED)
        block = VGroup(venue, title, authors, places).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        places.next_to(authors, DOWN, buff=0.15, aligned_edge=LEFT)
        block.move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(block.get_corner(UL) + 0.35 * UP, block.get_corner(UL) + 0.35 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        self.play(Create(rule), FadeIn(venue, shift=0.1 * RIGHT), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in (title, authors, places)], lag_ratio=0.25), run_time=1.6)
        self.wait(2.4)
        self.clear_stage()

    # ------------------------------------------------------------------ 01
    def operator(self):
        head = header(1, "Operator learning")
        rv = 1.1 * max(np.abs(v).max() for _, v, _ in SAMPLES)
        ru = 1.1 * max(np.abs(u).max() for _, _, u in SAMPLES)
        spec = dict(x_length=3.6, y_length=2.6, tips=False, axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False})
        axv = Axes(x_range=[0, 1, 0.5], y_range=[-rv, rv, rv], **spec).move_to([-4.7, 0.1, 0])
        axu = Axes(x_range=[0, 1, 0.5], y_range=[-ru, ru, ru], **spec).move_to([4.7, 0.1, 0])

        def curves(i):
            x, v, u = SAMPLES[i]
            return (axv.plot(lambda t: np.interp(t, x, v), x_range=[0, 1, 0.004], color=INK, stroke_width=3.5),
                    axu.plot(lambda t: np.interp(t, x, u), x_range=[0, 1, 0.004], color=ACCENT, stroke_width=3.5))

        labels = VGroup(M("v(x)", 0.9).next_to(axv, UP, buff=0.15), M("u(x)", 0.9, ACCENT).next_to(axu, UP, buff=0.15),
                        T("input function", 17, MUTED).next_to(axv, DOWN, buff=0.2),
                        T("solution", 17, MUTED).next_to(axu, DOWN, buff=0.2))
        solver = box("PDE solver", 3.3, 1.2, CLASSICAL, size=24).move_to([0, 0.1, 0])
        op = box(VGroup(T("neural operator", 24, ACCENT), M("cal(G)", 0.9, ACCENT)).arrange(RIGHT, buff=0.2), 3.3, 1.2, ACCENT).move_to(solver)
        arrows = VGroup(arrow(axv.get_right(), solver.get_left()), arrow(solver.get_right(), axu.get_left()))
        again = T("solve again for every new input", 18, CLASSICAL).next_to(solver, DOWN, buff=0.3)
        once = T("one forward pass per new input", 18, ACCENT).next_to(solver, DOWN, buff=0.3)
        apps = T("uncertainty quantification   ·   optimal experimental design", 20, MUTED).move_to([0, -2.55, 0])
        note = T("illustrative input functions", 15, MUTED).to_corner(DR, buff=0.5)
        ode = VGroup(T("antiderivative operator", 20, ACCENT), M("(d u)/(d x) = v(x), quad u(0) = 0", 1.0)).arrange(DOWN, buff=0.2).move_to([0, 2.35, 0])

        v0, u0 = curves(0)
        with self.voice("operator") as v:
            self.play(FadeIn(head), Create(axv), Create(axu), FadeIn(solver), FadeIn(labels), FadeIn(arrows), run_time=1.2)
            self.play(Create(v0), FadeIn(note), run_time=0.8)
            self.play(Indicate(solver, color=CLASSICAL, scale_factor=1.05), run_time=0.6)
            self.play(Create(u0), FadeIn(again), run_time=0.8)
            for i in (1, 2):
                vi, ui = curves(i)
                self.play(Transform(v0, vi), run_time=0.7)
                self.play(Indicate(solver, color=CLASSICAL, scale_factor=1.05), run_time=0.6)
                self.play(Transform(u0, ui), run_time=0.7)
            self.play(FadeIn(apps, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            self.play(ReplacementTransform(solver, op), ReplacementTransform(again, once), run_time=1.2)
            v.until(1, 0.55)
            vi, ui = curves(0)
            self.play(Transform(v0, vi), run_time=0.7)
            self.play(Transform(u0, ui), run_time=0.4)
            v.until(2)
            self.play(FadeIn(ode, shift=0.1 * DOWN), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 02
    def deeponet(self):
        head = header(2, "DeepONet")
        x, fv, _ = SAMPLES[0]
        ax = Axes(x_range=[0, 1, 0.5], y_range=[-2.6, 2.6, 2.6], x_length=2.3, y_length=1.3, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-5.5, 1.35, 0])
        curve = ax.plot(lambda t: np.interp(t, x, np.clip(fv, -2.5, 2.5)), x_range=[0, 1, 0.005], color=INK, stroke_width=3)
        zs = np.linspace(0.05, 0.95, 8)
        sensors = VGroup(*[Dot(ax.c2p(z, np.interp(z, x, np.clip(fv, -2.5, 2.5))), 0.06, color=CLASSICAL) for z in zs])
        sens_lab = M("v(z_1), dots, v(z_q)", 0.75).next_to(ax, DOWN, buff=0.2)
        xi = VGroup(M("xi", 1.3), T("location", 17, MUTED)).arrange(DOWN, buff=0.15).move_to([-5.5, -1.55, 0])
        branch = box("branch net", 2.3, 0.9, INK, size=22).move_to([-2.0, 1.35, 0])
        trunk = box("trunk net", 2.3, 0.9, INK, size=22).move_to([-2.0, -1.55, 0])
        bcol = M("mat(b_1; b_2; dots.v; b_p)", 0.8).move_to([0.6, 1.35, 0])
        tcol = M("mat(t_1; t_2; dots.v; t_p)", 0.8).move_to([0.6, -1.55, 0])
        prod = VGroup(Circle(0.28, color=INK, stroke_width=2.5), M("times", 0.8)).move_to([2.5, -0.1, 0])
        prod[1].move_to(prod[0])
        out = M("cal(G)_theta (v)(xi)", 1.0, ACCENT).move_to([4.3, -0.1, 0])
        formula = M("cal(G)_theta (v)(xi) = sum_(k=1)^p b_k (v) thin t_k (xi) + b_0", 1.15).move_to([0.6, -3.15, 0])
        VGroup(ax, curve, sensors, sens_lab, xi, branch, trunk, bcol, tcol, prod, out).shift(0.6 * RIGHT)
        with self.voice("deeponet") as v:
            self.play(FadeIn(head), FadeIn(branch, shift=0.1 * RIGHT), FadeIn(trunk, shift=0.1 * RIGHT), run_time=1.2)
            v.until(1)
            self.play(Create(ax), Create(curve), run_time=1.0)
            self.play(LaggedStart(*[GrowFromCenter(d) for d in sensors], lag_ratio=0.12), FadeIn(sens_lab), run_time=1.2)
            self.play(GrowArrow(arrow(ax.get_right(), branch.get_left())), run_time=0.6)
            v.until(1, 0.55)
            self.play(FadeIn(xi), run_time=0.6)
            self.play(GrowArrow(arrow(xi.get_right(), trunk.get_left())), run_time=0.6)
            v.until(2)
            self.play(FadeIn(bcol), FadeIn(tcol), GrowArrow(arrow(branch.get_right(), bcol.get_left())),
                      GrowArrow(arrow(trunk.get_right(), tcol.get_left())), run_time=0.8)
            self.play(GrowArrow(arrow(bcol.get_right(), prod.get_top() + 0.05 * LEFT)), GrowArrow(arrow(tcol.get_right(), prod.get_bottom() + 0.05 * LEFT)),
                      FadeIn(prod), run_time=0.6)
            self.play(GrowArrow(arrow(prod.get_right(), out.get_left())), FadeIn(out), Write(formula), run_time=1.2)
        self.clear_stage()

    # ------------------------------------------------------------------ 03
    def cost(self):
        head = header(3, "Evaluation cost")
        plain = M("bold(x)^prime = sigma(W bold(x) + bold(b))", 1.5).move_to([0, 2.45, 0])
        colored = M(f'bold(x)^prime = #c("{CLASSICAL}", $sigma ($) #c("{QUANTUM}", $W bold(x)$) #c("{CLASSICAL}", $+ bold(b) )$)', 1.5).move_to(plain)
        n = 8
        cells = VGroup(*[Square(0.3, stroke_color=CLASSICAL, stroke_width=1.5, fill_color=CLASSICAL, fill_opacity=0.06)
                         .move_to([j * 0.3, -i * 0.3, 0]) for i in range(n) for j in range(n)]).move_to([-3.7, -0.35, 0])
        vec = VGroup(*[Square(0.3, stroke_color=INK, stroke_width=1.5) .move_to([0, -i * 0.3, 0]) for i in range(n)]).next_to(cells, RIGHT, buff=0.35)
        cl_lab = VGroup(T("classical layer", 20, CLASSICAL, weight=MEDIUM),
                        VGroup(T("n × n weights:", 18, INK), M("cal(O)(n^2)", 0.85, CLASSICAL), T("operations", 18, INK)).arrange(RIGHT, buff=0.15)
                        ).arrange(DOWN, buff=0.15).next_to(VGroup(cells, vec), DOWN, buff=0.35)
        ys = [0.7 - 0.3 * i for i in range(n)]
        wires = VGroup(*[wire(y, 1.4, 6.0, QUANTUM, 2) for y in ys])
        tri = Polygon([2.9, ys[0] + 0.15, 0], [5.3, ys[0] + 0.15, 0], [4.1, ys[-1] - 0.15, 0], stroke_color=METHOD, stroke_width=2,
                      fill_color=METHOD, fill_opacity=0.18)
        load = Polygon([1.75, ys[0] + 0.15, 0], [2.3, ys[0] + 0.15, 0], [2.75, ys[-1] - 0.15, 0], [2.2, ys[-1] - 0.15, 0],
                       stroke_color=QUANTUM, stroke_width=2, fill_color=QUANTUM, fill_opacity=0.18)
        q_lab = VGroup(T("quantum circuit on n qubits", 20, QUANTUM, weight=MEDIUM),
                       VGroup(T("cost", 18, INK), M("cal(O)(n \\/ delta^2)", 0.85, METHOD), T("for error δ per output entry", 18, INK)).arrange(RIGHT, buff=0.15)
                       ).arrange(DOWN, buff=0.15).next_to(wires, DOWN, buff=0.35).align_to(cl_lab, DOWN)
        with self.voice("cost") as v:
            self.play(FadeIn(head), Write(plain), run_time=1.4)
            self.play(FadeIn(cells), FadeIn(vec), run_time=0.8)
            self.play(LaggedStart(*[c.animate.set_fill(opacity=0.55) for c in cells], lag_ratio=0.04), run_time=max(v.dur(0) - 4.0, 2.0))
            self.play(FadeIn(cl_lab, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            wx = part(colored, QUANTUM)
            self.play(FadeTransform(plain, colored), run_time=0.9)
            brace = Brace(wx, DOWN, buff=0.08, color=QUANTUM)
            self.play(GrowFromCenter(brace), FadeIn(T("on a quantum circuit", 17, QUANTUM).next_to(brace, DOWN, buff=0.08)), run_time=0.8)
            self.play(Create(wires), run_time=1.0)
            self.play(FadeIn(load), FadeIn(tri), run_time=0.8)
            self.play(FadeIn(q_lab, shift=0.1 * UP), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ 04
    def encode(self):
        head = header(4, "Unary encoding")
        two = VGroup(wire(1.25, -6.3, -3.3), wire(0.45, -6.3, -3.3))
        gate1 = rbs(-4.8, 1.25, 0.45, "theta", size=0.9)
        kets2 = VGroup(M("q_1", 0.8).next_to(two[0], LEFT, buff=0.2), M("q_2", 0.8).next_to(two[1], LEFT, buff=0.2))
        g_lab = T("RBS gate", 20, QUANTUM, weight=MEDIUM).next_to(two, DOWN, buff=0.35)
        a = f'#c("{ACCENT}", $cos theta$)'
        b = f'#c("{ACCENT}", $sin theta$)'
        c = f'#c("{ACCENT}", $-sin theta$)'
        mat = M(f'U_"RBS" (theta) = mat(1, 0, 0, 0; 0, {a}, {b}, 0; 0, {c}, {a}, 0; 0, 0, 0, 1) #h(0.5em) '
                'mat(delim: #none, ket(00); ket(01); ket(10); ket(11))', 1.1).move_to([2.2, 0.85, 0])
        mat_lab = T("mixes 01 and 10, leaves 00 and 11 unchanged", 18, MUTED).next_to(mat, DOWN, buff=0.35)

        ys = [1.0, 0.38, -0.24, -0.86]
        wires = VGroup(*[wire(y, -6.4, -0.05) for y in ys])
        init = VGroup(*[M(f"ket({b})", 0.8).next_to(w, LEFT, buff=0.15) for b, w in zip("1000", wires)])
        loader = VGroup(*[rbs(-5.7 + 0.72 * k, ys[k], ys[k + 1], f"alpha_{k + 1}") for k in range(3)])
        l_lab = T("data loader", 18, QUANTUM, weight=MEDIUM).next_to(loader, UP, buff=0.35)
        bx0, base = 1.9, -0.25
        kets = VGroup(*[M(f"ket({s})", 0.75).move_to([bx0 + 1.1 * i, -2.25, 0]) for i, s in enumerate(["1000", "0100", "0010", "0001"])])
        axis = Line([bx0 - 0.6, base, 0], [bx0 + 3.9, base, 0], color=MUTED, stroke_width=2)
        state = M("ket(bold(x)) = sum_(j=1)^n x_j ket(e_j)", 1.0).move_to([3.55, 2.35, 0])
        bars = amp_bars(X_IN, bx0, base)
        amp_lab = T("amplitudes of the unary states", 17, MUTED).move_to([bx0 + 1.65, -2.8, 0])

        with self.voice("encode") as v:
            self.play(FadeIn(head), Create(two), FadeIn(kets2), run_time=1.0)
            self.play(FadeIn(gate1), FadeIn(g_lab), run_time=0.8)
            self.play(Write(mat), run_time=1.6)
            v.until(0, 0.55)
            self.play(FadeIn(mat_lab), Indicate(gate1, color=ACCENT, scale_factor=1.1), run_time=1.2)
            v.until(1)
            self.play(FadeOut(VGroup(two, gate1, kets2, g_lab, mat, mat_lab)), run_time=0.6)
            self.play(Create(axis), FadeIn(kets), FadeIn(amp_lab), Write(state), run_time=1.2)
            self.play(LaggedStart(*[GrowFromEdge(r, DOWN if a > 0 else UP) for r, a in zip(bars, X_IN)], lag_ratio=0.25), run_time=1.6)
            v.until(2)
            start = amp_bars([1, 0, 0, 0], bx0, base)
            self.play(Transform(bars, start), Create(wires), FadeIn(init), run_time=1.0)
            self.play(FadeIn(l_lab), run_time=0.5)
            for g, amps in zip(loader, loader_steps(X_IN)):
                self.play(FadeIn(g), run_time=0.45)
                self.play(Transform(bars, amp_bars(amps, bx0, base)), run_time=1.0)
        self.enc = dict(head=head, ys=ys, bars=bars, bx0=bx0, base=base, state=state)

    # ------------------------------------------------------------------ 05
    def pyramid(self):
        e = self.enc
        head = header(5, "Orthogonal pyramid")
        ys, bars = e["ys"], e["bars"]
        gates, k = VGroup(), 0
        cols = pyramid_columns(4)
        for c, col in enumerate(cols):
            for j in col:
                gates.add(rbs(-3.25 + 0.62 * c, ys[j], ys[j + 1], f"theta_{k + 1}", METHOD))
                k += 1
        p_lab = VGroup(T("pyramid", 18, METHOD, weight=MEDIUM), M("W", 0.9, METHOD)).arrange(RIGHT, buff=0.15).next_to(gates, UP, buff=0.35)
        count = VGroup(M("n(n-1) / 2 = 6", 0.9, METHOD), T("angles for n = 4", 18, MUTED)).arrange(DOWN, buff=0.12).move_to([-3.4, -2.35, 0])
        ystate = M("ket(bold(y)) = W ket(bold(x))", 1.0, METHOD).move_to(e["state"])
        by_col, k = [], 0
        for col in cols:
            by_col.append(VGroup(*gates[k:k + len(col)]))
            k += len(col)
        with self.voice("pyramid") as v:
            self.play(FadeOut(e["head"]), FadeIn(head), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(g, shift=0.1 * DOWN) for g in gates], lag_ratio=0.3), FadeIn(p_lab), run_time=2.6)
            self.play(FadeIn(count, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            for g, amps in zip(by_col, pyramid_steps(X_IN)):
                self.play(Indicate(g, color=METHOD, scale_factor=1.12), Transform(bars, amp_bars(amps, e["bx0"], e["base"], color=QUANTUM)),
                          run_time=max((v.dur(1) - 1.4) / 5, 0.9))
            self.play(bars.animate.set_fill(METHOD, 0.85), FadeTransform(e["state"], ystate), run_time=0.9)
        self.clear_stage()

    # ------------------------------------------------------------------ 06
    def readout(self):
        head = header(6, "Tomography")
        ya, ys = 2.55, [1.9, 1.4, 0.9, 0.4]
        x0, x1 = -5.9, 5.8
        wires = VGroup(wire(ya, x0, x1), *[wire(y, x0, x1) for y in ys])
        w_lab = VGroup(T("ancilla", 16, MUTED).next_to(wires[0], LEFT, buff=0.15),
                       T("data", 16, MUTED).move_to([x0 - 0.45, (ys[0] + ys[-1]) / 2, 0]))
        top, bot = ys[0] + 0.22, ys[-1] - 0.22
        mid = (top + bot) / 2

        def block(x, w, label, color):
            r = RoundedRectangle(corner_radius=0.08, width=w, height=top - bot, stroke_color=color, stroke_width=2.5,
                                 fill_color=PAPER, fill_opacity=1).move_to([x, mid, 0])
            r2 = r.copy().set_fill(color, 0.12)
            return VGroup(r, r2, M(label, 0.8, color).move_to(r))

        h1 = gate("H", 0.5, 0.42, size=0.7).move_to([-5.35, ya, 0])
        c1 = cnot(-4.7, ya, ys[0])
        load = block(-3.6, 1.2, '"load" thin bold(x)', QUANTUM)
        pyr = VGroup(Polygon([-2.75, top, 0], [-1.05, top, 0], [-1.9, bot, 0], stroke_color=METHOD, stroke_width=2.5,
                             fill_color=METHOD, fill_opacity=0.22))
        pyr.add(M("W", 0.9, METHOD).move_to([-1.9, top - 0.45, 0]))
        undo = block(-0.1, 1.35, '"load"^dagger thin bold(u)', QUANTUM)
        xg = gate("X", 0.5, 0.42, size=0.7).move_to([1.05, ya, 0])
        c2 = cnot(1.7, ya, ys[0])
        redo = block(2.85, 1.2, '"load" thin bold(u)', QUANTUM)
        h2 = gate("H", 0.5, 0.42, size=0.7).move_to([4.0, ya, 0])
        meters = VGroup(*[meter().scale(0.62).move_to([5.05, y, 0]) for y in [ya, *ys]])
        u_lab = M("bold(u) = (1 / sqrt(n), dots, 1 / sqrt(n))", 0.7, MUTED).move_to([1.4, -0.2, 0])
        circuit = VGroup(h1, c1, load, pyr, undo, xg, c2, redo, h2, meters)

        px = [-5.7, -4.35, -3.0, -1.65]
        base, sc = -3.3, 5.0
        pair = VGroup()
        for j in range(4):
            pair.add(VGroup(Rectangle(width=0.4, height=PR0[j] * sc, stroke_width=0, fill_color=ACCENT, fill_opacity=0.85)
                            .move_to([px[j] - 0.22, base + PR0[j] * sc / 2, 0]),
                            Rectangle(width=0.4, height=PR1[j] * sc, stroke_width=0, fill_color=MUTED, fill_opacity=0.6)
                            .move_to([px[j] + 0.22, base + PR1[j] * sc / 2, 0])))
        axis = Line([px[0] - 0.7, base, 0], [px[-1] + 0.7, base, 0], color=MUTED, stroke_width=2)
        e_lab = VGroup(*[M(f"ket(e_{j + 1})", 0.7).move_to([px[j], base - 0.32, 0]) for j in range(4)])
        legend = VGroup(VGroup(Square(0.2, stroke_width=0, fill_color=ACCENT, fill_opacity=0.85), T("ancilla 0", 16)).arrange(RIGHT, buff=0.1),
                        VGroup(Square(0.2, stroke_width=0, fill_color=MUTED, fill_opacity=0.6), T("ancilla 1", 16)).arrange(RIGHT, buff=0.1)
                        ).arrange(RIGHT, buff=0.35).move_to([(px[0] + px[-1]) / 2, -0.75, 0])
        signs = VGroup(*[T("+" if y >= 0 else "−", 24, QUANTUM, weight=MEDIUM).next_to(p, UP, buff=0.12) for p, y in zip(pair, Y_OUT)])
        prob = M("Pr[0, e_j] - Pr[1, e_j] = y_j / sqrt(n)", 1.0).move_to([3.55, -1.15, 0])
        shots = VGroup(VGroup(M("1 / delta^2", 0.8), T("shots: error ≈ δ per entry, independent of n", 18)).arrange(RIGHT, buff=0.15),
                       VGroup(T("circuit depth ∝ n per shot, so layer cost", 18), M("cal(O)(n \\/ delta^2)", 0.8, METHOD)).arrange(RIGHT, buff=0.15)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.55, -2.25, 0])
        keep = VGroup(T("0010", 22, QUANTUM, weight=MEDIUM), T("unary: keep", 17, QUANTUM)).arrange(RIGHT, buff=0.15)
        drop = VGroup(T("0110", 22, ACCENT, weight=MEDIUM), T("two 1s: discard", 17, ACCENT)).arrange(RIGHT, buff=0.15)
        post = VGroup(keep, drop).arrange(RIGHT, buff=0.6).move_to([3.55, -3.35, 0])
        strike = Line(drop[0].get_left() + 0.05 * LEFT, drop[0].get_right() + 0.05 * RIGHT, color=ACCENT, stroke_width=3)

        with self.voice("readout") as v:
            self.play(FadeIn(head), Create(wires), FadeIn(w_lab), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(m) for m in circuit], lag_ratio=0.18), run_time=2.6)
            self.play(FadeIn(u_lab), run_time=0.6)
            v.until(1)
            self.play(Create(axis), FadeIn(e_lab), FadeIn(legend), run_time=0.8)
            self.play(LaggedStart(*[GrowFromEdge(p, DOWN) for p in pair], lag_ratio=0.2), run_time=1.6)
            self.play(Write(prob), run_time=1.2)
            v.until(1, 0.6)
            self.play(LaggedStart(*[FadeIn(s, shift=0.1 * DOWN) for s in signs], lag_ratio=0.2), run_time=1.2)
            v.until(2)
            self.play(FadeIn(shots, shift=0.1 * UP), run_time=1.0)
            v.until(3)
            self.play(FadeIn(post), run_time=0.8)
            v.until(3, 0.55)
            self.play(Create(strike), run_time=0.5)
        self.clear_stage()

    # ------------------------------------------------------------------ 07
    def network(self):
        head = header(7, "Quantum DeepONet")
        rows = VGroup()
        for y, inp, outp, name in ((2.2, "v(z_1..z_q)", "b_1..b_p", "branch net"), (0.5, "xi", "t_1..t_p", "trunk net")):
            parts = [M(inp.replace("..", ", dots, "), 0.7),
                     box("quantum layer", 1.7, 0.75, METHOD, size=17),
                     VGroup(Circle(0.34, color=CLASSICAL, stroke_width=2.5), M("sigma, bold(b)", 0.6, CLASSICAL)),
                     box("quantum layer", 1.7, 0.75, METHOD, size=17),
                     VGroup(Circle(0.34, color=CLASSICAL, stroke_width=2.5), M("sigma, bold(b)", 0.6, CLASSICAL)),
                     box("linear output", 1.7, 0.75, CLASSICAL, size=17),
                     M(outp.replace("..", ", dots, "), 0.7)]
            for p in parts[2::2][:2]:
                p[1].move_to(p[0])
            for part_, xc in zip(parts, (-6.05, -3.95, -2.3, -0.65, 1.0, 2.65, 4.45)):
                part_.move_to([xc, y, 0])
            row = VGroup(*parts)
            links = VGroup(*[arrow(a.get_right(), b.get_left(), buff=0.08) for a, b in zip(parts, parts[1:])])
            lab = T(name, 17, MUTED).next_to(row, UP, buff=0.12).align_to(row, LEFT)
            rows.add(VGroup(lab, row, links))
        prod = VGroup(Circle(0.26, color=INK, stroke_width=2.5), M("times", 0.7)).move_to([6.15, 1.35, 0])
        prod[1].move_to(prod[0])
        to_prod = VGroup(arrow(rows[0][1][-1].get_right(), prod.get_top(), buff=0.1), arrow(rows[1][1][-1].get_right(), prod.get_bottom(), buff=0.1))
        name = T("quantum orthogonal neural networks in place of both nets", 18, METHOD).move_to([-0.2, -0.35, 0])
        train = box(VGroup(T("classical orthogonal network", 19, CLASSICAL, weight=MEDIUM), T("training", 16, MUTED)).arrange(DOWN, buff=0.06),
                    4.2, 1.0, CLASSICAL).move_to([-3.9, -1.55, 0])
        run = box(VGroup(T("quantum circuits", 19, QUANTUM, weight=MEDIUM), T("evaluation", 16, MUTED)).arrange(DOWN, buff=0.06),
                  4.2, 1.0, QUANTUM).move_to([3.9, -1.55, 0])
        hand = arrow(train.get_right(), run.get_left(), color=INK)
        hand_lab = VGroup(T("trained angles", 17, INK), M("theta_1, dots, theta_d", 0.7)).arrange(RIGHT, buff=0.15).next_to(hand, UP, buff=0.1)
        cmp = VGroup(
            VGroup(T("evaluation, per layer", 18, INK), M("cal(O)(n \\/ delta^2)", 0.8, METHOD), T("quantum", 17, METHOD),
                   M("cal(O)(n^2)", 0.8, CLASSICAL), T("classical", 17, CLASSICAL)).arrange(RIGHT, buff=0.22),
            VGroup(T("training, per weight update", 18, INK), M("cal(O)(n^2)", 0.8, CLASSICAL), T("as for a standard network", 17, CLASSICAL)).arrange(RIGHT, buff=0.22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -3.05, 0])
        with self.voice("network") as v:
            self.play(FadeIn(head), run_time=0.4)
            for r in rows:
                self.play(FadeIn(r[0]), LaggedStart(*[FadeIn(p, shift=0.08 * RIGHT) for p in r[1]], lag_ratio=0.15), FadeIn(r[2]), run_time=1.8)
            self.play(FadeIn(to_prod), FadeIn(prod), FadeIn(name), run_time=0.8)
            v.until(1)
            self.play(FadeIn(train, shift=0.1 * RIGHT), run_time=0.8)
            v.until(2)
            self.play(GrowArrow(hand), FadeIn(hand_lab), FadeIn(run, shift=0.1 * RIGHT), run_time=1.2)
            v.until(2, 0.35)
            self.play(LaggedStart(*[FadeIn(c, shift=0.1 * UP) for c in cmp], lag_ratio=0.5), run_time=1.6)
        self.clear_stage()

    # ------------------------------------------------------------------ 08
    def results(self):
        head = header(8, "Noiseless results")
        ax = Axes(x_range=[0, 6.4, 1], y_range=[0, 2.5, 0.5], x_length=7.4, y_length=4.2, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-2.55, -0.55, 0])
        grid = VGroup(*[DashedLine(ax.c2p(0, t), ax.c2p(6.4, t), color=LINE, stroke_width=1.5, dash_length=0.08) for t in (0.5, 1.0, 1.5, 2.0, 2.5)])
        ticks = VGroup(*[T(f"{t:g}%", 15, MUTED).next_to(ax.c2p(0, t), LEFT, buff=0.12) for t in (0, 0.5, 1.0, 1.5, 2.0, 2.5)])
        ylab = T("test L2 relative error", 17, MUTED).next_to(ax, UP, buff=0.2).align_to(ax, LEFT).shift(0.4 * LEFT)

        def bar(xc, val, color, opacity=0.85):
            lo, hi = ax.c2p(xc - 0.21, 0), ax.c2p(xc + 0.21, val)
            r = Rectangle(width=hi[0] - lo[0], height=hi[1] - lo[1], stroke_width=0, fill_color=color, fill_opacity=opacity)
            r.move_to((lo + hi) / 2)
            return VGroup(r, T(f"{val:.2f}%", 16, color).next_to(r, UP, buff=0.08))

        q = [bar(0.8, 0.49, METHOD), bar(2.0, 0.84, METHOD), bar(3.35, 2.25, METHOD), bar(5.15, 1.38, METHOD)]
        c = [bar(4.05, 1.91, CLASSICAL), bar(5.85, 1.05, CLASSICAL)]
        row1 = VGroup(M("l = 1.0", 0.65, MUTED).next_to(ax.c2p(0.8, 0), DOWN, buff=0.17),
                      M("l = 0.5", 0.65, MUTED).next_to(ax.c2p(2.0, 0), DOWN, buff=0.17),
                      T("advection", 17).next_to(ax.c2p(3.7, 0), DOWN, buff=0.15),
                      T("Burgers'", 17).next_to(ax.c2p(5.5, 0), DOWN, buff=0.15))
        groups = VGroup(row1, T("antiderivative", 17).move_to([ax.c2p(1.4, 0)[0], row1[0].get_bottom()[1] - 0.2, 0]))
        params = VGroup(*[VGroup(T(t, 15, MUTED), T("parameters", 15, MUTED)).arrange(DOWN, buff=0.04).next_to(row1[i], DOWN, buff=0.1)
                          for i, t in ((2, "3081 vs 3171"), (3, "2429 vs 2260"))])
        legend = VGroup(VGroup(Square(0.22, stroke_width=0, fill_color=METHOD, fill_opacity=0.85), T("quantum DeepONet", 17)).arrange(RIGHT, buff=0.12),
                        VGroup(Square(0.22, stroke_width=0, fill_color=CLASSICAL, fill_opacity=0.85), T("classical DeepONet", 17)).arrange(RIGHT, buff=0.12)
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.1, 2.3, 0], aligned_edge=LEFT)
        same = card([T("noiseless Qiskit simulation", 18, METHOD, weight=MEDIUM),
                     T("equals classical training", 18, INK),
                     T("in every example", 18, INK)], 3.8, METHOD).move_to([4.55, 0.55, 0])
        pinn = card([T("physics-informed", 19, METHOD, weight=MEDIUM),
                     T("no solution data", 17, MUTED),
                     VGroup(T("antiderivative", 18), T("0.76%", 18, METHOD, weight=MEDIUM)).arrange(RIGHT, buff=0.3),
                     VGroup(T("Poisson's equation", 18), T("0.95%", 18, METHOD, weight=MEDIUM)).arrange(RIGHT, buff=0.3),
                     T("l = 1, 10 principal components", 16, MUTED)], 3.8, METHOD).move_to([4.55, -2.25, 0])
        grow = lambda b: AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1], shift=0.1 * UP))
        with self.voice("results") as v:
            self.play(FadeIn(head), Create(ax), FadeIn(grid), FadeIn(ticks), FadeIn(ylab), FadeIn(groups), run_time=1.4)
            self.play(FadeIn(legend[0]), FadeIn(same, shift=0.1 * UP), run_time=1.0)
            v.until(1, 0.08)
            self.play(grow(q[0]), run_time=0.8)
            self.play(grow(q[1]), run_time=0.8)
            v.until(1, 0.62)
            self.play(grow(q[2]), run_time=0.8)
            v.until(1, 0.84)
            self.play(grow(q[3]), run_time=0.8)
            v.until(2)
            self.play(FadeIn(legend[1]), grow(c[0]), grow(c[1]), run_time=1.2)
            self.play(FadeIn(params), run_time=0.8)
            v.until(3)
            self.play(FadeIn(pinn, shift=0.1 * UP), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 09
    def noise(self):
        head = header(9, "Noise")
        w, h = 6.6, 3.0
        frames = VGroup(*[RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=LINE, stroke_width=2,
                                           fill_color=PAPER, fill_opacity=1).move_to(p)
                          for p in ([-3.55, 1.3, 0], [3.55, 1.3, 0], [-3.55, -2.15, 0], [3.55, -2.15, 0])])
        titles = VGroup(*[T(t, 19, c, weight=MEDIUM).next_to(f.get_corner(UL), DR, buff=0.22).align_to(f, LEFT).shift(0.3 * RIGHT)
                          for t, c, f in (("finite shots", INK, frames[0]), ("depolarizing gate noise", INK, frames[1]),
                                          ("post-selection", QUANTUM, frames[2]), ("network shape", INK, frames[3]))])
        ax = Axes(x_range=[0, 6, 1], y_range=[0, 4, 1], x_length=3.5, y_length=1.75, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to([-4.45, 1.05, 0])
        line = ax.plot(lambda t: 3.3 - 0.5 * t, x_range=[0.2, 5.8], color=ACCENT, stroke_width=4)
        a_lab = VGroup(T("shots", 16, MUTED).next_to(ax.x_axis, DOWN, buff=0.1),
                       T("10³", 16, MUTED).next_to(ax.c2p(0, 0), DOWN, buff=0.1), T("10⁹", 16, MUTED).next_to(ax.c2p(6, 0), DOWN, buff=0.1),
                       T("gap to noiseless", 15, MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.1))
        law = VGroup(M("prop 1 / sqrt(N_\"shot\")", 0.95, ACCENT), T("log–log slope −1/2", 16, MUTED)).arrange(DOWN, buff=0.14).move_to([-1.45, 1.05, 0])
        dep = VGroup(VGroup(T("function approximation,", 17, MUTED), M("f(x) = 1 / (1 + 25 x^2)", 0.75, MUTED)).arrange(RIGHT, buff=0.15),
                     VGroup(T("λ = 0.002", 20, INK), T("about 20% error", 20, ACCENT, weight=MEDIUM),
                            T("(noiseless 0.15%)", 17, MUTED)).arrange(RIGHT, buff=0.25),
                     VGroup(T("ibm_brisbane noise model", 20, INK), T("14.4% error", 20, ACCENT, weight=MEDIUM)).arrange(RIGHT, buff=0.3),
                     T("non-unary shots discarded · 10⁷ shots", 16, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        dep.move_to(frames[1]).shift(0.2 * DOWN).align_to(titles[1], LEFT)
        post = VGroup(T("keep unary outcomes only", 21, INK),
                      VGroup(T("0010 keep", 21, QUANTUM, weight=MEDIUM), T("0110 discard", 21, ACCENT, weight=MEDIUM)).arrange(RIGHT, buff=0.6),
                      VGroup(T("substantially lower error in the antiderivative tests,", 17, MUTED),
                             T("still well above the noiseless error under gate noise", 17, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        post.move_to(frames[2]).shift(0.2 * DOWN).align_to(titles[2], LEFT)
        deep = network_icon(6, 3, dx=0.36, dy=0.28).move_to([1.95, -1.75, 0])
        wide = network_icon(2, 6, dx=0.36, dy=0.28).move_to([5.2, -1.75, 0])
        deep_lab = VGroup(T("deeper", 18, ACCENT, weight=MEDIUM), T("error grows quickly", 16, INK)).arrange(DOWN, buff=0.05)
        wide_lab = VGroup(T("wider", 18, QUANTUM, weight=MEDIUM), T("little growth", 16, INK), T("in the tested range", 16, INK)).arrange(DOWN, buff=0.05)
        low = min(deep.get_bottom()[1], wide.get_bottom()[1]) - 0.2
        deep_lab.move_to([deep.get_center()[0], low, 0], aligned_edge=UP)
        wide_lab.move_to([wide.get_center()[0], low, 0], aligned_edge=UP)
        with self.voice("noise") as v:
            self.play(FadeIn(head), FadeIn(frames[0]), FadeIn(titles[0]), run_time=0.8)
            self.play(Create(ax), FadeIn(a_lab), Create(line), run_time=1.4)
            self.play(FadeIn(law, shift=0.1 * UP), run_time=0.8)
            v.until(1)
            self.play(FadeIn(frames[1]), FadeIn(titles[1]), FadeIn(dep[0]), run_time=0.8)
            v.until(1, 0.45)
            self.play(FadeIn(dep[1], shift=0.1 * UP), FadeIn(dep[3]), run_time=0.7)
            v.until(2)
            self.play(FadeIn(dep[2], shift=0.1 * UP), run_time=0.7)
            v.until(3)
            self.play(FadeIn(frames[2]), FadeIn(titles[2]), FadeIn(post[:2], shift=0.1 * UP), run_time=1.0)
            v.until(3, 0.5)
            self.play(FadeIn(post[2]), run_time=0.7)
            v.until(4)
            self.play(FadeIn(frames[3]), FadeIn(titles[3]), FadeIn(deep), FadeIn(deep_lab), run_time=1.0)
            v.until(4, 0.6)
            self.play(FadeIn(wide), FadeIn(wide_lab), run_time=0.8)
            v.until(5)
            self.play(Indicate(wide_lab[0], color=QUANTUM, scale_factor=1.2), run_time=1.0)
        self.clear_stage()

    # ------------------------------------------------------------------ 10
    def limits(self):
        head = header(10, "Limits")
        rows = VGroup(
            T("One qubit per vector entry limits network width on current devices.", 24),
            T("Circuit depth grows as n, above the O(log n) entanglement bound for noisy devices.", 24),
            T("The tested noise models leave out coherent noise and cross-talk.", 24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to([0.2, 0.2, 0])
        marks = VGroup(*[Line(r.get_left() + 0.35 * LEFT + 0.2 * UP, r.get_left() + 0.35 * LEFT + 0.2 * DOWN, color=ACCENT, stroke_width=5) for r in rows])
        with self.voice("limits") as v:
            self.play(FadeIn(head), FadeIn(rows[0], shift=0.1 * UP), FadeIn(marks[0]), run_time=1.0)
            v.until(1)
            self.play(FadeIn(rows[1], shift=0.1 * UP), FadeIn(marks[1]), run_time=0.8)
            v.until(2)
            self.play(FadeIn(rows[2], shift=0.1 * UP), FadeIn(marks[2]), run_time=0.8)
        self.clear_stage()

    # ------------------------------------------------------------------ close
    def closing(self):
        lines = VGroup(T("An orthogonal DeepONet is trained classically, and each layer", 30, weight=MEDIUM),
                       T("is evaluated on a circuit whose cost grows linearly with n.", 30, weight=MEDIUM),
                       VGroup(T("Noiseless simulations reproduce the classically trained networks.", 21, MUTED),
                              T("Simulated gate noise still raises the error sharply.", 21, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lines[2].shift(0.15 * DOWN)
        cite = VGroup(eyebrow("Read the paper"),
                      T("Xiao, Zheng, Jiao, Yang, Lu. Quantum 9, 1761 (2025)", 20),
                      T("doi.org/10.22331/q-2025-06-04-1761   ·   arXiv:2409.15683", 20, ACCENT),
                      T("Code: github.com/lu-group/quantum-deeponet", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        block = VGroup(lines, cite).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(ORIGIN).to_edge(LEFT, buff=0.9)
        rule = Line(lines.get_corner(UL) + 0.4 * UP, lines.get_corner(UL) + 0.4 * UP + 1.2 * RIGHT, color=ACCENT, stroke_width=4)
        with self.voice("close") as v:
            self.play(Create(rule), LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in lines], lag_ratio=0.35), run_time=2.4)
            v.until(0, 0.55)
            self.play(FadeIn(cite, shift=0.1 * UP), run_time=1.0)
        self.wait(3.0)


class DeepONetPoster(Scene):
    """Still image for the website thumbnail."""

    def construct(self):
        label = eyebrow("Quantum DeepONet", size=30).to_corner(UL, buff=0.6)
        n = 6
        ys = [1.9 - 0.62 * i for i in range(n)]
        wires = VGroup(*[wire(y, -6.2, 6.2, INK, 3) for y in ys])
        load = VGroup(*[rbs(-5.3 + 0.55 * k, ys[k], ys[k + 1], color=QUANTUM) for k in range(n - 1)])
        gates = VGroup(*[rbs(-1.9 + 0.62 * c, ys[j], ys[j + 1], color=METHOD) for c, col in enumerate(pyramid_columns(n)) for j in col])
        for g in (*load, *gates):
            g[0].set_stroke(width=8)
            for d in g[1]:
                d.scale(1.4)
        sub = T("each layer: load, orthogonal pyramid, readout", 36, ACCENT, weight=MEDIUM).move_to([0, -2.75, 0])
        self.add(label, wires, load, gates, sub)
