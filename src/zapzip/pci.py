"""
Perturbational Complexity Index (PCI), Lempel-Ziv version (Casali et al. 2013,
Sci. Transl. Med. 5:198ra105).

Works on any evoked-response data shaped (trials, channels, time):
EEG sources, electrode channels, or simulated region activity.

    from zapzip import pci
    result = pci(trials, n_pre=300)          # stimulus at sample 300
    result.value, result.significant         # PCI, binary matrix

Notes
-----
* LZ76 is the Kaspar & Schuster (1987) algorithm; it is cross-checked in the
  test suite against the textbook example and the independent `antropy` package.
* Binarization follows the bootstrap approach of Casali et al.: baseline samples
  are shuffled within trials, and the (1 - alpha) quantile of the maximum
  absolute trial-averaged baseline value is the significance threshold.
* Absolute values depend on channel count, sampling and preprocessing; compare
  PCI only between recordings processed the same way.
"""
from dataclasses import dataclass
import numpy as np

__all__ = ["lz76", "binarize", "pci_from_binary", "pci", "PCIResult"]


def lz76(sequence) -> int:
    """Lempel-Ziv 1976 complexity (number of distinct words) of a binary sequence."""
    s = np.asarray(sequence, dtype=np.int8).ravel()
    n = s.size
    if n == 0:
        return 0
    c, l, i, k, k_max = 1, 1, 0, 1, 1
    while True:
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            k_max = max(k, k_max)
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n:
                    break
                i, k, k_max = 0, 1, 1
            else:
                k = 1
    return c


def binarize(trials, n_pre, alpha=0.01, n_boot=500, seed=0):
    """Significance matrix (channels x post-stimulus samples).

    trials : array (n_trials, n_channels, n_samples), stimulus at index n_pre.
    Returns (significant: bool array, threshold: float, evoked: z-scored average).
    """
    x = np.asarray(trials, dtype=float)
    if x.ndim != 3:
        raise ValueError("trials must be shaped (trials, channels, time)")
    if not 0 < n_pre < x.shape[2]:
        raise ValueError("n_pre must lie inside the time axis")
    rng = np.random.default_rng(seed)
    base = x[:, :, :n_pre]
    mu = base.mean(axis=(0, 2), keepdims=True)
    sd = base.std(axis=(0, 2), keepdims=True) + 1e-12
    z = (x - mu) / sd
    evoked = z.mean(0)
    zb = z[:, :, :n_pre]
    nt = zb.shape[0]
    maxes = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n_pre, size=(nt, n_pre))
        maxes[b] = np.abs(np.take_along_axis(zb, idx[:, None, :], axis=2).mean(0)).max()
    thr = float(np.quantile(maxes, 1 - alpha))
    return np.abs(evoked[:, n_pre:]) > thr, thr, evoked


def pci_from_binary(significant) -> float:
    """PCI of a binary (channels x time) matrix: normalized LZ76 complexity."""
    S = np.asarray(significant, dtype=bool)
    S = S[np.argsort(S.sum(1))]                 # sort channels by total activity
    L = S.size
    p1 = S.mean()
    if p1 == 0 or p1 == 1:
        return 0.0
    H = -p1 * np.log2(p1) - (1 - p1) * np.log2(1 - p1)
    return lz76(S.T.ravel()) * np.log2(L) / (L * H)


@dataclass
class PCIResult:
    value: float
    significant: np.ndarray
    threshold: float
    evoked: np.ndarray

    @property
    def channels_active(self) -> int:
        return int(self.significant.any(1).sum())

    def __repr__(self):
        return (f"PCIResult(value={self.value:.3f}, channels_active={self.channels_active}/"
                f"{self.significant.shape[0]}, significant_fraction={self.significant.mean():.3f})")


def pci(trials, n_pre, n_post=None, alpha=0.01, n_boot=500, seed=0) -> PCIResult:
    """Compute PCI from evoked trials (n_trials, n_channels, n_samples).

    n_pre  : number of baseline samples before the stimulus.
    n_post : optional number of post-stimulus samples to analyse (default: all).
    """
    x = np.asarray(trials, dtype=float)
    if n_post is not None:
        x = x[:, :, :n_pre + n_post]
    sig, thr, ev = binarize(x, n_pre, alpha=alpha, n_boot=n_boot, seed=seed)
    return PCIResult(pci_from_binary(sig), sig, thr, ev)
