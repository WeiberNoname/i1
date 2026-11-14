# Pre-registered predictions — Blind Consciousness Monitor Challenge

Written and committed **before** any patient was simulated or any recording analysed.
The git timestamp of this file is the proof of order.

## The problem

A "clinic" receives 16 simulated cortex patients. Each has a **hidden state**
(wake-like, adaptation 0 pA, or sleep-like, 60 pA; 8 of each, shuffled) and a
**hidden background drive** drawn uniformly within ±30% of the default
(`nu_ext` 0.21–0.39 Hz). Individual differences of this kind are what make real
patients hard to compare.

The monitor gets only what a clinician would get: 40 recordings of each patient's
response to a 10 ms pulse into region 0 (20 regions × 600 ms, stimulus at 300 ms).
It never sees the state, the drive or the seed.

It may calibrate on 8 **known** patients (4 wake, 4 sleep, drives 0.21/0.27/0.33/0.39),
in the same way the clinical PCI cut-off was calibrated on known conscious and
unconscious subjects (Casarotto et al., 2016). It then labels each blind patient
"conscious-like" or "unconscious-like".

The answers are sealed in `sealed/answers.json`:
SHA-256 `befa3476a81eea982a74f8e8b5a061eab2c20adceefedba91752ceac33bc1e51`.

## Markers compared

1. **PCI** (`zapzip.pci`). The cut-off is set on the calibration patients at the midpoint between the highest sleep and lowest wake value, or at the best-accuracy point if they overlap.
2. **Spontaneous firing rate**, taken from the pre-stimulus baseline of the same recordings. It uses the same cut-off rule. This is the "obvious" marker: sleep fires less.

## Predictions

- **P1.** PCI labels at least 14 of 16 blind patients correctly.
- **P2.** The firing-rate marker does worse than PCI on the blind set, because drive differences shift rates and blur the two states. If rate does as well or better, that counts against PCI's value in this setting.
- **P3.** Every blind sleep-like patient's PCI falls below every blind wake-like patient's PCI (perfect separation).

Basis: in the paper, PCI was 0.40 ± 0.05 (wake) versus 0.22 ± 0.03 (sleep) on 6 networks, all at default drive. Drive variation is new here, so all three predictions can fail.

## Not tested here

Memory capacity as a marker. The paper found it moves the *opposite* way (sleep 0.30 versus wake 0.06), so a monitor built on it would invert the labels. It costs about 3 minutes per patient, so it is left out.
