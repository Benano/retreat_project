"""
Unit tests for the channels. THE phase-scramble channel's triple check
(rate preserved, power preserved, coherence reduced) is the manipulation
that the whole experiment rests on (spec Section 4.2; CLAUDE.md guardrail 4).

These tests use a *synthetic* gamma-modulated Poisson spike source:
  rate(t) = R0 * (1 + m * sin(2*pi*f_gamma*t))
spikes drawn independently per neuron via thinning. The receiver's "input
coherence" is operationalized as the magnitude-squared coherence between
the smoothed sender population rate and the smoothed delivered population
rate, in the gamma band.

We expect:
  intact            -> coherence ~= 1 in gamma band (modulo noise)
  phase_scramble    -> coherence << intact, with rate and power preserved
  rate_matched_poisson -> coherence << intact, rate envelope preserved
                          (fine power destroyed)
"""
from __future__ import annotations

import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channels import (
    IntactChannel,
    PhaseScrambleChannel,
    RateMatchedPoissonChannel,
    apply_channel,
    coherence,
    gamma_band_mean,
    population_rate,
    power_spectrum,
)


# --- synthetic gamma-modulated Poisson source ------------------------------

def synthetic_gamma_spikes(
    n_neurons: int = 200,
    duration_ms: float = 4000.0,
    R0_hz: float = 30.0,
    modulation: float = 0.6,
    f_gamma: float = 60.0,
    rng_seed: int = 0,
):
    """Generate inhomogeneous Poisson spikes with a shared gamma-modulated rate."""
    rng = np.random.default_rng(rng_seed)
    dt = 0.1  # ms
    t = np.arange(0, duration_ms, dt)
    rate_per_ms = R0_hz / 1000.0 * (1.0 + modulation * np.sin(2 * np.pi * f_gamma * t / 1000.0))
    rate_per_ms = np.clip(rate_per_ms, 0, None)
    # Bernoulli per bin per neuron
    spikes_t_list, spikes_i_list = [], []
    for k in range(n_neurons):
        u = rng.random(len(t))
        fires = u < rate_per_ms * dt  # per-bin probability
        ts = t[fires]
        spikes_t_list.append(ts)
        spikes_i_list.append(np.full(len(ts), k, dtype=np.int64))
    spikes_t = np.concatenate(spikes_t_list)
    spikes_i = np.concatenate(spikes_i_list)
    order = np.argsort(spikes_t, kind="stable")
    return spikes_t[order], spikes_i[order]


# --- helpers ---------------------------------------------------------------

def _pop_signal(spikes_t, duration_ms, bin_ms=1.0):
    _, rate = population_rate(spikes_t, duration_ms, bin_ms=bin_ms)
    # remove mean to avoid DC dominating coherence
    return rate - rate.mean()


def _report(name, sender_t, delivered_t, duration_ms):
    bin_ms = 1.0
    sx = _pop_signal(sender_t, duration_ms, bin_ms)
    sy = _pop_signal(delivered_t, duration_ms, bin_ms)
    # rates
    r_sender = len(sender_t) / (duration_ms / 1000.0)
    r_delivered = len(delivered_t) / (duration_ms / 1000.0)
    # power
    f_p, p_sender = power_spectrum(sx, bin_ms)
    _, p_delivered = power_spectrum(sy, bin_ms)
    gamma_p_sender = gamma_band_mean(f_p, p_sender)
    gamma_p_delivered = gamma_band_mean(f_p, p_delivered)
    # coherence
    f_c, c = coherence(sx, sy, bin_ms)
    gamma_coh = gamma_band_mean(f_c, c)
    return {
        "name": name,
        "rate_sender_hz": r_sender,
        "rate_delivered_hz": r_delivered,
        "rate_ratio": r_delivered / r_sender if r_sender > 0 else np.nan,
        "gamma_power_sender": gamma_p_sender,
        "gamma_power_delivered": gamma_p_delivered,
        "gamma_power_ratio": gamma_p_delivered / gamma_p_sender if gamma_p_sender > 0 else np.nan,
        "gamma_coherence": gamma_coh,
    }


# --- tests -----------------------------------------------------------------

def run_all():
    n_neurons = 200
    duration_ms = 4000.0
    print(f"Synthesizing {n_neurons} gamma-modulated Poisson neurons over {duration_ms:.0f} ms...")
    s_t, s_i = synthetic_gamma_spikes(n_neurons=n_neurons, duration_ms=duration_ms)
    rng = np.random.default_rng(42)

    # --- intact
    cfg_i = IntactChannel(delay_ms=4.0)
    t_i, i_i = apply_channel(s_t, s_i, n_neurons, duration_ms, cfg_i, rng)
    r_intact = _report("intact", s_t, t_i, duration_ms)

    # --- phase scramble (block-shuffle: rate + power preserved, coherence destroyed)
    cfg_ps = PhaseScrambleChannel(algorithm="block_shuffle", block_ms=16.0, delay_ms=4.0)
    t_ps, _ = apply_channel(s_t, s_i, n_neurons, duration_ms, cfg_ps, rng)
    r_ps = _report("phase_scramble_block", s_t, t_ps, duration_ms)

    # --- phase scramble (jitter alternative: stronger but power-reducing)
    cfg_ps_j = PhaseScrambleChannel(algorithm="jitter", window_ms=16.0, delay_ms=4.0)
    t_ps_j, _ = apply_channel(s_t, s_i, n_neurons, duration_ms, cfg_ps_j, rng)
    r_ps_j = _report("phase_scramble_jitter", s_t, t_ps_j, duration_ms)

    # --- rate-matched Poisson
    cfg_p = RateMatchedPoissonChannel(smooth_ms=5.0, delay_ms=4.0)
    t_p, _ = apply_channel(s_t, s_i, n_neurons, duration_ms, cfg_p, rng)
    r_p = _report("rate_matched_poisson", s_t, t_p, duration_ms)

    # ---- assertions
    failures = []

    def check(cond, msg):
        if cond:
            print(f"  PASS  {msg}")
        else:
            print(f"  FAIL  {msg}")
            failures.append(msg)

    print("\n=== intact ===")
    print(r_intact)
    check(0.95 < r_intact["rate_ratio"] < 1.05, "intact: rate preserved within +/-5%")
    check(r_intact["gamma_coherence"] > 0.5, "intact: gamma coherence > 0.5")

    print("\n=== phase_scramble (block_shuffle) ===")
    print(r_ps)
    check(0.99 < r_ps["rate_ratio"] < 1.01, "block_shuffle: rate preserved within +/-1%")
    check(0.8 < r_ps["gamma_power_ratio"] < 1.25,
          "block_shuffle: gamma power within +/-25% of sender (power preserved)")
    check(r_ps["gamma_coherence"] < 0.5 * r_intact["gamma_coherence"],
          "block_shuffle: gamma coherence <50% of intact (coherence destroyed)")
    check(r_ps["gamma_coherence"] < 0.3,
          "block_shuffle: absolute gamma coherence < 0.3")

    print("\n=== phase_scramble (jitter, comparison) ===")
    print(r_ps_j)
    check(0.95 < r_ps_j["rate_ratio"] < 1.05, "jitter: rate preserved within +/-5%")
    # Jitter is *not* expected to preserve power (acts as low-pass) — we just
    # confirm coherence is destroyed.
    check(r_ps_j["gamma_coherence"] < 0.5 * r_intact["gamma_coherence"],
          "jitter: gamma coherence <50% of intact")

    print("\n=== rate_matched_poisson ===")
    print(r_p)
    check(0.7 < r_p["rate_ratio"] < 1.3,
          "rate_matched_poisson: rate preserved within +/-30% (Poisson noise)")
    check(r_p["gamma_coherence"] < r_intact["gamma_coherence"],
          "rate_matched_poisson: gamma coherence reduced vs intact")

    print()
    if failures:
        print(f"=== {len(failures)} FAILURE(S) ===")
        for m in failures:
            print(" -", m)
        return 1
    print("=== ALL CHANNEL TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
