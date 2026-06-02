"""
Analysis pipeline (spec Section 6).

Computes, per trial / per condition:
  - Firing rates (population and per-cell)
  - LFP-proxy power spectrum (= smoothed population rate; cheap and standard)
  - Sender→receiver magnitude-squared coherence and gamma-band PPC
  - Granger causality (sender→receiver, receiver→sender) via VAR
  - Transfer entropy (binned, model-free cross-check)
  - Decoding accuracy: linear classifier of sender stimulus identity from
    receiver E-cell spike counts (the headline dependent variable)

All numpy / scipy / scikit-learn / statsmodels. No Brian2 here — the pipeline
operates on saved simulation outputs so conditions can be re-analyzed without
re-running.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy.signal import coherence as scoh, welch
from scipy.signal import correlate
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold


# ---------------------------------------------------------------------------
# Spike-train → time-series helpers
# ---------------------------------------------------------------------------

def population_rate(spikes_t: np.ndarray, n_cells: int, duration_ms: float,
                    bin_ms: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Population firing rate (Hz averaged across the population)."""
    n_bins = int(np.ceil(duration_ms / bin_ms))
    counts, edges = np.histogram(spikes_t, bins=n_bins, range=(0, n_bins * bin_ms))
    rate = counts / (n_cells * bin_ms / 1000.0)
    t = (edges[:-1] + edges[1:]) / 2
    return t, rate


def spike_counts_per_cell(spikes_t: np.ndarray, spikes_i: np.ndarray,
                          n_cells: int, t_start: float = 0.0,
                          t_end: float | None = None) -> np.ndarray:
    """Return shape (n_cells,) of spike counts in [t_start, t_end]."""
    mask = spikes_t >= t_start
    if t_end is not None:
        mask &= spikes_t < t_end
    return np.bincount(spikes_i[mask], minlength=n_cells)


# ---------------------------------------------------------------------------
# Spectral measures
# ---------------------------------------------------------------------------

def lfp_proxy(spikes_t: np.ndarray, n_cells: int, duration_ms: float,
              bin_ms: float = 1.0, smooth_ms: float = 2.0) -> np.ndarray:
    """LFP proxy = Gaussian-smoothed population rate (centered, zero-mean)."""
    _, rate = population_rate(spikes_t, n_cells, duration_ms, bin_ms=bin_ms)
    sigma_bins = max(smooth_ms / bin_ms, 1e-9)
    half = int(np.ceil(4 * sigma_bins))
    x = np.arange(-half, half + 1)
    kernel = np.exp(-0.5 * (x / sigma_bins) ** 2)
    kernel /= kernel.sum()
    smoothed = np.convolve(rate, kernel, mode="same")
    return smoothed - smoothed.mean()


def _nperseg(signal_len: int, fs: float) -> int:
    """Choose a segment length that gives multiple Welch segments.

    Coherence is trivially 1.0 with a single segment (no averaging). We aim
    for ≥4 segments with 50% overlap. nperseg ≈ N/3 (with 50% overlap that's
    ~6 segments). Floor at 64, ceiling at fs (1 s segments).
    """
    target = max(64, min(int(fs), signal_len // 3))
    return target


def power_spectrum(signal: np.ndarray, dt_ms: float,
                   freqs_range_hz: tuple[float, float] = (1.0, 200.0)
                   ) -> tuple[np.ndarray, np.ndarray]:
    fs = 1000.0 / dt_ms
    f, p = welch(signal, fs=fs, nperseg=_nperseg(len(signal), fs))
    band = (f >= freqs_range_hz[0]) & (f <= freqs_range_hz[1])
    return f[band], p[band]


def sender_receiver_coherence(send_sig: np.ndarray, recv_sig: np.ndarray,
                              dt_ms: float,
                              freqs_range_hz: tuple[float, float] = (1.0, 200.0)
                              ) -> tuple[np.ndarray, np.ndarray]:
    fs = 1000.0 / dt_ms
    f, c = scoh(send_sig, recv_sig, fs=fs, nperseg=_nperseg(len(send_sig), fs))
    band = (f >= freqs_range_hz[0]) & (f <= freqs_range_hz[1])
    return f[band], c[band]


def gamma_band_mean(f: np.ndarray, v: np.ndarray,
                    band_hz: tuple[float, float] = (30.0, 90.0)) -> float:
    mask = (f >= band_hz[0]) & (f <= band_hz[1])
    return float(np.mean(v[mask])) if mask.any() else float("nan")


# ---------------------------------------------------------------------------
# Directed influence (Granger via VAR, transfer entropy)
# ---------------------------------------------------------------------------

def granger_causality(x_send: np.ndarray, y_recv: np.ndarray,
                      lag: int = 5) -> dict:
    """Pairwise-conditional Granger via OLS VAR.

    Uses statsmodels' grangercausalitytests at a SINGLE FIXED LAG (default 5,
    appropriate for 1-ms bins and gamma rhythm of ~60 Hz / 16 ms period).
    Reviewer round 1 M4 flagged that taking max-F across multiple lags inflates
    the statistic, so we report only the fixed-lag value here.
    """
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except ImportError:
        return {"available": False}

    import warnings
    warnings.filterwarnings("ignore")

    data_xy = np.column_stack([y_recv, x_send])  # tests x → y (sender → receiver)
    data_yx = np.column_stack([x_send, y_recv])  # tests y → x (receiver → sender)
    res_sr = grangercausalitytests(data_xy, maxlag=lag, verbose=False)
    res_rs = grangercausalitytests(data_yx, maxlag=lag, verbose=False)

    def at_lag(res, L):
        F, p, df_diff, df_resid = res[L][0]["ssr_ftest"]
        return float(F), float(p)

    F_sr, p_sr = at_lag(res_sr, lag)
    F_rs, p_rs = at_lag(res_rs, lag)
    return {
        "available": True,
        "F_send_to_recv": F_sr,
        "p_send_to_recv": p_sr,
        "F_recv_to_send": F_rs,
        "p_recv_to_send": p_rs,
        "asymmetry_F": F_sr - F_rs,
        "lag_used": lag,
    }


def transfer_entropy(x_send: np.ndarray, y_recv: np.ndarray,
                     n_bins: int = 4, lag: int = 2) -> float:
    """Binned transfer entropy x → y (Schreiber 2000), in nats.

    Discretizes both signals into n_bins equiprobable bins. Estimates
    TE = sum p(y_t+1, y_t, x_t) * log[ p(y_t+1 | y_t, x_t) / p(y_t+1 | y_t) ]
    """
    def quantize(v, n):
        ranks = np.argsort(np.argsort(v))
        return (ranks * n // len(v)).clip(0, n - 1)

    xq = quantize(x_send, n_bins)
    yq = quantize(y_recv, n_bins)
    n = len(xq) - lag
    if n <= 10:
        return float("nan")
    x_past = xq[: -lag] if lag > 0 else xq[:-1]
    y_past = yq[:-lag] if lag > 0 else yq[:-1]
    y_future = yq[lag:] if lag > 0 else yq[1:]
    # ensure aligned lengths
    L = min(len(x_past), len(y_past), len(y_future))
    x_past = x_past[-L:]
    y_past = y_past[-L:]
    y_future = y_future[-L:]

    # Joint histograms
    from collections import Counter
    p_xy_yp = Counter(zip(x_past, y_past, y_future))
    p_xy = Counter(zip(x_past, y_past))
    p_y_yp = Counter(zip(y_past, y_future))
    p_y = Counter(y_past)
    N = L
    te = 0.0
    for (xp, yp, yn), c_xy_yp in p_xy_yp.items():
        c_xy = p_xy[(xp, yp)]
        c_y_yp = p_y_yp[(yp, yn)]
        c_y = p_y[yp]
        if c_xy == 0 or c_y == 0:
            continue
        num = (c_xy_yp / N) * (c_y / N)
        den = (c_xy / N) * (c_y_yp / N)
        if num <= 0 or den <= 0:
            continue
        te += (c_xy_yp / N) * np.log(num / den)
    return float(te)


# ---------------------------------------------------------------------------
# Decoder: stimulus identity from receiver E-cell spike counts.
# This is the headline dependent variable (spec Section 6, item 5).
# ---------------------------------------------------------------------------

def build_decoder_features(trials: list[dict], n_receiver_E: int,
                           transient_ms: float = 200.0,
                           window_ms: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Stack per-trial receiver E spike-count vectors into (n_trials, N_E).

    Optionally only count spikes within a sliding window of length
    window_ms (counted from transient_ms). Returns (X, y).
    """
    X_rows, y_rows = [], []
    for tr in trials:
        recv = tr["receiver"]
        dur = tr["trial"]["duration_ms"]
        t_start = transient_ms
        t_end = dur if window_ms is None else transient_ms + window_ms
        x = spike_counts_per_cell(recv["spikes_E_t"], recv["spikes_E_i"],
                                   n_receiver_E, t_start=t_start, t_end=t_end)
        X_rows.append(x)
        y_rows.append(tr["trial"]["stimulus_id"])
    return np.asarray(X_rows, dtype=float), np.asarray(y_rows, dtype=int)


def decode_stimulus(X: np.ndarray, y: np.ndarray, n_folds: int = 5,
                    seed: int = 0) -> dict:
    """Stratified k-fold logistic regression. Returns mean accuracy + per-fold."""
    # Per-trial z-score across cells to remove a per-trial overall-rate confound
    X = X.astype(float)
    row_mean = X.mean(axis=1, keepdims=True)
    row_std = X.std(axis=1, keepdims=True) + 1e-6
    X = (X - row_mean) / row_std

    if len(np.unique(y)) < 2 or len(y) < n_folds * 2:
        return {"mean_accuracy": float("nan"), "accuracies": [], "n_classes": int(len(np.unique(y)))}

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    accs = []
    for tr, te in skf.split(X, y):
        clf = LogisticRegression(max_iter=2000, C=1.0,
                                 multi_class="auto", solver="lbfgs")
        clf.fit(X[tr], y[tr])
        accs.append(float(clf.score(X[te], y[te])))
    return {
        "mean_accuracy": float(np.mean(accs)),
        "se_accuracy": float(np.std(accs, ddof=1) / np.sqrt(len(accs))) if len(accs) > 1 else 0.0,
        "accuracies": accs,
        "n_classes": int(len(np.unique(y))),
        "chance": 1.0 / len(np.unique(y)),
    }


# ---------------------------------------------------------------------------
# All-in-one per-trial summary
# ---------------------------------------------------------------------------

@dataclass
class PerTrialMetrics:
    sender_rate_hz: float
    receiver_rate_hz: float
    delivered_rate_hz: float        # spikes ACTUALLY delivered to receiver (post-channel)
    sender_gamma_power: float
    receiver_gamma_power: float
    delivered_gamma_power: float    # power of the delivered signal
    sender_peak_hz: float | None
    receiver_peak_hz: float | None
    gamma_coherence: float          # sender vs receiver (post-transient)
    delivered_coherence: float      # delivered vs sender (post-transient) - the manipulation check
    granger_F_sr: float
    granger_F_rs: float
    transfer_entropy: float
    config_dict: dict


def summarize_trial(trial: dict, transient_ms: float = 200.0,
                    bin_ms: float = 1.0, smooth_ms: float = 2.0
                    ) -> PerTrialMetrics:
    """Compute per-trial measurements used both as manipulation checks and
    as the (rate/power/coherence) dependent variables."""
    sender = trial["sender"]
    recv = trial["receiver"]
    n_send = sender["config"]["N_E"]
    n_recv = recv["config_recv"]["N_E"]
    dur = trial["trial"]["duration_ms"]

    # restrict to post-transient
    def mask(t):
        return t >= transient_ms

    s_t = sender["spikes_E_t"][mask(sender["spikes_E_t"])]
    s_i = sender["spikes_E_i"][mask(sender["spikes_E_t"])]
    r_t = recv["spikes_E_t"][mask(recv["spikes_E_t"])]
    r_i = recv["spikes_E_i"][mask(recv["spikes_E_t"])]
    eff_dur = dur - transient_ms

    # Delivered (post-channel) spikes — this is what actually reaches the
    # receiver and is the correct signal for the rate/power manipulation
    # check (reviewer round 1, B1).
    d_t_all = trial.get("delivered_t")
    d_i_all = trial.get("delivered_i")
    if d_t_all is not None and len(d_t_all) > 0:
        d_t = np.asarray(d_t_all)[mask(np.asarray(d_t_all))]
        d_i = np.asarray(d_i_all)[mask(np.asarray(d_t_all))] if d_i_all is not None else None
    else:
        d_t = np.array([])
        d_i = None

    s_rate_hz = len(s_t) / n_send / (eff_dur / 1000.0)
    r_rate_hz = len(r_t) / n_recv / (eff_dur / 1000.0)
    d_rate_hz = len(d_t) / n_send / (eff_dur / 1000.0) if len(d_t) else 0.0

    s_sig = lfp_proxy(s_t, n_send, eff_dur, bin_ms=bin_ms, smooth_ms=smooth_ms)
    r_sig = lfp_proxy(r_t, n_recv, eff_dur, bin_ms=bin_ms, smooth_ms=smooth_ms)
    d_sig = (lfp_proxy(d_t, n_send, eff_dur, bin_ms=bin_ms, smooth_ms=smooth_ms)
             if len(d_t) else np.zeros_like(s_sig))

    fS, pS = power_spectrum(s_sig, bin_ms)
    fR, pR = power_spectrum(r_sig, bin_ms)
    fD, pD = power_spectrum(d_sig, bin_ms)
    gS = gamma_band_mean(fS, pS)
    gR = gamma_band_mean(fR, pR)
    gD = gamma_band_mean(fD, pD)
    # peak in 30-90 Hz band
    def peak_band(f, p, lo=30, hi=90):
        m = (f >= lo) & (f <= hi)
        if not m.any() or p[m].max() <= 0:
            return None
        return float(f[m][np.argmax(p[m])])

    fc, c = sender_receiver_coherence(s_sig, r_sig, bin_ms)
    gcoh = gamma_band_mean(fc, c)
    # Delivered–sender coherence: manipulation-check metric
    if len(d_t):
        fdc, dc = sender_receiver_coherence(s_sig, d_sig, bin_ms)
        d_coh = gamma_band_mean(fdc, dc)
    else:
        d_coh = float("nan")

    gc = granger_causality(s_sig, r_sig, lag=5)
    te = transfer_entropy(s_sig, r_sig, n_bins=4, lag=2)

    return PerTrialMetrics(
        sender_rate_hz=s_rate_hz,
        receiver_rate_hz=r_rate_hz,
        delivered_rate_hz=d_rate_hz,
        sender_gamma_power=gS,
        receiver_gamma_power=gR,
        delivered_gamma_power=gD,
        sender_peak_hz=peak_band(fS, pS),
        receiver_peak_hz=peak_band(fR, pR),
        gamma_coherence=gcoh,
        delivered_coherence=d_coh,
        granger_F_sr=float(gc.get("F_send_to_recv", float("nan"))),
        granger_F_rs=float(gc.get("F_recv_to_send", float("nan"))),
        transfer_entropy=te,
        config_dict={
            "channel": trial["trial"]["channel"],
            "duration_ms": dur,
            "transient_ms": transient_ms,
        },
    )
