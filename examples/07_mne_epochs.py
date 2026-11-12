"""PCI from MNE-Python epochs (TMS-EEG or any evoked EEG/MEG).

With real data, replace the synthetic EpochsArray by your own `mne.Epochs`
(already filtered, artifact-cleaned and epoched around the stimulus at t = 0).
"""
import numpy as np
import mne
from zapzip import pci

# --- synthetic stand-in for real epochs: 40 trials, 20 EEG channels, 1000 Hz, -0.3 to +0.3 s
sfreq, n_ch = 1000.0, 20
info = mne.create_info([f"EEG{i:02d}" for i in range(n_ch)], sfreq, ch_types="eeg")
rng = np.random.default_rng(0)
data = rng.normal(scale=1e-6, size=(40, n_ch, 600))
for ch in range(n_ch):
    data[:, ch, 310 + 8 * ch:340 + 8 * ch] += 2.5e-6         # channel-specific evoked waves
epochs = mne.EpochsArray(data, info, tmin=-0.3, verbose=False)

# --- the part you need for real data
x = epochs.get_data()                              # (trials, channels, samples)
n_pre = int(np.sum(epochs.times < 0))              # samples before the stimulus
n_post = int(np.sum((epochs.times >= 0) & (epochs.times < 0.3)))   # analyse 0-300 ms
result = pci(x, n_pre=n_pre, n_post=n_post)
print(result)
