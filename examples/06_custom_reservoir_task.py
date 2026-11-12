"""Use the cortex as a reservoir computer for your own task.

Task: two input regions receive random on/off pulses every 20 ms. A linear readout
must report whether region 0 was ON one step ago (a 20 ms memory task), using only
the network's spiking activity. About 2 minutes.
"""
import numpy as np
from zapzip import Cortex

rng = np.random.default_rng(0)
T = 3000                                    # 3000 steps x 20 ms = 60 s
bits = rng.integers(0, 2, size=(T, 2))      # on/off for input regions 0 and 1
inputs = np.zeros((T, 20)); inputs[:, :2] = 6.0 * bits      # Hz per input fibre

ctx = Cortex(state="sleep", seed=21)        # try "wake" too and compare
X = ctx.reservoir_states(inputs)            # (T, 2000) readout features

target = np.roll(bits[:, 0], 1)             # region 0's input one step ago
Xb = np.c_[(X - X.mean(0)) / (X.std(0) + 1e-6), np.ones(T)]
tr, te = slice(50, 2100), slice(2100, T)
w = np.linalg.solve(Xb[tr].T @ Xb[tr] + 100 * np.eye(Xb.shape[1]), Xb[tr].T @ target[tr])
acc = ((Xb[te] @ w > 0.5) == (target[te] > 0.5)).mean()
print(f"held-out accuracy {acc:.2f} (chance 0.50)")
