"""Smoke test: one trial of each channel, run metrics pipeline."""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ping_group import PINGConfig
from network import StimulusBank, FeedforwardConfig, TrialConfig, run_trial
from channels import IntactChannel, PhaseScrambleChannel, RateMatchedPoissonChannel
from metrics import summarize_trial


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "calibrated_ping.json")) as fh:
        cfg = PINGConfig(**json.load(fh))
    cfg_recv = PINGConfig(**cfg.to_dict())
    cfg_recv.name = "R"

    bank = StimulusBank(n_stimuli=2, n_cells=cfg.N_E, seed=7)
    ff = FeedforwardConfig()

    channels = [
        ("intact", IntactChannel(delay_ms=4.0)),
        ("scramble", PhaseScrambleChannel(algorithm="block_shuffle", block_ms=16.0, delay_ms=4.0)),
        ("poisson", RateMatchedPoissonChannel(smooth_ms=5.0, delay_ms=4.0)),
    ]

    header = (f"{'channel':10s}  {'srate':>5s}  {'rrate':>5s}  "
              f"{'sγpow':>7s}  {'rγpow':>7s}  {'γcoh':>5s}  "
              f"{'F_sr':>6s}  {'F_rs':>6s}  {'TE':>6s}")
    print(header)
    print("-" * len(header))
    for name, ch in channels:
        tr = TrialConfig(stimulus_id=0, channel=ch,
                         duration_ms=800.0, transient_ms=200.0,
                         sender_seed=0, receiver_seed=100, channel_seed=200)
        out = run_trial(cfg, cfg_recv, bank, tr, ff)
        m = summarize_trial(out)
        print(f"{name:10s}  {m.sender_rate_hz:5.1f}  {m.receiver_rate_hz:5.1f}  "
              f"{m.sender_gamma_power:7.2f}  {m.receiver_gamma_power:7.2f}  "
              f"{m.gamma_coherence:5.3f}  {m.granger_F_sr:6.2f}  "
              f"{m.granger_F_rs:6.2f}  {m.transfer_entropy:6.3f}")


if __name__ == "__main__":
    main()
