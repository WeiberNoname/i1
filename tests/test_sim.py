import numpy as np
import pytest

pytest.importorskip("numba")
from zapzip import Cortex, pci   # noqa: E402

SMALL = dict(regions=6, NE=400, NI=100)


def test_build_and_rates_are_plausible():
    ctx = Cortex(state="wake", seed=3, **SMALL)
    rates = ctx.region_rates(ctx.run(0.5), 0.5)
    assert rates.shape == (6,)
    assert 0.5 < rates.mean() < 15


def test_sleep_fires_less_than_wake():
    w = Cortex(state="wake", seed=3, **SMALL); s = Cortex(state="sleep", seed=3, **SMALL)
    rw = w.region_rates(w.run(1.0), 1.0).mean(); rs = s.region_rates(s.run(1.0), 1.0).mean()
    assert rs < rw


def test_zap_shape():
    ctx = Cortex(seed=3, **SMALL)
    trials = ctx.zap(n_pulses=2, pre_ms=50, post_ms=50)
    assert trials.shape == (2, 6, 100)


def test_bad_params():
    with pytest.raises(ValueError):
        Cortex(NE=100, KE_loc=280)


@pytest.mark.slow
def test_wake_pci_exceeds_sleep_pci():
    """The paper's central result, re-derived through the package API."""
    vals = {}
    for s in ("wake", "sleep"):
        ctx = Cortex(state=s, seed=21)
        vals[s] = pci(ctx.zap(n_pulses=40, seed=1), n_pre=300).value
    assert vals["wake"] > vals["sleep"] + 0.05
