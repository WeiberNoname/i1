"""
A small spiking 'cortex' you can put to sleep, zap and use as a computer.

10,000 conductance-based adaptive exponential integrate-and-fire (AdEx) neurons in
20 regions on a ring. Wake-like and sleep-like states differ only in the
spike-frequency adaptation of excitatory cells (0 vs 60 pA), as in Goldman et al. (2023).

    from zapzip import Cortex, pci
    ctx = Cortex(state="wake", seed=1)
    trials = ctx.zap(n_pulses=40)            # (pulses, regions, ms)
    print(pci(trials, n_pre=300))
    print(ctx.memory_capacity(seconds=60))

Requires numba (pip install "zapzip[sim]"). About 2 s of CPU per simulated second.
"""
import numpy as np

try:
    import numba as nb
except ImportError:  # pragma: no cover
    nb = None

__all__ = ["Cortex", "DEFAULTS", "STATES"]

STATES = {"wake": 0.0, "sleep": 60e-12}

DEFAULTS = dict(
    regions=20, NE=400, NI=100,
    KE_loc=280, KE_lr=120, KI=80, lr_lambda=2.5,
    Qe=2e-9, Qi=5e-9, tau_e=5e-3, tau_i=5e-3, Ee=0.0, Ei=-80e-3,
    C=200e-12, gL=10e-9, EL_e=-64e-3, EL_i=-65e-3,
    Vt=-50e-3, Vreset=-65e-3, Vpeak=-30e-3, De=2e-3, Di=0.5e-3,
    tau_w=500e-3, a=0.0, tref=5e-3,
    K_ext=400, nu_ext=0.3, input_fibres=50, dt=1e-4,
)


def _kernel():
    if nb is None:
        raise ImportError('zapzip.Cortex needs numba: pip install "zapzip[sim]"')

    @nb.njit(cache=True)
    def seed(s):
        np.random.seed(s)

    @nb.njit(cache=True, fastmath=True, parallel=True)
    def run(nsteps, V, w, ge, gi, ref, is_E, region, EL, Delta, b,
            E_ptr, E_idx, I_ptr, I_idx, lam_ext, lam_in_reg,
            Qe, Qi, C, gL, Ee, Ei, Vt, Vreset, Vpeak, a, tau_w, tref, dt, de, di, counts):
        N = V.size
        M = lam_in_reg.size
        Lreg = np.empty(M)
        for r in range(M):
            Lreg[r] = np.exp(-(lam_ext + lam_in_reg[r]))
        Lext = np.exp(-lam_ext)
        for k in range(nsteps):
            for n in nb.prange(N):
                L = Lreg[region[n]] if is_E[n] else Lext
                kk = 0
                p = np.random.random()
                while p > L:
                    kk += 1
                    p *= np.random.random()
                if kk > 0:
                    ge[n] += Qe * kk
                if ref[n] > 0.0:
                    ref[n] -= dt
                    V[n] = Vreset
                else:
                    x = (V[n] - Vt) / Delta[n]
                    if x > 20.0:
                        x = 20.0
                    I = gL * (EL[n] - V[n]) + gL * Delta[n] * np.exp(x) \
                        + ge[n] * (Ee - V[n]) + gi[n] * (Ei - V[n]) - w[n]
                    V[n] += dt * I / C
                w[n] += dt * (a * (V[n] - EL[n]) - w[n]) / tau_w
            for n in range(N):
                if V[n] >= Vpeak:
                    V[n] = Vreset
                    w[n] += b[n]
                    ref[n] = tref
                    counts[n] += 1
                    if is_E[n]:
                        for j in range(E_ptr[n], E_ptr[n + 1]):
                            ge[E_idx[j]] += Qe
                    else:
                        for j in range(I_ptr[n], I_ptr[n + 1]):
                            gi[I_idx[j]] += Qi
                ge[n] *= de
                gi[n] *= di
    return seed, run


_KERNEL = None


def _csr(pre, post, N):
    order = np.argsort(pre, kind="stable")
    ptr = np.zeros(N + 1, np.int64)
    np.add.at(ptr, pre + 1, 1)
    return np.cumsum(ptr), post[order].astype(np.int64)


class Cortex:
    """Spiking cortical network with a wake/sleep switch, a perturbation and task inputs."""

    def __init__(self, state="wake", seed=0, **params):
        global _KERNEL
        if _KERNEL is None:
            _KERNEL = _kernel()
        self._seed_fn, self._run = _KERNEL
        p = dict(DEFAULTS); p.update(params); self.p = p
        M, NE, NI = p["regions"], p["NE"], p["NI"]
        for key, pool in (("KE_loc", NE), ("KI", NI)):
            if p[key] > pool:
                raise ValueError(f"{key}={p[key]} exceeds population size {pool}")
        rng = np.random.default_rng(seed)
        nreg = NE + NI
        self.M, self.N = M, M * nreg
        self.region = np.repeat(np.arange(M), nreg).astype(np.int64)
        self.is_E = np.tile(np.r_[np.ones(NE, bool), np.zeros(NI, bool)], M)
        d = np.abs(np.arange(M)[:, None] - np.arange(M)[None, :])
        d = np.minimum(d, M - d).astype(float)
        P = np.exp(-d / p["lr_lambda"]) * rng.uniform(0.3, 1.7, (M, M))
        np.fill_diagonal(P, 0); P /= P.sum(1, keepdims=True)
        preE, postE, preI, postI = [], [], [], []
        for r in range(M):
            tgt = np.arange(r * nreg, (r + 1) * nreg)
            nt = tgt.size
            loc = np.argpartition(rng.random((nt, NE)), p["KE_loc"] - 1, axis=1)[:, :p["KE_loc"]]
            preE.append((r * nreg + loc).ravel()); postE.append(np.repeat(tgt, p["KE_loc"]))
            regs = np.array([rng.choice(M, p["KE_lr"], p=P[r]) for _ in range(nt)])
            preE.append((regs * nreg + rng.integers(0, NE, regs.shape)).ravel())
            postE.append(np.repeat(tgt, p["KE_lr"]))
            inh = np.argpartition(rng.random((nt, NI)), p["KI"] - 1, axis=1)[:, :p["KI"]]
            preI.append((r * nreg + NE + inh).ravel()); postI.append(np.repeat(tgt, p["KI"]))
        self._E_ptr, self._E_idx = _csr(np.concatenate(preE), np.concatenate(postE), self.N)
        self._I_ptr, self._I_idx = _csr(np.concatenate(preI), np.concatenate(postI), self.N)
        self._seed_fn(int(seed) + 12345)
        self.EL = np.where(self.is_E, p["EL_e"], p["EL_i"])
        self.Delta = np.where(self.is_E, p["De"], p["Di"])
        self.V = rng.uniform(-65e-3, -55e-3, self.N)
        self.w = np.zeros(self.N); self.ge = np.zeros(self.N); self.gi = np.zeros(self.N)
        self.ref = np.zeros(self.N)
        self.set_state(state)
        self.run(1.0)                                  # settle

    # ------------------------------------------------------------------ control
    def set_state(self, state):
        """'wake', 'sleep', or an adaptation strength in pA (e.g. 30)."""
        b = STATES[state] if isinstance(state, str) else float(state) * 1e-12
        self.state = state
        self.b = np.where(self.is_E, b, 0.0)

    def run(self, seconds, input_hz=None):
        """Simulate. input_hz: extra Poisson rate per fibre for each region's E cells (len = regions).
        Returns spike counts per neuron."""
        p = self.p; dt = p["dt"]
        lam_in = np.zeros(self.M) if input_hz is None else np.asarray(input_hz, float) * p["input_fibres"] * dt
        counts = np.zeros(self.N, np.int32)
        self._run(int(round(seconds / dt)), self.V, self.w, self.ge, self.gi, self.ref, self.is_E,
                  self.region, self.EL, self.Delta, self.b, self._E_ptr, self._E_idx, self._I_ptr,
                  self._I_idx, p["K_ext"] * p["nu_ext"] * dt, lam_in, p["Qe"], p["Qi"], p["C"], p["gL"],
                  p["Ee"], p["Ei"], p["Vt"], p["Vreset"], p["Vpeak"], p["a"], p["tau_w"], p["tref"], dt,
                  np.exp(-dt / p["tau_e"]), np.exp(-dt / p["tau_i"]), counts)
        return counts

    def region_rates(self, counts, seconds):
        """Mean excitatory firing rate per region (Hz) from spike counts."""
        E = self.is_E
        return np.bincount(self.region[E], weights=counts[E], minlength=self.M) / (self.p["NE"] * seconds)

    # ------------------------------------------------------------- experiments
    def zap(self, n_pulses=40, region=0, pre_ms=300, post_ms=300, pulse_hz=150.0, pulse_ms=10,
            smooth_ms=10, seed=0):
        """Perturbation protocol. Returns trials (pulses, regions, pre_ms + post_ms) of region rates,
        stimulus at index pre_ms, boxcar-smoothed over smooth_ms (EEG-like)."""
        rng = np.random.default_rng(seed)
        out = np.empty((n_pulses, self.M, pre_ms + post_ms))
        stim = np.zeros(self.M); stim[region] = pulse_hz
        for k in range(n_pulses):
            self.run(rng.uniform(0.3, 0.7))
            for t in range(pre_ms + post_ms):
                on = pre_ms <= t < pre_ms + pulse_ms
                out[k, :, t] = self.region_rates(self.run(1e-3, stim if on else None), 1e-3)
        if smooth_ms > 1:
            ker = np.ones(smooth_ms) / smooth_ms
            out = np.apply_along_axis(lambda x: np.convolve(x, ker, "same"), 2, out)
        return out

    def reservoir_states(self, inputs_hz, step_s=0.02, n_features=2000, tau_s=0.02, seed=0):
        """Drive the network with a sequence of input vectors (T x regions, Hz per fibre), one per
        step_s, and return readout features (T x n_features): exponentially filtered spike counts
        of randomly chosen excitatory neurons."""
        rng = np.random.default_rng(seed)
        feat = np.sort(rng.choice(np.flatnonzero(self.is_E), n_features, replace=False))
        X = np.zeros((len(inputs_hz), n_features), np.float32)
        tr = np.zeros(n_features); dec = np.exp(-step_s / tau_s)
        for t, u in enumerate(inputs_hz):
            tr = tr * dec + self.run(step_s, u)[feat]
            X[t] = tr
        return X

    def memory_capacity(self, seconds=90.0, input_regions=(0, 1, 2, 3), max_lag=15, peak_hz=6.0, seed=0):
        """Linear memory capacity (Jaeger 2001): sum over lags 1..max_lag of the held-out r^2 of a
        ridge readout recalling a random input u(t - lag). Returns (capacity, r2 per lag 0..max_lag)."""
        rng = np.random.default_rng(seed)
        n = int(seconds / 0.02); u = rng.random(n)
        U = np.zeros((n, self.M)); U[:, list(input_regions)] = peak_hz * u[:, None]
        X = self.reservoir_states(U, seed=seed)
        skip = 50; ntr = int((n - skip) * 0.7) + skip
        r2 = []
        for k in range(max_lag + 1):
            y = np.roll(u, k)
            yhat = _ridge(X[skip:ntr], y[skip:ntr], X[ntr:])
            c = np.corrcoef(yhat, y[ntr:])[0, 1]
            r2.append(float(max(c, 0) ** 2))
        return float(sum(r2[1:])), r2


def _ridge(Xtr, ytr, Xte, alphas=(0.1, 1, 10, 100, 1000)):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    A = np.c_[(Xtr - mu) / sd, np.ones(len(Xtr))]; B = np.c_[(Xte - mu) / sd, np.ones(len(Xte))]
    cut = int(len(A) * 0.8); best = None
    for a in alphas:
        wv = np.linalg.solve(A[:cut].T @ A[:cut] + a * np.eye(A.shape[1]), A[:cut].T @ ytr[:cut])
        e = np.mean((A[cut:] @ wv - ytr[cut:]) ** 2)
        if best is None or e < best[0]:
            best = (e, a)
    wv = np.linalg.solve(A.T @ A + best[1] * np.eye(A.shape[1]), A.T @ ytr)
    return B @ wv
