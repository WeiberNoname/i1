"""Zap a wake-like and a sleep-like cortex and compare PCI and memory (about 10 minutes)."""
from zapzip import Cortex, pci

for state in ("wake", "sleep"):
    ctx = Cortex(state=state, seed=21)
    r = pci(ctx.zap(n_pulses=40, seed=1), n_pre=300)
    cap, _ = Cortex(state=state, seed=21).memory_capacity(seconds=60)
    print(f"{state:5s}  PCI {r.value:.2f}  regions {r.channels_active}/20  memory capacity {cap:.2f}")
