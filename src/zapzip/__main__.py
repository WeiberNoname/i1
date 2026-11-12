"""Command line:
  zapzip pci recording.npy --pre 300 [--post 300] [--alpha 0.01]
      recording.npy holds an array (trials, channels, samples); stimulus at sample --pre
  zapzip demo [--state wake|sleep|both] [--pulses 40] [--seed 0]
      builds the simulated cortex, zaps it and prints PCI per state
"""
import argparse
import sys
import numpy as np
from . import pci


def main(argv=None):
    ap = argparse.ArgumentParser(prog="zapzip", description="Perturbational complexity index tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pci", help="PCI of a saved recording")
    a.add_argument("file"); a.add_argument("--pre", type=int, required=True)
    a.add_argument("--post", type=int); a.add_argument("--alpha", type=float, default=0.01)
    a.add_argument("--save-binary", help="optional .npy path for the significance matrix")
    d = sub.add_parser("demo", help="zap the simulated cortex")
    d.add_argument("--state", default="both", choices=["wake", "sleep", "both"])
    d.add_argument("--pulses", type=int, default=40); d.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if args.cmd == "pci":
        x = np.load(args.file)
        r = pci(x, n_pre=args.pre, n_post=args.post, alpha=args.alpha)
        print(f"PCI = {r.value:.3f}  (active channels {r.channels_active}/{r.significant.shape[0]}, "
              f"significant fraction {r.significant.mean():.3f}, threshold z = {r.threshold:.2f})")
        if args.save_binary:
            np.save(args.save_binary, r.significant)
        return 0

    from .sim import Cortex
    states = ["wake", "sleep"] if args.state == "both" else [args.state]
    for s in states:
        print(f"building {s} cortex (10,000 neurons)...", file=sys.stderr, flush=True)
        ctx = Cortex(state=s, seed=args.seed)
        r = pci(ctx.zap(n_pulses=args.pulses, seed=args.seed), n_pre=300)
        print(f"{s:5s}  PCI = {r.value:.3f}  regions reached {r.channels_active}/20")
    return 0


if __name__ == "__main__":
    sys.exit(main())
