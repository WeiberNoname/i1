import numpy as np
import pytest
from zapzip import lz76, pci, pci_from_binary


def test_lz76_textbook_example():
    # Kaspar & Schuster (1987): 0 . 001 . 10 . 100 . 1000 . 101 -> 6 words
    assert lz76([int(c) for c in "0001101001000101"]) == 6


def test_lz76_constant_and_empty():
    assert lz76([]) == 0
    assert lz76([1] * 100) == 2


@pytest.mark.parametrize("n,p", [(50, 0.1), (500, 0.5), (5000, 0.1), (5000, 0.5)])
def test_lz76_matches_antropy(n, p):
    antropy = pytest.importorskip("antropy")
    x = (np.random.default_rng(n).random(n) < p).astype(int)
    assert lz76(x) == antropy.lziv_complexity("".join(map(str, x)), normalize=False)


def test_pci_from_binary_extremes():
    rng = np.random.default_rng(0)
    assert pci_from_binary(rng.random((20, 300)) < 0.3) == pytest.approx(1.0, abs=0.1)
    block = np.zeros((20, 300), bool); block[:, 10:60] = True
    assert pci_from_binary(block) < 0.05
    assert pci_from_binary(np.zeros((5, 10), bool)) == 0.0


def test_pci_detects_structure_and_ignores_noise():
    rng = np.random.default_rng(1)
    noise = rng.normal(size=(40, 16, 400))
    r = pci(noise, n_pre=200)
    assert r.significant.mean() < 0.01            # pure noise: (almost) nothing significant

    evoked = noise.copy()
    for ch in range(16):                          # each channel answers at its own delay
        evoked[:, ch, 200 + 5 * ch:230 + 5 * ch] += 3.0
    rich = pci(evoked, n_pre=200)
    same = noise.copy(); same[:, :, 210:240] += 3.0   # every channel answers identically
    uniform = pci(same, n_pre=200)
    assert rich.channels_active == 16
    assert rich.value > uniform.value


def test_input_validation():
    with pytest.raises(ValueError):
        pci(np.zeros((5, 100)), n_pre=10)
    with pytest.raises(ValueError):
        pci(np.zeros((5, 4, 100)), n_pre=100)
