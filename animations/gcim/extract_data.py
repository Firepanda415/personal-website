"""Copy the plotted ADAPT-GCIM convergence data from the QuGCM repository into data.json.

Usage: python extract_data.py /path/to/QuGCM

The curves are |E - E_exact| per ADAPT iteration for H6 at an H-H distance of 5.0 Å
(STO-3G), the case in Fig. 4 and Table 3 of npj Quantum Inf. 10, 127 (2024).
"""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

SOURCES = {
    "adapt_gcim": ("ADAPT-GCIM/Paper_Data/ADAPT-GCIM/GCM_H65A_tp4.zip", "GCM_H65A_tp4/GCM_DIFF.npy"),
    "adapt_vqe": ("ADAPT-GCIM/Paper_Data/ADAPT-VQE-GCIM/GV_H65A.zip", "GV_H65A/VQE_DIFF.npy"),
}


def main(repo):
    repo = Path(repo)
    data, sources = {}, {}
    for key, (archive, member) in SOURCES.items():
        path = repo / archive
        with zipfile.ZipFile(path) as z:
            values = np.load(io.BytesIO(z.read(member)), allow_pickle=True)
        data[key] = [float(abs(v)) for v in np.asarray(values, float)]
        sources[f"{archive}:{member}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    data["sources"] = sources
    out = Path(__file__).with_name("data.json")
    out.write_text(json.dumps(data, indent=1))
    print(f"wrote {out}: {len(data['adapt_gcim'])} ADAPT-GCIM and {len(data['adapt_vqe'])} ADAPT-VQE iterations")


if __name__ == "__main__":
    main(sys.argv[1])
