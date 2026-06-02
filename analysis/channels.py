"""
Phase-scramble and rate-matched Poisson channels.

These are the *experimental intervention* of the project (spec Section 4.2).
They take a sender's spike train (per-neuron arrays of spike times) and emit
delivered spike trains for the receiver, manipulating phase/coherence while
attempting to preserve marginal rate statistics and the power spectrum.

Channels are implemented as offline transformations on numpy arrays. The
caller is responsible for feeding the resulting spikes into Brian2 via a
SpikeGeneratorGroup (see network.py).

Three channel modes (spec Section 4.2):
  1. ``intact``                 — delivered = sender spikes shifted by a fixed
                                  conduction delay. Coherence preserved; the
                                  delay sets the imposed phase offset.
  2. ``phase_scramble``         — each spike's time is jittered within a sliding
                                  window of width W centered on the spike, so
                                  per-window spike count is preserved but the
                                  fine timing relative to the gamma cycle is
                                  destroyed.
  3. ``rate_matched_poisson``   — replace each cell's spike train with an
                                  inhomogeneous Poisson process whose
                                  instantaneous rate matches the cell's
                                  smoothed rate.

All channels return per-neuron arrays of spike times in ms.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Channel configs
# ---------------------------------------------------------------------------

@dataclass
class IntactChannel:
    """Pass-through with a fixed conduction delay."""
    delay_ms: float = 4.0


@dataclass
class PhaseScrambleChannel:
    """Destroy sender-delivered phase alignment while preserving rate and power.

    Two algorithms:

    - ``"block_shuffle"`` (default, recommended): chunk the spike train into
      consecutive blocks of width ``block_ms`` (≈ one gamma cycle), then
      apply a random permutation over block positions. Each block's internal
      structure — including its cell-to-cell co-firing pattern — is
      preserved, so the gamma envelope and power spectrum are preserved.
      The temporal alignment with the sender at any specific time is
      destroyed, so inter-areal coherence collapses. This is the channel
      Section 4.2 of the spec asks for: phase relationship destroyed, rate
      and power preserved.

    - ``"jitter"``: each spike's time is independently jittered uniformly
      within ±window_ms/2. This destroys coherence more aggressively but
      *also* reduces gamma power (the window acts as a low-pass), so it is
      not power-preserving. Kept as a stronger-destruction comparison.

    The block_shuffle algorithm preserves per-block spike count exactly and
    per-cell total rate exactly.
    """
    algorithm: str = "block_shuffle"   # "block_shuffle" or "jitter"
    block_ms: float = 16.0             # block width for block_shuffle (~1 gamma cycle)
    window_ms: float = 16.0            # jitter window (only used if algorithm="jitter")
    delay_ms: float = 4.0
    refractory_ms: float = 1.0         # honor receiver-side refractory (jitter mode)


@dataclass
class RateMatchedPoissonChannel:
    """Replace each cell's spike train with an inhomogeneous Poisson process.

    The instantaneous rate is the cell's smoothed firing rate (Gaussian
    kernel of width ``smooth_ms``). This destroys *all* fine temporal
    structure (gamma plus everything else) while matching the slow rate.
    """
    smooth_ms: float = 5.0
    delay_ms: float = 4.0


ChannelConfig = IntactChannel | PhaseScrambleChannel | RateMatchedPoissonChannel


# ---------------------------------------------------------------------------
# Channel application
# ---------------------------------------------------------------------------

def apply_channel(
    spikes_t: np.ndarray,       # spike times in ms (1D)
    spikes_i: np.ndarray,       # neuron index for each spike (1D)
    n_neurons: int,
    duration_ms: float,
    cfg: ChannelConfig,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply a channel to a flat (t, i) spike record. Returns (t', i') sorted by t'."""
    rng = rng or np.random.default_rng(0)

    if isinstance(cfg, IntactChannel):
        out_t = spikes_t + cfg.delay_ms
        out_i = spikes_i.copy()

    elif isinstance(cfg, PhaseScrambleChannel):
        out_t, out_i = _phase_scramble(spikes_t, spikes_i, n_neurons,
                                       duration_ms, cfg, rng)

    elif isinstance(cfg, RateMatchedPoissonChannel):
        out_t, out_i = _rate_matched_poisson(spikes_t, spikes_i, n_neurons,
                                             duration_ms, cfg, rng)

    else:
        raise ValueError(f"Unknown channel config: {cfg!r}")

    # Keep within simulation window
    mask = (out_t >= 0) & (out_t < duration_ms)
    out_t, out_i = out_t[mask], out_i[mask]

    # Deduplicate: SpikeGeneratorGroup in Brian2 forbids the same neuron firing
    # twice in the same dt bin. After channel transforms (especially block
    # shuffle) within-cell collisions can occur. We push collisions BACK by
    # min_dt rather than forward to avoid sliding spikes out of the trial
    # window (which was a source of net spike loss caught by reviewer B1).
    if len(out_t) > 0:
        min_dt = 0.11  # > Brian2 default dt of 0.1 ms
        order = np.lexsort((out_t, out_i))
        out_t = out_t[order]
        out_i = out_i[order]
        prev_i = -1
        prev_t = -np.inf
        for k in range(len(out_t)):
            if out_i[k] != prev_i:
                prev_i = out_i[k]
                prev_t = out_t[k]
                continue
            if out_t[k] < prev_t + min_dt:
                # nudge forward; if this would exit the window, leave it and
                # rely on the duration mask (rare for sensible min_dt)
                out_t[k] = prev_t + min_dt
            prev_t = out_t[k]

    order = np.argsort(out_t, kind="stable")
    return out_t[order], out_i[order]


def _phase_scramble(spikes_t, spikes_i, n_neurons, duration_ms, cfg, rng):
    delay = cfg.delay_ms
    if cfg.algorithm == "block_shuffle":
        T_b = cfg.block_ms
        # Use INTEGER number of full blocks that fit in the trial. Spikes in
        # the partial trailing block (if any) are passed through with a small
        # uniform jitter rather than scrambled, so they aren't dropped.
        n_blocks = int(duration_ms // T_b)
        usable_end_ms = n_blocks * T_b

        block_idx = np.floor(spikes_t / T_b).astype(np.int64)
        within_block_offset = spikes_t - block_idx * T_b

        # Random permutation over block positions, shared across cells.
        perm = rng.permutation(n_blocks)

        # In-range spikes: map block b -> perm[b]
        in_range = block_idx < n_blocks
        new_block_start = np.zeros_like(spikes_t)
        new_block_start[in_range] = perm[block_idx[in_range]] * T_b
        # Partial-block spikes: keep their original block position so we don't
        # drop them and don't introduce a wraparound bias.
        new_block_start[~in_range] = block_idx[~in_range] * T_b

        # Apply delay with WRAP-AROUND inside the usable window, so spikes
        # near the end of a block don't slide past duration_ms and get culled.
        new_t = new_block_start + within_block_offset + delay
        wrap_mask = (new_t >= usable_end_ms) & in_range
        new_t[wrap_mask] -= usable_end_ms  # wrap into the usable window
        return new_t, spikes_i.copy()

    elif cfg.algorithm == "jitter":
        W = cfg.window_ms
        new_t = spikes_t + rng.uniform(-W / 2, W / 2, size=spikes_t.shape)
        new_t = new_t + delay
        if cfg.refractory_ms > 0:
            for k in range(n_neurons):
                mask = spikes_i == k
                if not mask.any():
                    continue
                idx = np.where(mask)[0]
                order = np.argsort(new_t[idx], kind="stable")
                sorted_idx = idx[order]
                ts = new_t[sorted_idx]
                for j in range(1, len(ts)):
                    if ts[j] < ts[j - 1] + cfg.refractory_ms:
                        ts[j] = ts[j - 1] + cfg.refractory_ms
                new_t[sorted_idx] = ts
        return new_t, spikes_i.copy()

    else:
        raise ValueError(f"Unknown phase-scramble algorithm: {cfg.algorithm!r}")


def _rate_matched_poisson(spikes_t, spikes_i, n_neurons, duration_ms, cfg, rng):
    smooth = cfg.smooth_ms
    delay = cfg.delay_ms
    # Bin rate per neuron at 1 ms, Gaussian-smooth, then thin a 1 kHz Poisson
    # process per cell at the smoothed rate. Time-rescaling theorem trick.
    dt = 1.0  # ms
    n_bins = int(np.ceil(duration_ms / dt))
    out_t_list, out_i_list = [], []
    sigma_bins = max(smooth / dt, 1.0)
    # Pre-build a small Gaussian kernel (±4 sigma).
    half = int(np.ceil(4 * sigma_bins))
    x = np.arange(-half, half + 1)
    kernel = np.exp(-0.5 * (x / sigma_bins) ** 2)
    kernel /= kernel.sum()
    for k in range(n_neurons):
        mask = spikes_i == k
        if not mask.any():
            continue
        ts = spikes_t[mask]
        counts, _ = np.histogram(ts, bins=n_bins, range=(0, n_bins * dt))
        rate_per_ms = np.convolve(counts, kernel, mode="same")  # spikes per ms
        # Draw Poisson counts per ms bin from the smoothed rate
        new_counts = rng.poisson(rate_per_ms)
        # Place spikes uniformly within each ms bin
        nz = np.where(new_counts > 0)[0]
        for b in nz:
            n = new_counts[b]
            out_t_list.append(b * dt + rng.uniform(0, dt, size=n))
            out_i_list.append(np.full(n, k, dtype=np.int64))
    if not out_t_list:
        return np.empty(0), np.empty(0, dtype=np.int64)
    out_t = np.concatenate(out_t_list) + delay
    out_i = np.concatenate(out_i_list)
    return out_t, out_i


# ---------------------------------------------------------------------------
# Manipulation-check utilities — used by unit tests and reported alongside
# every experimental condition (CLAUDE.md guardrail 4).
# ---------------------------------------------------------------------------

def population_rate(spikes_t: np.ndarray, duration_ms: float,
                    bin_ms: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Population firing-rate time series (Hz averaged over the population)."""
    n_bins = int(np.ceil(duration_ms / bin_ms))
    counts, edges = np.histogram(spikes_t, bins=n_bins, range=(0, n_bins * bin_ms))
    rate = counts / (bin_ms / 1000.0)
    t = (edges[:-1] + edges[1:]) / 2
    return t, rate


def power_spectrum(signal: np.ndarray, dt_ms: float,
                   freqs_range_hz: tuple[float, float] = (1.0, 200.0)
                   ) -> tuple[np.ndarray, np.ndarray]:
    """One-sided power spectrum via Welch."""
    from scipy.signal import welch
    fs = 1000.0 / dt_ms  # Hz
    f, p = welch(signal, fs=fs, nperseg=min(len(signal), int(fs)))
    band = (f >= freqs_range_hz[0]) & (f <= freqs_range_hz[1])
    return f[band], p[band]


def coherence(x: np.ndarray, y: np.ndarray, dt_ms: float,
              freqs_range_hz: tuple[float, float] = (1.0, 200.0)
              ) -> tuple[np.ndarray, np.ndarray]:
    """Magnitude-squared coherence via scipy.signal.coherence."""
    from scipy.signal import coherence as scoh
    fs = 1000.0 / dt_ms
    f, c = scoh(x, y, fs=fs, nperseg=min(len(x), int(fs)))
    band = (f >= freqs_range_hz[0]) & (f <= freqs_range_hz[1])
    return f[band], c[band]


def gamma_band_mean(f: np.ndarray, v: np.ndarray,
                    band_hz: tuple[float, float] = (30.0, 90.0)) -> float:
    """Mean of ``v`` over the gamma band."""
    mask = (f >= band_hz[0]) & (f <= band_hz[1])
    if not mask.any():
        return float("nan")
    return float(np.mean(v[mask]))
