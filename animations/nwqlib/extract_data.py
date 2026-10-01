"""Collect the NWQLib numbers plotted in the explainer into data.json.

Usage, from a checkout of the NWQLib repository with its Python environment:
    python /path/to/animations/nwqlib/extract_data.py /path/to/NWQLib

Everything is recomputed with the public NWQLib workflow and takes well under a minute on a laptop.
The heat-plate solve follows examples/qls_linear_system_intro.ipynb: the plan, the predicted and
compiled CX counts, the solve on Aer and the check against numpy. The scaling follows the QLS part of
examples/resource_estimation_at_scale.ipynb: the screened Poisson equation on a ring of 2**q sites with a
product-state right-hand side, compiled at 4 to 16 system qubits and only planned and estimated above.
"""
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import numpy as np

REPO = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().with_name("data.json")

import nwqlib  # noqa: E402
import qiskit  # noqa: E402
import qiskit_aer  # noqa: E402
from nwqlib import LinearSystem, estimate, plan, prepare, solve  # noqa: E402
from nwqlib.algorithms import QLS  # noqa: E402
from nwqlib.algorithms.qls import QLSVerification  # noqa: E402
from nwqlib.execution import ExecutionLimits  # noqa: E402
from nwqlib.operators import PeriodicStencil  # noqa: E402
from nwqlib.problems import ingest_product  # noqa: E402
from nwqlib.resources import ResourceContext  # noqa: E402

CX = ResourceContext(basis="cx")
LEVEL_1 = {"basis_gates": ["cx", "u"], "optimization_level": 1, "seed_transpiler": 7}
LEVEL_0 = {"basis_gates": ["cx", "u"], "optimization_level": 0, "seed_transpiler": 7, "approximation_degree": 1.0}


def count(quantity):
    """A resource quantity as a number, or None when the estimate leaves it unavailable."""
    if quantity.fact.availability != "concrete":
        return None
    value = quantity.fact.value
    return int(value.numerator) if value.kind == "rational" else float(value.value)


def plate():
    """Steady heat in a 4 x 4 plate with two heaters, as in qls_linear_system_intro."""
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

    started = perf_counter()
    selected = plan(problem, method=QLS(epsilon_inv=0.01), seed=7)
    planned = perf_counter()
    predicted = estimate(selected, context=CX)
    result = solve(selected, progress=False)
    solved = perf_counter()
    x = np.asarray(result.x)
    rec = selected.reconstruction

    check, _ = result.verify(checks=QLSVerification(comparisons=("spectral_domain", "inverse_relative_error", "inverse_success")))
    checked = {item.frame.metric: item.fact.value.value for application in check.applications for item in application.facts}
    prepared = prepare(selected, progress=False)
    with prepared.run:
        compiled = prepared.inspect_resources(transpile_options=LEVEL_1)

    labels = {q.metric: q.interpretation for q in predicted.quantities}
    return dict(
        grid=grid, heaters=[[r, c, p] for (r, c), p in heaters.items()],
        A_nonzeros=int(np.count_nonzero(A)),
        x=x.real.tolist(), max_imag=float(np.abs(x.imag).max()), reference=reference.tolist(),
        relative_error=float(np.linalg.norm(x - reference) / np.linalg.norm(reference)),
        method_allowance=float(checked["method_allowance"]),
        error_over_allowance=float(checked["relative_error_over_method_allowance"]),
        success=float(result.algorithm_success_mass),
        encoding=rec.encoding_family, alpha=float(rec.alpha), sigma_min=float(rec.sigma_min), sigma_max=float(rec.sigma_max),
        kappa_A=float(rec.condition_number), kappa=float(rec.kappa_be), polynomial_kappa=float(rec.polynomial_kappa),
        eigenvalues_over_alpha=(np.linalg.eigvalsh(A) / rec.alpha).tolist(),
        degree=int(rec.degree), chebyshev=[float(c) for c in rec.polynomial.coefficients],
        polynomial_bound=float(rec.polynomial.certificate), rescale=float(rec.polynomial.rescale),
        phases=[float(p) for p in rec.phase_solution],
        qubits=int(rec.width), system_qubits=int(np.log2(rec.padded_dimension)),
        cx_estimate=count(predicted.quantity("cx")), cx_label=labels["cx"],
        calls=count(predicted.quantity("calls")),
        depth_estimate=count(predicted.quantity("logical_depth")), depth_label=labels["logical_depth"],
        t_label=labels["t"],
        cx_compiled=int(compiled["operations"].get("cx", 0)), compiled_depth=int(compiled["depth"]),
        plan_seconds=planned - started, plan_estimate_solve_seconds=solved - started)


def screened_poisson(q):
    """A = I + (2I - S - S^dagger)/4 on a ring of 2**q sites and a product-state b, as in resource_estimation_at_scale."""
    b = ingest_product([[np.cos(0.3 + 0.1 * j), np.sin(0.3 + 0.1 * j)] for j in range(q)])
    return LinearSystem(A=PeriodicStencil(q, mass=1.0, diffusion=0.25), b=b)


def scaling():
    """QLS on the ring: compiled at small sizes, planned and estimated up to 100 system qubits. Nothing is simulated."""
    compiled = []
    for q in (4, 6, 8, 12, 16):
        selected = plan(screened_poisson(q), method=QLS(epsilon_inv=0.01), seed=7)
        law = estimate(selected, context=CX).quantity("cx")
        prepared = prepare(selected, progress=False, limits=ExecutionLimits(max_simulation_qubits=32))  # builds, runs nothing
        with prepared.run:
            inventory = prepared.inspect_resources(max_operations=10_000_000, transpile_options=LEVEL_0)
        compiled.append(dict(q=q, law=count(law), label=law.interpretation, compiled=int(inventory["operations"].get("cx", 0)),
                             qubits=int(inventory["num_qubits"])))
    planned = []
    for q in (4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 100):
        started = perf_counter()
        selected = plan(screened_poisson(q), method=QLS(epsilon_inv=0.01), seed=7)
        workload = estimate(selected, context=CX)
        seconds = perf_counter() - started
        rec = selected.reconstruction
        planned.append(dict(q=q, qubits=count(workload.quantity("logical_width", location="logical_device")),
                            cx=count(workload.quantity("cx")), label=workload.quantity("cx").interpretation,
                            degree=int(rec.degree), alpha=float(rec.alpha), kappa=float(rec.kappa_be),
                            encoding=rec.encoding_family, seconds=seconds))
    return dict(compiled=compiled, planned=planned)


def main():
    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    data = dict(nwqlib_commit=sha, nwqlib_version=nwqlib.__version__, qiskit=qiskit.__version__,
                qiskit_aer=qiskit_aer.__version__, python=platform.python_version(),
                machine=cpu or platform.machine(), plate=plate(), scaling=scaling())
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    summary = {k: v for k, v in data["plate"].items() if k not in ("x", "reference", "chebyshev", "phases", "eigenvalues_over_alpha")}
    print(json.dumps({k: v for k, v in data.items() if k not in ("plate", "scaling")}, indent=1))
    print(json.dumps(summary, indent=1))
    print(json.dumps(data["scaling"], indent=1))


if __name__ == "__main__":
    main()
