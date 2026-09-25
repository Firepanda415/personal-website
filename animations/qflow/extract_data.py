"""Collect the plotted QFlow data into data.json.

Usage: python extract_data.py /path/to/arXiv-2606.04186-source

The energy profile is traced from the top panel of Fig. 3 (H2O_TZ.png in the arXiv source of
arXiv:2606.04186v1), because the raw ExaChem output is not published. Each pixel column of a
cycle's line gives one point, calibrated on the gridlines at -76.05 ... -76.30 hartree and at
combination numbers 0 ... 12000. The traced end point (-76.3169) matches the Table 1 mean
(-76.3168), and the dashed CCSD line reads -76.3247.

The cycle sizes rerun the coverage-driven sampling algorithm (Fig. 1 of the paper) with
(n_o, n_v) = (3, 3) for three seeds. Occupied and virtual counts follow from the qubit counts
in Table 1 with the oxygen 1s orbital uncorrelated. The paper's own seed is not published.
"""
import hashlib
import itertools
import json
import random
import sys
from math import comb
from pathlib import Path

import numpy as np
from PIL import Image

CYCLE_RGB = {1: (31, 119, 180), 2: (255, 127, 14), 3: (44, 160, 44), 4: (214, 39, 40), 5: (148, 103, 189)}
GRID_Y = (111.5, 1115.5)   # pixel rows of the -76.05 and -76.30 gridlines
GRID_X = (576.5, 2674.5)   # pixel columns of combination numbers 0 and 12000
PANEL = (95, 1234)         # pixel rows of the top panel

# Table 1 and the propane paragraph: (occupied, virtual, cycle size reported in the paper).
SYSTEMS = {"H2O cc-pVDZ": (4, 19, 292), "H2O aug-cc-pVDZ": (4, 36, 1089), "H2O cc-pVTZ": (4, 53, 2387),
           "H2O aug-cc-pVTZ": (4, 87, 6412), "H2O cc-pVQZ": (4, 110, 10319), "C3H8 cc-pVDZ": (13, 69, 56860)}


def trace(png):
    im = np.asarray(Image.open(png).convert("RGB")).astype(int)
    energy = lambda r: -76.05 - (r - GRID_Y[0]) / (GRID_Y[1] - GRID_Y[0]) * 0.25
    combo = lambda c: (c - GRID_X[0]) / (GRID_X[1] - GRID_X[0]) * 12000
    top = im[PANEL[0]:PANEL[1]]
    n, cycle, e = [], [], []
    for x in range(478, 2764):  # inside the axes frame
        best = None
        for k, rgb in CYCLE_RGB.items():
            hit = np.abs(top[:, x] - np.array(rgb)).max(1) < 40
            if hit.sum() >= 3 and (best is None or hit.sum() > best[2]):
                best = (k, np.flatnonzero(hit) + PANEL[0], hit.sum())
        if best:
            n.append(round(combo(x), 1))
            cycle.append(best[0])
            e.append(round(float(energy(np.median(best[1]))), 5))
    return dict(combination=n, cycle=cycle, energy=e, ccsd=round(energy(1214.5), 4))


def cycle_size(n_occ, n_vir, seed, no=3, nv=3):
    """Number of (no, nv) active spaces the greedy sampler keeps before every
    (o1, o2, v1, v2) double-excitation group is covered."""
    rng = random.Random(seed)
    occ = {p: i for i, p in enumerate(itertools.combinations(range(n_occ), 2))}
    vir = {p: i for i, p in enumerate(itertools.combinations(range(n_vir), 2))}
    left, kept = set(range(len(occ) * len(vir))), 0
    while left:
        O, V = sorted(rng.sample(range(n_occ), no)), sorted(rng.sample(range(n_vir), nv))
        new = {occ[a] * len(vir) + vir[b] for a in itertools.combinations(O, 2) for b in itertools.combinations(V, 2)} & left
        if new:
            kept += 1
            left -= new
    return kept


def parameters(n_occ, n_vir):
    """Spin-conserving singles and doubles amplitudes over spin orbitals."""
    return 2 * n_occ * n_vir + 2 * comb(n_occ, 2) * comb(n_vir, 2) + n_occ ** 2 * n_vir ** 2


def main(src):
    png = Path(src) / "H2O_TZ.png"
    sampling = {name: dict(occupied=o, virtual=v, qubits=2 * (o + v), groups=comb(o, 2) * comb(v, 2), paper=paper,
                           rerun=[cycle_size(o, v, seed) for seed in range(3)], parameters=parameters(o, v))
                for name, (o, v, paper) in SYSTEMS.items()}
    data = dict(source=dict(file="H2O_TZ.png (arXiv:2606.04186v1 source)", sha256=hashlib.sha256(png.read_bytes()).hexdigest()),
                h2o_tz=trace(png), sampling=sampling)
    out = Path(__file__).with_name("data.json")
    out.write_text(json.dumps(data, separators=(",", ":")))
    for name, s in sampling.items():
        print(f"{name}: paper {s['paper']}, rerun {s['rerun']}, {s['parameters']} parameters")
    print(f"trace: {len(data['h2o_tz']['energy'])} points, end {data['h2o_tz']['energy'][-1]}, CCSD {data['h2o_tz']['ccsd']}")


if __name__ == "__main__":
    main(sys.argv[1])
