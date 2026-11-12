"""Plot the binary matrix that PCI compresses (needs matplotlib)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from zapzip import pci

rng = np.random.default_rng(1)
x = rng.normal(size=(50, 16, 500))
for ch in range(16):
    x[:, ch, 200 + 6 * ch:240 + 6 * ch] += 2.0          # a travelling wave across channels

r = pci(x, n_pre=200)
plt.figure(figsize=(7, 3))
plt.imshow(r.significant, aspect="auto", cmap="Greys", interpolation="nearest")
plt.xlabel("samples after stimulus"); plt.ylabel("channel")
plt.title(f"Significant response, PCI = {r.value:.2f}")
plt.tight_layout(); plt.savefig("significance.png", dpi=120)
print("saved significance.png;", r)
