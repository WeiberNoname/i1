# Pre-registered predictions — Challenge 2: when activity misleads

Committed **before** any Challenge 2 patient was simulated or any PCI computed for these states.

## Why this challenge

In [Challenge 1](../challenge/), firing rate separated wake from sleep as well as PCI did. PCI's real-world value lies in patients whose activity misleads: busy but unconscious (as under ketamine), or quiet but aware. This challenge asks whether PCI keeps tracking the network's regime when firing rate points the wrong way.

## What "conscious-like" means here

The ground truth is defined **by construction, using the theory PCI comes from**. Integrated, differentiated wake-type dynamics count as conscious-like. Disconnected or bistable, sleep-type dynamics count as unconscious-like. So this tests whether PCI tracks that regime despite misleading activity. It cannot test consciousness itself.

## The four hidden patient types (4 each, 16 blind patients, shuffled)

| Type | How it is built | Truth label |
| --- | --- | --- |
| wake | adaptation 0 pA, drive 0.3 ± 30% | conscious-like |
| sleep | adaptation 60 pA, drive 0.3 ± 30% | unconscious-like |
| **disconnected-active** | adaptation 0 pA, **no long-range links** (400 local excitatory inputs), **high drive 1.0 ± 30%** | unconscious-like |
| **quiet-wake** | adaptation 0 pA, **stronger inhibition** (Qi = 9 nS instead of 5), drive 0.3 ± 30% | conscious-like |

The two new types were tuned **on firing rate and burstiness only** (pilot: disconnected-active ≈ 2.3–2.6 Hz, non-bursting; quiet-wake ≈ 1.2 Hz, non-bursting). No PCI was computed for them before this file was committed.

Sealed answers: `sealed/answers.json`, SHA-256 `fa373859212e8701a2a6ab66cc325cc00ebc08facc9ee333a8f0d877b1954ce3`.

## The monitor

The monitor uses the cut-offs **calibrated in Challenge 1** on ordinary wake and sleep patients: PCI 0.249 and firing rate 2.04 Hz. It is then deployed unchanged on the new population, as a clinic would deploy a validated monitor on new patients.

## Predictions

- **P1 (manipulation check).** The firing-rate marker mislabels at least 6 of the 8 atypical patients. If it does not, the challenge failed to create misleading activity, and P2–P4 tell us little.
- **P2.** PCI labels at least 6 of the 8 atypical patients correctly.
- **P3.** PCI labels at least 12 of all 16 patients correctly.
- **P4.** PCI beats firing rate overall (more correct labels out of 16).

## Known risks that could make PCI fail

- The quiet-wake state has low activity, and Challenge 1 showed that near-silent recordings can inflate PCI.
- A disconnected network may respond in only one region. PCI's normalization of a sparse one-row matrix has not been tested and could score high.
- The Challenge 1 PCI cut-off (0.249) is known to be pulled low by an outlier.
