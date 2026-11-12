"""Lempel-Ziv complexity of any signal: binarize around the median, then count LZ76 words.

Normalized LZ is ~1 for white noise and close to 0 for regular signals.
"""
import numpy as np
from zapzip import lz76


def lz_normalized(signal):
    b = (np.asarray(signal) > np.median(signal)).astype(int)
    n = b.size
    return lz76(b) * np.log2(n) / n


t = np.linspace(0, 10, 4000)
rng = np.random.default_rng(0)
signals = {
    "sine wave": np.sin(2 * np.pi * 3 * t),
    "sine + some noise": np.sin(2 * np.pi * 3 * t) + 0.5 * rng.normal(size=t.size),
    "white noise": rng.normal(size=t.size),
}
for name, s in signals.items():
    print(f"{name:18s} normalized LZ = {lz_normalized(s):.3f}")
