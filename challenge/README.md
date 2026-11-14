# Blind Consciousness Monitor Challenge

**Can a monitor tell which simulated "patients" are in a wake-like state using only their electrical echo, without ever seeing the answer?**

This challenge mirrors how PCI is used clinically. A cut-off is calibrated on patients whose state is known, then applied blind to new patients (Casarotto et al., 2016). Here the patients are simulated cortices from `zapzip.Cortex`:

- **The hidden truth.** Each of 16 blind patients is wake-like (adaptation 0 pA) or sleep-like (60 pA), 8 of each, shuffled. Each also has its own background drive, randomly within ±30%, to mimic individual differences.
- **What the monitor sees.** Only 40 recorded responses to a 10 ms pulse per patient (20 regions × 600 ms), plus 8 calibration patients with known labels.
- **The rules.** The hidden answers were sealed (SHA-256 recorded) and the [predictions](PREDICTIONS.md) were committed to GitHub **before** any patient was simulated.

## Result

| Pre-registered prediction | Outcome |
| --- | --- |
| **P1.** PCI labels ≥ 14 of 16 blind patients correctly | ✅ **Held**: 15 of 16 |
| **P2.** Spontaneous firing rate does worse than PCI | ❌ **Failed**: rate got 16 of 16 |
| **P3.** Every blind sleep patient's PCI is below every wake patient's | ✅ **Held**: sleep 0.19–0.27, wake 0.33–0.44 |

```
patient  true   drive  PCI    by PCI   rate (Hz)  by rate
P13      sleep  0.354  0.194  ok       0.94       ok
P03      sleep  0.293  0.196  ok       0.87       ok
P06      sleep  0.336  0.211  ok       0.93       ok
P14      sleep  0.341  0.220  ok       0.97       ok
P11      sleep  0.285  0.224  ok       0.85       ok
P04      sleep  0.270  0.236  ok       0.78       ok
P01      sleep  0.237  0.239  ok       0.69       ok
P16      sleep  0.376  0.270  MISS     1.00       ok
P09      wake   0.246  0.328  ok       3.09       ok
P07      wake   0.231  0.344  ok       3.03       ok
P12      wake   0.283  0.365  ok       3.15       ok
P15      wake   0.296  0.383  ok       3.18       ok
P05      wake   0.210  0.407  ok       3.04       ok
P08      wake   0.343  0.422  ok       3.24       ok
P02      wake   0.368  0.440  ok       3.24       ok
P10      wake   0.361  0.442  ok       3.24       ok
```

## What we learned

1. **PCI separated the blind patients perfectly, but the calibrated cut-off was in the wrong place.** Any cut-off between 0.27 and 0.33 would have scored 16/16. The cut-off came out at 0.249 because one calibration patient was an outlier. **C5** was sleep-like with the lowest drive, nearly silent at 0.16 Hz, and scored PCI 0.35. The monitor did exactly what a clinician would do with that calibration set, and paid for it with one miss (P16).
2. **A nearly silent network can fake a high PCI.** C5's baseline activity was so low that ordinary spikes counted as "significant", which inflated its complexity. This is a real limitation of baseline-normalized PCI. It is now listed in the main README: check baseline activity before trusting a PCI value.
3. **The obvious marker was enough here.** In this model, wake-like and sleep-like states differ about 3-fold in spontaneous firing (≈3 Hz versus ≈1 Hz). Drive differences of ±30% did not blur that. So this challenge **does not** show that PCI adds anything over firing rate in this model. That is what P2 tested, and it failed.
4. **Where PCI should matter** is in states where activity and consciousness come apart. In humans, ketamine anaesthesia keeps the brain highly active while consciousness is lost, and a locked-in patient is conscious but cannot move. This model has no such states yet. Building one is the honest next challenge.

## Run it yourself

```bash
pip install -e "..[sim]"
python simulate_patients.py     # the "world": builds 24 patients, ~30 min
python monitor.py               # the "clinic": recordings only → decisions.json
python score.py                 # unblinding: checks the seal, scores → results.json
```

| File | Role |
| --- | --- |
| `PREDICTIONS.md` | Pre-registered predictions and the seal hash (committed before any run) |
| `calibration_patients.json` | 8 known patients (states and drives visible) |
| `blind_patients.json` | 16 blind patients (IDs and seeds only) |
| `sealed/answers.json` | The hidden truth (SHA-256 `befa3476…bc1e51`); only `simulate_patients.py` and `score.py` read it |
| `decisions.json` | The monitor's markers and labels |
| `results.json` | The scored outcome |
