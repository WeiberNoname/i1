"""The 'world' for Challenge 2: builds the 16 blind patients and records 40 pulses each.
Only this script and score.py read sealed/answers.json. About 70 s per patient."""
import json
import os
import time
import numpy as np
from zapzip import Cortex

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "recordings")

KIND_PARAMS = {
    "wake": dict(state="wake"),
    "sleep": dict(state="sleep"),
    "disconnected_active": dict(state="wake", KE_lr=0, KE_loc=400),
    "quiet_wake": dict(state="wake", Qi=9e-9),
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for p in json.load(open(os.path.join(HERE, "sealed", "answers.json"))):
        path = os.path.join(OUT, f"{p['id']}.npy")
        if os.path.exists(path):
            continue
        t = time.time()
        ctx = Cortex(seed=p["seed"], nu_ext=p["nu_ext"], **KIND_PARAMS[p["kind"]])
        np.save(path, ctx.zap(n_pulses=40, seed=p["seed"]).astype(np.float32))
        print(f"{p['id']} recorded ({time.time() - t:.0f}s)", flush=True)
