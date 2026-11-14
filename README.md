# zapzip

**Measure how complex a brain's (or a model's) electrical echo is — and play with a small simulated cortex that you can put to sleep, zap, and use as a computer.**

[![tests](https://github.com/WeiberNoname/i1/actions/workflows/tests.yml/badge.svg)](https://github.com/WeiberNoname/i1/actions/workflows/tests.yml)

`zapzip` does two things:

1. **PCI for any recording.** The *Perturbational Complexity Index* (Casali et al., 2013) estimates the level of consciousness from the brain's response to a brief perturbation: zap, record, keep what differs from baseline, compress it. A response that spreads widely *and* differs from channel to channel compresses poorly and scores high. `zapzip.pci()` computes it from any array shaped `(trials, channels, samples)` — EEG, MEG, intracranial electrodes, cultured-neuron arrays or simulations.
2. **A cortex to try it on.** `zapzip.Cortex` is a 10,000-neuron spiking network (20 regions, adaptive exponential integrate-and-fire neurons). One parameter, neuronal adaptation, switches it between wake-like and sleep-like states. You can zap it, sweep a "sleep dial", measure memory, or feed it inputs and train your own readout.

```
  zap  ──►  record  ──►  threshold  ──►  binarize  ──►  compress  ──►  PCI
 (pulse)   (trials ×     (bootstrap     (1 = differs    (Lempel–Ziv,
           channels ×     of baseline)   from baseline)  ÷ entropy)
           time)
```

---

## Contents

- [Install](#install)
- [Quick start](#quick-start)
- [Examples](#examples)
  1. [PCI on your own data](#1-pci-on-your-own-data)
  2. [From MNE-Python epochs (EEG/TMS-EEG)](#2-from-mne-python-epochs-eegtms-eeg)
  3. [Command line](#3-command-line)
  4. [See what PCI compresses](#4-see-what-pci-compresses)
  5. [Lempel–Ziv complexity of any signal](#5-lempelziv-complexity-of-any-signal)
  6. [Wake vs sleep in the simulated cortex](#6-wake-vs-sleep-in-the-simulated-cortex)
  7. [The sleep dial](#7-the-sleep-dial)
  8. [Your own task: the cortex as a reservoir computer](#8-your-own-task-the-cortex-as-a-reservoir-computer)
  9. [Memory capacity](#9-memory-capacity)
- [API reference](#api-reference)
- [How it was checked](#how-it-was-checked)
- [Limits — read before using on real data](#limits--read-before-using-on-real-data)
- [Blind consciousness monitor challenge](challenge/)
- [References](#references)

---

## Install

```bash
# PCI only (needs just numpy)
pip install "git+https://github.com/WeiberNoname/i1.git"

# PCI + simulator (adds numba)
pip install "zapzip[sim] @ git+https://github.com/WeiberNoname/i1.git"
```

From a clone, for development:

```bash
git clone https://github.com/WeiberNoname/i1.git
cd i1
pip install -e ".[sim,test]"
pytest -m "not slow"          # 13 fast tests, about a minute
pytest -m slow                # re-derives the wake > sleep result, about 3 minutes
```

Python 3.9 or newer.

## Quick start

```python
import numpy as np
from zapzip import pci

trials = np.load("evoked.npy")            # shape (trials, channels, samples), stimulus at sample 300
result = pci(trials, n_pre=300, n_post=300)

print(result)                             # PCIResult(value=0.412, channels_active=12/20, significant_fraction=0.031)
result.value                              # the PCI number
result.significant                        # bool matrix (channels × post-stimulus samples) that was compressed
result.channels_active                    # how many channels responded at all
```

## Examples

Every example below is a runnable script in [`examples/`](examples/). The outputs shown are what those scripts printed when they were tested.

### 1. PCI on your own data

[`examples/01_pci_on_your_data.py`](examples/01_pci_on_your_data.py) builds two synthetic 32-channel recordings with the same amount of response. In one, each channel answers at its own delay. In the other, every channel answers identically.

```python
from zapzip import pci

r_varied  = pci(varied_recording,  n_pre=300, n_post=300)
r_uniform = pci(uniform_recording, n_pre=300, n_post=300)
```

```
varied response   PCIResult(value=0.209, channels_active=32/32, significant_fraction=0.086)
uniform response  PCIResult(value=0.008, channels_active=32/32, significant_fraction=0.167)
```

The uniform response has *more* significant points but scores near zero: it is all the same pattern, so it compresses away. That is the core idea of PCI.

### 2. From MNE-Python epochs (EEG/TMS-EEG)

[`examples/07_mne_epochs.py`](examples/07_mne_epochs.py). With your own cleaned `mne.Epochs` (stimulus at t = 0):

```python
import numpy as np
from zapzip import pci

x = epochs.get_data()                                            # (trials, channels, samples)
n_pre = int(np.sum(epochs.times < 0))                            # samples before the stimulus
n_post = int(np.sum((epochs.times >= 0) & (epochs.times < 0.3)))  # analyse 0–300 ms
result = pci(x, n_pre=n_pre, n_post=n_post)
```

Filtering, artifact removal (for TMS: the pulse artifact and muscle responses) and channel selection or source reconstruction happen **before** this step and are up to you.

### 3. Command line

Save your array as `.npy` and run:

```bash
zapzip pci evoked.npy --pre 300 --post 300
```

```
PCI = 0.209  (active channels 32/32, significant fraction 0.086, threshold z = 0.61)
```

Options: `--alpha 0.01` (significance level), `--save-binary sig.npy` (writes the binary matrix).

Simulated demo (about 5 minutes):

```bash
zapzip demo                 # both states
zapzip demo --state sleep --pulses 60 --seed 3
```

### 4. See what PCI compresses

[`examples/03_plot_significance.py`](examples/03_plot_significance.py) (needs `matplotlib`):

```python
import matplotlib.pyplot as plt
from zapzip import pci

r = pci(x, n_pre=200)
plt.imshow(r.significant, aspect="auto", cmap="Greys", interpolation="nearest")
plt.xlabel("samples after stimulus"); plt.ylabel("channel")
plt.title(f"PCI = {r.value:.2f}")
```

Looking at this matrix is the best sanity check. A single block means a uniform response. A scattered or staggered pattern means a differentiated one.

### 5. Lempel–Ziv complexity of any signal

`lz76` works on any binary sequence. [`examples/02_lempel_ziv_on_signals.py`](examples/02_lempel_ziv_on_signals.py) binarizes signals around their median:

```python
import numpy as np
from zapzip import lz76

def lz_normalized(signal):
    b = (signal > np.median(signal)).astype(int)
    return lz76(b) * np.log2(b.size) / b.size
```

```
sine wave          normalized LZ = 0.024
sine + some noise  normalized LZ = 0.586
white noise        normalized LZ = 1.032
```

This is useful for spontaneous EEG, heart-rate series or game telemetry: anything where you want "how predictable is this?" as a number.

### 6. Wake vs sleep in the simulated cortex

```python
from zapzip import Cortex, pci

for state in ("wake", "sleep"):
    ctx = Cortex(state=state, seed=21)               # builds 10,000 neurons
    r = pci(ctx.zap(n_pulses=40), n_pre=300)         # 40 pulses into region 0
    print(state, r)
```

```
wake  PCIResult(value=0.394, channels_active=9/20, significant_fraction=0.014)
sleep PCIResult(value=0.202, channels_active=19/20, significant_fraction=0.053)
```

As in human TMS-EEG, the sleep-like response spreads *further* but scores *lower*: every region bursts and falls silent together. Full script: [`examples/04_wake_vs_sleep.py`](examples/04_wake_vs_sleep.py).

### 7. The sleep dial

`state` also accepts a number: the adaptation strength in pA (0 = wake, 60 = sleep). [`examples/05_sleep_dial.py`](examples/05_sleep_dial.py):

```python
for b in (0, 20, 40, 60):
    ctx = Cortex(state=b, seed=21)
    r = pci(ctx.zap(n_pulses=40, seed=1), n_pre=300)
    print(f"adaptation {b:3d} pA   PCI {r.value:.2f}   regions reached {r.channels_active}/20")
```

```
adaptation   0 pA   PCI 0.41   regions reached 9/20
adaptation  20 pA   PCI 0.25   regions reached 17/20
adaptation  40 pA   PCI 0.24   regions reached 18/20
adaptation  60 pA   PCI 0.23   regions reached 20/20
```

You can also change state on a running network with `ctx.set_state("sleep")` or `ctx.set_state(30)`.

### 8. Your own task: the cortex as a reservoir computer

Feed any input sequence and train a readout on the network's activity. [`examples/06_custom_reservoir_task.py`](examples/06_custom_reservoir_task.py) asks whether region 0 was ON one step (20 ms) ago:

```python
import numpy as np
from zapzip import Cortex

T = 3000                                            # 3000 steps × 20 ms = 60 s
bits = np.random.default_rng(0).integers(0, 2, size=(T, 2))
inputs = np.zeros((T, 20)); inputs[:, :2] = 6.0 * bits    # Hz per input fibre, per region

ctx = Cortex(state="sleep", seed=21)
X = ctx.reservoir_states(inputs)                    # (T, 2000) features, one row per step
# ...train any readout on X (ridge regression in the script)
```

```
held-out accuracy 0.64 (chance 0.50)
```

`reservoir_states` takes inputs shaped `(steps, regions)` in Hz per input fibre, plus `step_s` (default 0.02 s), `n_features` (default 2000) and `tau_s` (default 0.02 s). Plug in your own task: classify patterns, predict a signal, drive a game paddle.

### 9. Memory capacity

```python
ctx = Cortex(state="sleep", seed=21)
capacity, r2_by_lag = ctx.memory_capacity(seconds=90)
```

This is the standard linear memory capacity (Jaeger, 2001): how well a ridge readout recovers a random input from 1 to 15 steps back, summed. In our research runs it was about 0.06 in the wake-like state and about 0.30 in the sleep-like state. Adaptation acts as a short memory trace, so the state with the lower PCI remembers more.

## Application: a blind consciousness monitor

[`challenge/`](challenge/) uses the tool on a problem it was built for. 24 simulated patients have hidden wake/sleep states and individual differences. Predictions were pre-registered on GitHub before any run, and the answers were sealed. PCI separated the 16 blind patients perfectly and labelled 15 of 16 correctly. A plain firing-rate marker also scored 16 of 16, so the challenge shows the pipeline works but not that PCI beats simpler markers in this model. Full results and what they mean are in the [challenge README](challenge/README.md).

## API reference

| Function / class | Purpose |
| --- | --- |
| `pci(trials, n_pre, n_post=None, alpha=0.01, n_boot=500, seed=0)` | PCI from `(trials, channels, samples)`; returns `PCIResult` |
| `PCIResult` | `.value`, `.significant`, `.threshold`, `.evoked`, `.channels_active` |
| `binarize(trials, n_pre, alpha, n_boot, seed)` | Just the significance step: `(significant, threshold, evoked)` |
| `pci_from_binary(matrix)` | PCI of a binary matrix you made yourself |
| `lz76(sequence)` | Lempel–Ziv 1976 word count of a binary sequence |
| `Cortex(state="wake", seed=0, **params)` | Simulated cortex. `state`: `"wake"`, `"sleep"` or adaptation in pA. Parameters such as `regions`, `KE_lr` (long-range inputs per neuron) and `nu_ext` (background drive) can be overridden. |
| `Cortex.run(seconds, input_hz=None)` | Simulate; returns spike counts per neuron |
| `Cortex.region_rates(counts, seconds)` | Mean excitatory rate per region (Hz) |
| `Cortex.zap(n_pulses=40, region=0, pre_ms=300, post_ms=300, pulse_hz=150, pulse_ms=10, smooth_ms=10, seed=0)` | Perturbation protocol; returns `(pulses, regions, ms)` |
| `Cortex.reservoir_states(inputs_hz, step_s=0.02, n_features=2000, tau_s=0.02, seed=0)` | Readout features for your own tasks |
| `Cortex.memory_capacity(seconds=90, input_regions=(0,1,2,3), max_lag=15)` | `(capacity, r2_per_lag)` |
| `Cortex.set_state(state)` | Change wake/sleep/adaptation on a running network |

Speed: about 2 seconds of CPU per simulated second on 2 cores. The first call compiles the kernel, which takes a few seconds and is cached afterwards.

## How it was checked

- **Lempel–Ziv:** `lz76` gives the textbook answer (Kaspar & Schuster 1987: `0001101001000101` → 6) and identical word counts to the independent [`antropy`](https://github.com/raphaelvallat/antropy) package on random sequences (tested in `tests/test_pci.py`).
- **PCI behaviour:** about 1 for a random binary matrix, about 0 for a uniform block, nothing significant in pure noise, and a channel-specific response scores above an identical-everywhere one.
- **The science result, re-derived through this package:** wake 0.39 versus sleep 0.20 (`pytest -m slow`).
- **The research behind it:** on 6 independently wired networks, PCI was 0.40 ± 0.05 (wake) versus 0.22 ± 0.03 (sleep), and memory capacity was 0.06 versus 0.30, with the same direction in 6 of 6 networks. Freezing adaptation removed the memory gain but not the PCI drop.
- Tests run on every push via GitHub Actions (Python 3.10 and 3.12).

## Limits — read before using on real data

- **This is the original Lempel–Ziv PCI.** The faster state-transition variant (PCIst; Comolatti et al., 2019) is not included.
- **Absolute values are not portable.** Clinical PCI uses source-reconstructed TMS-EEG (thousands of sources, 0–300 ms after the pulse) with an empirical cut-off around 0.31 (Casarotto et al., 2016). Values from other channel counts, sampling rates, windows or preprocessing are **not** comparable with that cut-off or with each other. Compare only recordings processed identically.
- **Near-silent recordings inflate PCI.** Significance is judged against each channel's baseline variability. If baseline activity is almost absent, ordinary small responses look significant and PCI rises. In the [blind challenge](challenge/), a sleep-like network firing at 0.16 Hz scored 0.35. Check baseline activity before trusting a value.
- **Preprocessing is yours.** Baseline normalization uses each channel's pooled pre-stimulus mean and SD. Artifact rejection, filtering and re-referencing must happen before calling `pci`.
- **The simulator is a toy cortex.** It has 20 regions on a ring, point neurons, no thalamus and no plasticity. It reproduces the qualitative wake/sleep contrast, not a human brain. Its PCI values are not clinical values.
- **PCI is not a consciousness detector for arbitrary systems.** It is an empirical marker validated in humans. A high score in a model means "complex like a waking brain's response", nothing more.

## References

- Casali, A. G., et al. (2013). A theoretically based index of consciousness independent of sensory processing and behavior. *Science Translational Medicine*, 5(198), 198ra105.
- Casarotto, S., et al. (2016). Stratification of unresponsive patients by an independently validated index of brain complexity. *Annals of Neurology*, 80(5), 718–729.
- Comolatti, R., et al. (2019). A fast and general method to empirically estimate the complexity of brain responses to transcranial and intracranial stimulations. *Brain Stimulation*, 12(5), 1280–1289.
- Goldman, J. S., et al. (2023). A comprehensive neural simulation of slow-wave sleep and highly responsive wakefulness dynamics. *Frontiers in Computational Neuroscience*, 16, 1058957.
- Jaeger, H. (2001). Short term memory in echo state networks. GMD Report 152.
- Kaspar, F., & Schuster, H. G. (1987). Easily calculable measure for the complexity of spatiotemporal patterns. *Physical Review A*, 36(2), 842–848.

## Licence

MIT — see [LICENSE](LICENSE).
