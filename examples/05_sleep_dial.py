"""Turn the 'sleep dial' (adaptation, pA) and watch PCI fall. About 2 minutes per level."""
from zapzip import Cortex, pci

for b in (0, 20, 40, 60):
    ctx = Cortex(state=b, seed=21)            # a number = adaptation strength in pA
    r = pci(ctx.zap(n_pulses=40, seed=1), n_pre=300)
    print(f"adaptation {b:3d} pA   PCI {r.value:.2f}   regions reached {r.channels_active}/20", flush=True)
