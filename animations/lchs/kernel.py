"""Kernel functions plotted in the explainer, in the paper's hbar = 2 convention."""
import json
from pathlib import Path

import numpy as np

R, R_PRIME, BETA = 1.6, 0.25, 0.5
SIGMA, SIGMA_PRIME = np.exp(R), np.exp(R_PRIME)

DATA = json.loads(Path(__file__).with_name("data.json").read_text())
C = np.array(DATA["coefficients_re"]) + 1j * np.array(DATA["coefficients_im"])


def g_beta(k, beta=BETA):
    """Generalized exact-LCHS kernel, Eq. (6), principal branch."""
    k = np.asarray(k, dtype=float)
    return np.exp(2**beta) / (2 * np.pi * (1 - 1j * k) * np.exp((1 + 1j * k) ** beta))


def hermite_functions(n_max, y):
    """Normalized Hermite functions h_0..h_{n_max-1} by the stable three-term recurrence."""
    h = np.zeros((n_max, y.size))
    h[0] = np.pi**-0.25 * np.exp(-y**2 / 2)
    if n_max > 1:
        h[1] = np.sqrt(2) * y * h[0]
    for n in range(1, n_max - 1):
        h[n + 1] = np.sqrt(2 / (n + 1)) * y * h[n] - np.sqrt(n / (n + 1)) * h[n - 1]
    return h


def squeezed_fock(n_max, x, sigma=SIGMA_PRIME):
    """phi_{n,r'}(x) = (sqrt(2) sigma')^(-1/2) h_n(x / (sqrt(2) sigma'))."""
    s = np.sqrt(2) * sigma
    return hermite_functions(n_max, x / s) / np.sqrt(s)


def phi_r(x):
    """Postselection squeezed vacuum, width sigma = e^r."""
    return (2 * np.pi * SIGMA**2) ** -0.25 * np.exp(-x**2 / (4 * SIGMA**2))


def psi_N(x):
    return C @ squeezed_fock(C.size, x)


def overlap_scale(x):
    """alpha_{N,r} = 1 / <phi_r | psi_N>, by quadrature on the grid x."""
    return 1 / np.trapezoid(phi_r(x) * psi_N(x), x)
