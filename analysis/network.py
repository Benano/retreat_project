"""
Sender → channel → receiver pipeline.

Architecture (spec Section 4.1):
  - Sender A: PING microcircuit, driven by a stimulus pattern across its
    E cells.
  - Channel: intact / phase_scramble / rate_matched_poisson (channels.py).
  - Receiver R: PING microcircuit. Sender's delivered spikes excite a
    topographically-aligned subset of receiver E cells via feedforward
    excitatory synapses with a conduction delay.

Implementation is two-stage:
  1. Simulate the sender in isolation with the stimulus drive. Record
     sender E spikes.
  2. Apply the channel to the sender E spike train (offline numpy).
  3. Simulate the receiver, feeding the delivered spikes through a
     SpikeGeneratorGroup → Synapses(EE feedforward).

This 2-stage design lets us hold the sender constant and compare channel
conditions with paired spike trains, which gives much tighter CIs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional

import brian2 as b2
import numpy as np

from ping_group import PINGConfig, PINGGroup
from channels import (
    IntactChannel,
    PhaseScrambleChannel,
    RateMatchedPoissonChannel,
    ChannelConfig,
    apply_channel,
)


mV = b2.mV
ms = b2.ms
Hz = b2.Hz
nS = b2.nS
pA = b2.pA


# ---------------------------------------------------------------------------
# Stimulus generation
# ---------------------------------------------------------------------------

@dataclass
class StimulusBank:
    """A bank of K stimuli, each a per-E-cell extra-current vector.

    Each stimulus is a localized Gaussian bump across the E cell index
    (think: a labeled-line / tuning-curve representation).
    """
    n_stimuli: int = 4
    n_cells: int = 200
    bump_width: float = 15.0      # cells (sigma of Gaussian)
    bump_amplitude: float = 80.0  # pA  (peak extra drive)
    baseline: float = 0.0         # pA  (added to all cells)
    seed: int = 0

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        # Evenly spaced bump centers, but with a small jitter so they aren't
        # exactly periodic.
        centers = np.linspace(0, self.n_cells - 1, self.n_stimuli + 1)[:-1]
        centers = centers + rng.uniform(-3, 3, self.n_stimuli)
        idx = np.arange(self.n_cells)
        self.patterns = np.stack([
            self.baseline + self.bump_amplitude *
            np.exp(-0.5 * ((idx - c) / self.bump_width) ** 2)
            for c in centers
        ])  # shape (K, N_E)
        self.centers = centers

    def get(self, stim_id: int) -> np.ndarray:
        """Return the per-E-cell extra-current vector for stimulus k."""
        return self.patterns[stim_id]


# ---------------------------------------------------------------------------
# Sender-only simulation
# ---------------------------------------------------------------------------

def run_sender(
    cfg: PINGConfig,
    duration_ms: float,
    stimulus_pa: Optional[np.ndarray],   # shape (N_E,) extra current
    rng_seed: int = 0,
) -> dict:
    """Simulate the sender PING group with an optional per-E-cell stimulus drive.

    Returns a dict with E-spike (t, i) arrays and population rate.
    """
    b2.start_scope()
    b2.defaultclock.dt = cfg.dt * ms
    grp = PINGGroup(cfg=cfg, rng_seed=rng_seed)
    if stimulus_pa is not None:
        grp.E.I_drive = (cfg.drive_E + stimulus_pa) * pA
    net = b2.Network(grp.brian_objects)
    net.run(duration_ms * ms, report=None)
    return {
        "spikes_E_t": np.asarray(grp.spikemon_E.t / ms),
        "spikes_E_i": np.asarray(grp.spikemon_E.i),
        "rate_E_t": np.asarray(grp.popmon_E.t / ms),
        "rate_E": np.asarray(grp.popmon_E.smooth_rate(window="gaussian", width=1 * ms) / Hz),
        "config": cfg.to_dict(),
        "seed": rng_seed,
        "duration_ms": duration_ms,
        "stimulus_pa": None if stimulus_pa is None else stimulus_pa.tolist(),
    }


# ---------------------------------------------------------------------------
# Receiver simulation given delivered spikes
# ---------------------------------------------------------------------------

@dataclass
class FeedforwardConfig:
    """How sender E cells project onto receiver E cells (and optionally I)."""
    # Each sender cell j connects to receiver cells in [j-half_width, j+half_width]
    # (modulo N_E) — a topographic mapping that lets the receiver inherit the
    # stimulus bump pattern.
    half_width: int = 8
    p_within_window: float = 0.5
    g_FF_to_E: float = 0.45    # nS per delivered spike onto receiver E cell
    g_FF_to_I: float = 0.10    # nS per delivered spike onto receiver I cell
    fraction_to_I: float = 0.10  # fraction of FF synapses that also hit I cells


def run_receiver(
    cfg_recv: PINGConfig,
    delivered_t: np.ndarray,     # ms
    delivered_i: np.ndarray,     # source neuron index (sender E)
    n_sender_E: int,
    duration_ms: float,
    ff: FeedforwardConfig,
    rng_seed: int = 0,
) -> dict:
    """Run the receiver PING group, driven by ``delivered_*`` spikes through
    a feedforward EE projection.
    """
    b2.start_scope()
    b2.defaultclock.dt = cfg_recv.dt * ms

    grp = PINGGroup(cfg=cfg_recv, rng_seed=rng_seed)
    # start_scope() above prevents name collisions with the sender simulation.

    # SpikeGeneratorGroup carries delivered spikes
    sg = b2.SpikeGeneratorGroup(
        n_sender_E,
        indices=np.asarray(delivered_i, dtype=int),
        times=np.asarray(delivered_t) * ms,
        name="ff_sg",
    )

    # Feedforward synapses: topographic E→E with ±half_width window
    syn_E = b2.Synapses(sg, grp.E,
                        on_pre=f"g_e_post += {ff.g_FF_to_E}*nS",
                        delay=0 * ms,   # conduction delay is already in delivered_t
                        name="ff_syn_E")
    # Build connectivity index arrays
    rng = np.random.default_rng(rng_seed)
    src_list, tgt_list = [], []
    for j in range(n_sender_E):
        # receiver E cells in window around j
        targets = (j + np.arange(-ff.half_width, ff.half_width + 1)) % cfg_recv.N_E
        # subsample
        keep = rng.random(len(targets)) < ff.p_within_window
        for t in targets[keep]:
            src_list.append(j)
            tgt_list.append(int(t))
    syn_E.connect(i=np.array(src_list), j=np.array(tgt_list))

    # Optional FF onto I cells: small fraction of FF synapses
    if ff.fraction_to_I > 0:
        syn_I = b2.Synapses(sg, grp.I,
                            on_pre=f"g_e_post += {ff.g_FF_to_I}*nS",
                            delay=0 * ms,
                            name="ff_syn_I")
        src_I, tgt_I = [], []
        for j in range(n_sender_E):
            if rng.random() < ff.fraction_to_I:
                tgt = rng.integers(0, cfg_recv.N_I)
                src_I.append(j)
                tgt_I.append(int(tgt))
        if src_I:
            syn_I.connect(i=np.array(src_I), j=np.array(tgt_I))
        objects_extra = [syn_I]
    else:
        objects_extra = []

    net = b2.Network(grp.brian_objects + [sg, syn_E] + objects_extra)
    net.run(duration_ms * ms, report=None)

    return {
        "spikes_E_t": np.asarray(grp.spikemon_E.t / ms),
        "spikes_E_i": np.asarray(grp.spikemon_E.i),
        "spikes_I_t": np.asarray(grp.spikemon_I.t / ms),
        "spikes_I_i": np.asarray(grp.spikemon_I.i),
        "rate_E_t": np.asarray(grp.popmon_E.t / ms),
        "rate_E": np.asarray(grp.popmon_E.smooth_rate(window="gaussian", width=1 * ms) / Hz),
        "rate_I": np.asarray(grp.popmon_I.smooth_rate(window="gaussian", width=1 * ms) / Hz),
        "config_recv": cfg_recv.to_dict(),
        "ff": asdict(ff),
        "seed": rng_seed,
        "duration_ms": duration_ms,
    }


# ---------------------------------------------------------------------------
# Full sender → channel → receiver trial
# ---------------------------------------------------------------------------

@dataclass
class TrialConfig:
    """One trial: stimulus id, channel mode, seeds for sender / receiver / channel."""
    stimulus_id: int = 0
    channel: ChannelConfig = field(default_factory=lambda: IntactChannel(delay_ms=4.0))
    duration_ms: float = 1200.0
    transient_ms: float = 200.0
    sender_seed: int = 0
    receiver_seed: int = 1000
    channel_seed: int = 2000


def run_trial(
    cfg_sender: PINGConfig,
    cfg_recv: PINGConfig,
    stim_bank: StimulusBank,
    trial: TrialConfig,
    ff: FeedforwardConfig,
) -> dict:
    """Run one sender → channel → receiver trial. Returns aggregated dict."""
    stim = stim_bank.get(trial.stimulus_id)

    sender = run_sender(cfg_sender, trial.duration_ms, stim, rng_seed=trial.sender_seed)

    rng_chan = np.random.default_rng(trial.channel_seed)
    delivered_t, delivered_i = apply_channel(
        sender["spikes_E_t"], sender["spikes_E_i"],
        cfg_sender.N_E, trial.duration_ms, trial.channel, rng=rng_chan,
    )

    receiver = run_receiver(
        cfg_recv, delivered_t, delivered_i,
        n_sender_E=cfg_sender.N_E,
        duration_ms=trial.duration_ms,
        ff=ff,
        rng_seed=trial.receiver_seed,
    )

    return {
        "trial": {
            "stimulus_id": trial.stimulus_id,
            "channel": _channel_to_dict(trial.channel),
            "duration_ms": trial.duration_ms,
            "transient_ms": trial.transient_ms,
            "sender_seed": trial.sender_seed,
            "receiver_seed": trial.receiver_seed,
            "channel_seed": trial.channel_seed,
        },
        "sender": sender,
        "receiver": receiver,
        "delivered_t": delivered_t,
        "delivered_i": delivered_i,
    }


def _channel_to_dict(c):
    d = asdict(c)
    d["__type__"] = type(c).__name__
    return d


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke():
    """Run one trial of each channel and print delivered/receiver spike counts."""
    with open("analysis/calibrated_ping.json") as fh:
        cfg_dict = json.load(fh)
    cfg = PINGConfig(**cfg_dict)
    cfg_recv = PINGConfig(**cfg_dict)
    cfg_recv.name = "R"
    bank = StimulusBank(n_stimuli=2, n_cells=cfg.N_E, seed=7)
    ff = FeedforwardConfig()

    for mode_name, ch in [
        ("intact", IntactChannel(delay_ms=4.0)),
        ("scramble", PhaseScrambleChannel(algorithm="block_shuffle", block_ms=16.0, delay_ms=4.0)),
        ("poisson", RateMatchedPoissonChannel(smooth_ms=5.0, delay_ms=4.0)),
    ]:
        trial = TrialConfig(stimulus_id=0, channel=ch,
                            duration_ms=800.0, transient_ms=200.0,
                            sender_seed=0, receiver_seed=100, channel_seed=200)
        out = run_trial(cfg, cfg_recv, bank, trial, ff)
        s_n = len(out["sender"]["spikes_E_t"])
        d_n = len(out["delivered_t"])
        r_n = len(out["receiver"]["spikes_E_t"])
        print(f"  {mode_name:10s}  sender={s_n:5d}  delivered={d_n:5d}  receiver_E={r_n:5d}")


if __name__ == "__main__":
    _smoke()
