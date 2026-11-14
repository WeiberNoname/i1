"""The 'clinic': labels patients from their recordings only.

Reads recordings/*.npy and calibration_patients.json (known labels). It never opens
sealed/. Writes decisions.json with every marker value and label.

    python monitor.py
"""
import json
import os
import numpy as np
from zapzip import pci

HERE = os.path.dirname(os.path.abspath(__file__))
N_PRE = 300


def markers(pid):
    x = np.load(os.path.join(HERE, "recordings", f"{pid}.npy"))
    r = pci(x, n_pre=N_PRE)
    return dict(pci=round(r.value, 4), channels_active=r.channels_active,
                rate_hz=round(float(x[:, :, :N_PRE].mean()), 3))


def cutoff(conscious, unconscious):
    """Midpoint between the classes if they separate, else the best-accuracy point."""
    lo, hi = max(unconscious), min(conscious)
    if hi > lo:
        return (lo + hi) / 2, True
    cands = sorted(conscious + unconscious)
    best = max(((a + b) / 2 for a, b in zip(cands, cands[1:])),
               key=lambda c: sum(v > c for v in conscious) + sum(v <= c for v in unconscious))
    return best, False


if __name__ == "__main__":
    cal = json.load(open(os.path.join(HERE, "calibration_patients.json")))
    blind = json.load(open(os.path.join(HERE, "blind_patients.json")))
    calm = {p["id"]: dict(markers(p["id"]), state=p["state"]) for p in cal}
    cuts = {}
    for m in ("pci", "rate_hz"):
        w = [v[m] for v in calm.values() if v["state"] == "wake"]
        s = [v[m] for v in calm.values() if v["state"] == "sleep"]
        c, sep = cutoff(w, s)
        cuts[m] = dict(cutoff=round(c, 4), separable_in_calibration=sep)
    out = {"cutoffs": cuts, "calibration": calm, "blind": {}}
    for p in blind:
        mk = markers(p["id"])
        mk["label_by_pci"] = "conscious-like" if mk["pci"] > cuts["pci"]["cutoff"] else "unconscious-like"
        mk["label_by_rate"] = "conscious-like" if mk["rate_hz"] > cuts["rate_hz"]["cutoff"] else "unconscious-like"
        out["blind"][p["id"]] = mk
        print(p["id"], mk, flush=True)
    json.dump(out, open(os.path.join(HERE, "decisions.json"), "w"), indent=1)
    print("cutoffs", cuts)
