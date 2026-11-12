"""PCI on any evoked recording: here a synthetic 32-channel dataset.

Replace `make_fake_recording()` with your own array shaped (trials, channels, samples).
"""
import numpy as np
from zapzip import pci


def make_fake_recording(varied=True, n_trials=60, n_ch=32, n_samp=600, stim=300, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n_trials, n_ch, n_samp))
    for ch in range(n_ch):
        if varied:      # each channel answers with its own delay and duration
            start = stim + 5 + 7 * (ch % 9)
            x[:, ch, start:start + 20 + 3 * (ch % 5)] += 2.5
        else:           # every channel answers in exactly the same way
            x[:, ch, stim + 10:stim + 60] += 2.5
    return x


for label, varied in [("varied response", True), ("uniform response", False)]:
    r = pci(make_fake_recording(varied), n_pre=300, n_post=300)
    print(f"{label:17s} {r}")
