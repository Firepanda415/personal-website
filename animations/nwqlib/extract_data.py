"""Collect the NWQLib numbers plotted in the explainer into data.json.

Usage, with the NWQLib environment and a checkout of the NWQLib repository:
    python nwqlib/extract_data.py /path/to/nwqlib

The heat-plate solve, its accuracy sweep and the ring planning are recomputed with the
public NWQLib workflow, as in examples/qls_linear_system_intro.ipynb and the section "Plan and
estimate beyond simulation" of docs/algorithms/qls.md. Together they take a few seconds.
The H4 ADAPT-GCIM iterations, their circuit count with exact outcome probabilities and the
reanalysis with other overlap cutoffs are read from the stored outputs of examples/gcim_lanczos_qpe_eigenvalue_intro.ipynb, and the predicted and compiled CX counts of
four notebooks from the table in docs/why_nwqlib.md.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().with_name("data.json")

from nwqlib import LinearSystem, estimate, plan, prepare, solve  # noqa: E402
from nwqlib.algorithms import QLS  # noqa: E402
from nwqlib.operators import PeriodicStencil, operator_input  # noqa: E402
from nwqlib.problems import ingest_product  # noqa: E402
from nwqlib.resources import ResourceContext  # noqa: E402


def cx_estimate(selected):
    return float(estimate(selected, context=ResourceContext(basis="cx")).quantity("cx").fact.value.value)


def plate():
    """Steady heat in a 4 x 4 plate with two heaters, exactly as in qls_linear_system_intro."""
    grid, heaters = 4, {(1, 1): 1.0, (2, 3): 0.5}
    h = 1 / (grid + 1)
    chain = 2 * np.eye(grid) - np.eye(grid, k=1) - np.eye(grid, k=-1)
    A = np.kron(chain, np.eye(grid)) + np.kron(np.eye(grid), chain)
    source = np.zeros((grid, grid))
    for (row, column), power in heaters.items():
        source[row, column] = power
    b = h**2 * source.ravel()
    problem = LinearSystem(A=A, b=b)
    reference = np.linalg.solve(A, b)

    selected = plan(problem, method=QLS(epsilon_inv=0.01), seed=7)
    result = solve(selected, progress=False)
    x = np.asarray(result.x)
    rec = selected.reconstruction
    prepared = prepare(selected, progress=False)
    with prepared.run:
        compiled = prepared.inspect_resources(
            transpile_options={"basis_gates": ["cx", "u"], "optimization_level": 1, "seed_transpiler": 7})

    sweep = []
    for epsilon in (0.1, 0.05, 0.02, 0.01, 0.005, 0.002):
        candidate = plan(problem, method=QLS(epsilon_inv=epsilon), seed=7)
        run = solve(candidate, progress=False)
        sweep.append(dict(epsilon=epsilon, degree=candidate.reconstruction.degree, cx=cx_estimate(candidate),
                          error=float(np.linalg.norm(np.asarray(run.x) - reference) / np.linalg.norm(reference)),
                          success=float(run.algorithm_success_mass)))

    return dict(
        grid=grid, heaters=[[r, c, p] for (r, c), p in heaters.items()],
        x=x.real.tolist(), max_imag=float(np.abs(x.imag).max()), reference=reference.tolist(),
        relative_error=float(np.linalg.norm(x - reference) / np.linalg.norm(reference)),
        success=float(result.algorithm_success_mass),
        encoding=rec.encoding_family, alpha=float(rec.alpha), kappa_A=float(rec.condition_number),
        kappa=float(rec.kappa_be), degree=int(rec.degree), qubits=int(rec.width),
        system_qubits=int(np.log2(rec.padded_dimension)),
        polynomial_bound=float(rec.polynomial.certificate), rescale=float(rec.polynomial.rescale),
        cx_estimate=cx_estimate(selected), cx_compiled=int(compiled["operations"].get("cx", 0)),
        compiled_depth=int(compiled["depth"]), compiled_single=int(compiled["operations"].get("u", 0)),
        sweep=sweep)


def ring():
    """Compact planning of a periodic stencil, as in docs/algorithms/qls.md. Nothing is solved."""
    rows = []
    for q in (10, 20, 40):
        A = operator_input(PeriodicStencil(q, mass=0.1, diffusion=0.1))
        b = ingest_product([[np.cos(0.3 + 0.1 * j), np.sin(0.3 + 0.1 * j)] for j in range(q)])
        selected = plan(LinearSystem(A=A, b=b), method=QLS(epsilon_inv=0.01), seed=7)
        workload = estimate(selected, context=ResourceContext(basis="cx"))
        rows.append(dict(q=q, kappa=float(selected.reconstruction.kappa_be), degree=int(selected.reconstruction.degree),
                         qubits=int(workload.quantity("logical_width", location="logical_device").fact.value.numerator),
                         cx=float(workload.quantity("cx").fact.value.value)))
    return rows


def html_tables(notebook):
    """Rows of every HTML table in the stored outputs of a notebook, as lists of cell strings."""
    cells = json.loads(notebook.read_text())["cells"]
    tables = []
    for cell in cells:
        for output in cell.get("outputs", []):
            text = "".join(output.get("data", {}).get("text/html", []))
            for table in re.findall(r"<table>(.*?)</table>", text, re.S):
                rows = re.findall(r"<tr>(.*?)</tr>", table, re.S)
                tables.append([[html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                                for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)] for r in rows])
    return tables


def h4():
    tables = html_tables(REPO / "examples" / "gcim_lanczos_qpe_eigenvalue_intro.ipynb")
    refs = next(t for t in tables if t[0][0] == "Quantity" and any(r[0] == "CCSD error" for r in t))
    steps = next(t for t in tables if t[0][:3] == ["Iteration", "Generator added", "Error [mHa]"])
    counts = next(t for t in tables if t[0] == ["Iteration", "Basis states", "Cumulative circuits"])
    cutoffs = next(t for t in tables if t[0][:2] == ["Overlap cutoff", "Kept directions"])
    ref = {r[0]: float(r[1].replace("−", "-")) for r in refs[1:] if r[0].endswith("error")}
    return dict(hf=ref["Hartree–Fock error"], mp2=ref["MP2 error"], ccsd=ref["CCSD error"],
                iterations=[dict(iteration=int(r[0]), generator=r[1], error=float(r[2])) for r in steps[1:]],
                circuits=int(counts[-1][2].replace(",", "")),
                reanalysis=[dict(cutoff=float(r[0]), kept=int(r[1]), error=float(r[3])) for r in cutoffs[1:]])


def cx_table():
    text = (REPO / "docs" / "why_nwqlib.md").read_text()
    rows = re.findall(r"^\| `(\w+)` \| ([\d,]+)(?:, an? (\w+(?: \w+)?))? \| ([\d,]+) \|$", text, re.M)
    return [dict(notebook=n, estimate=int(e.replace(",", "")), kind=k or "estimate", compiled=int(c.replace(",", "")))
            for n, e, k, c in rows]


def main():
    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    data = dict(nwqlib_commit=sha, plate=plate(), ring=ring(), h4=h4(), cx_table=cx_table())
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in data["plate"].items() if k not in ("x", "reference")}, indent=1))
    print(json.dumps(data["ring"], indent=1))
    print(json.dumps(data["h4"], indent=1, ensure_ascii=False))
    print(json.dumps(data["cx_table"], indent=1))


if __name__ == "__main__":
    main()
