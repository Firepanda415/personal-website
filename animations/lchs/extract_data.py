"""Copy the plotted paper data from the CV-DV-LCHS repository into data.json.

Usage: python extract_data.py /path/to/CV-DV-LCHS

The squeezed-Fock coefficients are the shared kernel state at
(r, r', beta, N) = (1.6, 0.25, 0.5, 32). The truncation tail is eps_tr(N) of Fig. 3(a).
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

COEFFS = "results_revision_v2/coefficients_dirichlet_r1p6_rp0p25_b0p5_N32_nq240.json"
TAIL = "results_joint_tradeoff/epsilon_tail.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(repo):
    repo = Path(repo)
    coeffs = json.loads((repo / COEFFS).read_text())
    with open(repo / TAIL) as f:
        tail = [(int(r["n_coeff"]), float(r["eps_tr"])) for r in csv.DictReader(f)]
    data = {
        "kernel": coeffs["kernel"],
        "coefficients_re": coeffs["coefficients_re"],
        "coefficients_im": coeffs["coefficients_im"],
        "epsilon_tail": tail,
        "sources": {name: sha256(repo / name) for name in (COEFFS, TAIL)},
    }
    out = Path(__file__).with_name("data.json")
    out.write_text(json.dumps(data, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1])
