"""Build data.json for section 04 of the Bayesian explainer from the paper's code repository.

The repository (github.com/QCOL-LU/Bayesian-Error-Characterization-and-Mitigation) ships a
tutorial run on ibm_perth from August 2022: readout bit strings of the Hadamard test circuit
(Tutorial/Data/Filter_data.csv), the vendor calibration (Params.csv), and saved posterior samples
(Post_Qubit1.csv). The paper's own experiments used ibmqx2 and are not in the repository.

This script repeats the repository's consistent Bayesian inference (src/measfilter.py, output())
for one qubit with the tutorial's settings, 40000 prior samples, prior standard deviation 0.1,
1024 shots per estimate, and seed 127, and stores densities on a grid plus a subset of prior samples.

Usage: python bayesian/extract_data.py /path/to/Bayesian-Error-Characterization-and-Mitigation
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import stats

QUBIT = 1
N_PRIOR = 40000
PRIOR_SD = 0.1
SHOTS_PER_POINT = 1024
SEED = 127
N_DOTS = 900
GRID = np.linspace(0.30, 0.70, 321)


def params(path):
    rows, one = [], {}
    for row in csv.reader(path.open()):
        if row[0] == "End":
            rows.append(one)
            one = {}
        else:
            one[row[0]] = row[1]
    return rows


def main(repo):
    repo = Path(repo)
    data_dir = repo / "Tutorial" / "Data"
    files = {name: data_dir / name for name in ("Filter_data.csv", "Params.csv", f"Post_Qubit{QUBIT}.csv")}
    bits = np.array(next(csv.reader(files["Filter_data.csv"].open())))
    # Little-endian bit strings, as in getData0(): qubit i is character i of the reversed string.
    zero = np.array([b[::-1][QUBIT] == "0" for b in bits])
    d = zero.reshape(-1, SHOTS_PER_POINT).mean(axis=1)

    p = next(q for q in params(files["Params.csv"]) if int(q["qubit"]) == QUBIT)
    center = np.array([1 - float(p["pm1p0"]), 1 - float(p["pm0p1"])])   # (Pr(0|0), Pr(1|1))
    center[(center == 1) | (center < 0.7)] = 0.95

    rng = np.random.default_rng(SEED)
    a, b = (0 - center) / PRIOR_SD, (1 - center) / PRIOR_SD
    prior = np.column_stack([stats.truncnorm.rvs(a[j], b[j], loc=center[j], scale=PRIOR_SD, size=N_PRIOR, random_state=rng)
                             for j in range(2)])
    q = 0.5 * prior[:, 0] + 0.5 * (1 - prior[:, 1])     # QoI(): Pr(measure 0) of H|0> under readout error
    obs, pushed = stats.gaussian_kde(d), stats.gaussian_kde(q)
    dense = np.linspace(0, 1, 2001)
    po, pp = obs(dense), pushed(dense)
    ok = (po > 1e-6) & (pp > 1e-6)
    bound = (po[ok] / pp[ok]).max()
    accept = rng.uniform(size=N_PRIOR) < obs(q) / pushed(q) / bound
    post = stats.gaussian_kde(q[accept])

    stored = np.loadtxt(files[f"Post_Qubit{QUBIT}.csv"], delimiter=",")
    pick = rng.choice(N_PRIOR, N_DOTS, replace=False)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = {
        "source": {"repository": "https://github.com/QCOL-LU/Bayesian-Error-Characterization-and-Mitigation", "commit": commit,
                   "device": "ibm_perth", "calibration_date": p["update_date"], "qubit": QUBIT,
                   "sha256": {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in files.items()}},
        "settings": {"n_prior": N_PRIOR, "prior_sd": PRIOR_SD, "shots_per_point": SHOTS_PER_POINT, "seed": SEED},
        "vendor": {"m0": float(p["pm1p0"]), "m1": float(p["pm0p1"])},
        "estimates": [round(float(x), 6) for x in d],
        "grid": [round(float(x), 5) for x in GRID],
        "density": {k: [round(float(x), 5) for x in f(GRID)] for k, f in (("data", obs), ("prior", pushed), ("kept", post))},
        "dots": [[round(1 - prior[i, 0], 5), round(1 - prior[i, 1], 5), bool(accept[i])] for i in pick],
        "summary": {"accepted_fraction": round(float(accept.mean()), 4),
                    "posterior_mean_m0_m1": [round(float(1 - prior[accept, 0].mean()), 4), round(float(1 - prior[accept, 1].mean()), 4)],
                    "stored_posterior_mean_m0_m1": [round(float(1 - stored[:, 0].mean()), 4), round(float(1 - stored[:, 1].mean()), 4)],
                    "stored_posterior_size": int(stored.shape[0])},
    }
    target = Path(__file__).resolve().with_name("data.json")
    target.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"]), f"{len(d)} estimates, mean {d.mean():.4f}", f"-> {target}")


if __name__ == "__main__":
    main(sys.argv[1])
