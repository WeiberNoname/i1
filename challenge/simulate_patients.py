"""The 'world': builds every patient and records its response to 40 pulses.

This is the only script that reads the hidden answers. It writes recordings/<id>.npy,
shaped (pulses, regions, ms), stimulus at 300 ms. About 2 minutes per patient.

    python simulate_patients.py            # all 24 patients
"""
import json
import os
import sys
import time
import numpy as np
from zapzip import Cortex

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "recordings")


def record(p):
    path = os.path.join(OUT, f"{p['id']}.npy")
    if os.path.exists(path):
        return
    t = time.time()
    ctx = Cortex(state=p["state"], seed=p["seed"], nu_ext=p["nu_ext"])
    trials = ctx.zap(n_pulses=40, seed=p["seed"]).astype(np.float32)
    np.save(path, trials)
    print(f"{p['id']} recorded ({time.time() - t:.0f}s)", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cal = json.load(open(os.path.join(HERE, "calibration_patients.json")))
    blind = json.load(open(os.path.join(HERE, "sealed", "answers.json")))
    for p in cal + blind:
        record(p)
    sys.exit(0)
