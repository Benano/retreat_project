"""
Experiment 1 (H1): phase-tuning curve.

Channel = intact, sweep conduction delay across one gamma cycle and measure
sender → receiver transfer at each delay.

Headline figure: decoding accuracy and γ-band coherence as functions of
conduction delay, with 95% CIs across seeds.

Saves:
  /analysis/results/exp1/trial_*.pkl          (per-trial dumps)
  /analysis/results/exp1/summary.json         (per-condition aggregates)
  /figures/fig_phase_tuning.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ping_group import PINGConfig
from network import (
    StimulusBank, FeedforwardConfig, TrialConfig, run_trial,
)
from channels import IntactChannel
from metrics import summarize_trial, build_decoder_features, decode_stimulus
from run_utils import save_pickle, save_json, trim_trial_for_disk


# ---------------------------------------------------------------------------
# Top-level worker (must be picklable for ProcessPoolExecutor)
# ---------------------------------------------------------------------------

def _trial_worker(args: dict) -> tuple[dict, dict]:
    """Run one (delay, seed, stimulus) trial and return (trimmed_trial, metrics)."""
    cfg_dict = args["cfg"]
    cfg_recv_dict = args["cfg_recv"]
    ff_dict = args["ff"]
    delay_ms = args["delay_ms"]
    stim_id = args["stim_id"]
    sender_seed = args["sender_seed"]
    receiver_seed = args["receiver_seed"]
    channel_seed = args["channel_seed"]
    duration_ms = args["duration_ms"]
    transient_ms = args["transient_ms"]

    cfg = PINGConfig(**cfg_dict)
    cfg_recv = PINGConfig(**cfg_recv_dict)
    bank = StimulusBank(n_stimuli=args["n_stimuli"], n_cells=cfg.N_E,
                        seed=args["bank_seed"],
                        bump_amplitude=args.get("bump_amplitude", 80.0))
    ff = FeedforwardConfig(**ff_dict)
    trial_cfg = TrialConfig(
        stimulus_id=stim_id,
        channel=IntactChannel(delay_ms=delay_ms),
        duration_ms=duration_ms,
        transient_ms=transient_ms,
        sender_seed=sender_seed,
        receiver_seed=receiver_seed,
        channel_seed=channel_seed,
    )
    out = run_trial(cfg, cfg_recv, bank, trial_cfg, ff)
    m = summarize_trial(out, transient_ms=transient_ms)
    trimmed = trim_trial_for_disk(out)
    return trimmed, asdict(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delays-ms", type=float, nargs="+",
                    default=[2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0])
    ap.add_argument("--n-seeds", type=int, default=20)
    ap.add_argument("--n-stimuli", type=int, default=4)
    ap.add_argument("--duration-ms", type=float, default=800.0)
    ap.add_argument("--transient-ms", type=float, default=200.0)
    ap.add_argument("--n-workers", type=int, default=int(os.environ.get("EXP_WORKERS", "4")))
    ap.add_argument("--out-dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "exp1"))
    ap.add_argument("--scale", type=str, choices=["dev", "full"], default="dev")
    ap.add_argument("--bump-amplitude", type=float, default=80.0,
                    help="pA peak extra drive per stimulus. Lower = harder task.")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "calibrated_ping.json")) as fh:
        cfg_dict = json.load(fh)
    cfg = PINGConfig(**cfg_dict)
    if args.scale == "full":
        cfg.N_E, cfg.N_I = 800, 200
    cfg_recv = PINGConfig(**cfg.to_dict())
    cfg_recv.name = "R"
    ff = FeedforwardConfig()

    # Build work list: every (delay, seed, stim) triple.
    work = []
    for delay in args.delays_ms:
        for seed in range(args.n_seeds):
            for stim in range(args.n_stimuli):
                work.append({
                    "cfg": cfg.to_dict(),
                    "cfg_recv": cfg_recv.to_dict(),
                    "ff": asdict(ff),
                    "delay_ms": float(delay),
                    "stim_id": int(stim),
                    "sender_seed": int(seed * 100 + stim),
                    "receiver_seed": int(seed * 100 + stim + 50000),
                    "channel_seed": int(seed * 100 + stim + 100000),
                    "duration_ms": float(args.duration_ms),
                    "transient_ms": float(args.transient_ms),
                    "n_stimuli": int(args.n_stimuli),
                    "bank_seed": 7,
                    "bump_amplitude": float(args.bump_amplitude),
                })

    print(f"Experiment 1 (H1 phase tuning, {args.scale} scale)")
    print(f"  delays: {args.delays_ms} ms")
    print(f"  n_seeds={args.n_seeds}, n_stimuli={args.n_stimuli}")
    print(f"  duration={args.duration_ms} ms (transient {args.transient_ms} ms)")
    print(f"  total trials: {len(work)}, workers={args.n_workers}")

    os.makedirs(args.out_dir, exist_ok=True)
    save_json(vars(args), os.path.join(args.out_dir, "run_config.json"))

    from run_utils import run_trials_parallel
    t0 = time.time()
    results = run_trials_parallel(work, _trial_worker, n_workers=args.n_workers,
                                  progress_every=max(5, len(work) // 20))
    print(f"Trials finished in {time.time() - t0:.0f} s")

    # Save trimmed trials and a flat metrics table
    metrics_rows = []
    for k, (trimmed, m) in enumerate(results):
        # Save sparsely to keep disk usage manageable: write only one trial per
        # (delay, seed) pair as an exemplar; metrics for all.
        if k % args.n_stimuli == 0:
            save_pickle(trimmed, os.path.join(args.out_dir, f"trial_{k:05d}.pkl"))
        row = dict(m)
        row.update({
            "delay_ms": work[k]["delay_ms"],
            "seed": k // args.n_stimuli // args.n_seeds * 0 + work[k]["sender_seed"] // 100,
            "stim_id": work[k]["stim_id"],
        })
        metrics_rows.append(row)
    save_json(metrics_rows, os.path.join(args.out_dir, "metrics_rows.json"))

    # ---- aggregate ----
    # Build trials list (in memory) for decoder per (delay, seed)
    delays = sorted({w["delay_ms"] for w in work})
    seeds = sorted({w["sender_seed"] // 100 for w in work})

    by_delay = {}
    for k, (trimmed, m) in enumerate(results):
        d = work[k]["delay_ms"]
        by_delay.setdefault(d, []).append((trimmed, m, work[k]))

    summary = []
    for d in delays:
        items = by_delay.get(d, [])
        if not items:
            continue
        trials = [t for (t, _m, _w) in items]
        mrows = [m for (_t, m, _w) in items]
        n_recv = trials[0]["receiver"]["config_recv"]["N_E"]
        X, y = build_decoder_features(trials, n_recv,
                                       transient_ms=args.transient_ms)
        n_folds = min(5, int(np.min(np.bincount(y))))
        if n_folds >= 2:
            dec = decode_stimulus(X, y, n_folds=n_folds, seed=0)
            decode_mean = dec["mean_accuracy"]
            decode_se = dec["se_accuracy"]
            decode_n = len(dec["accuracies"])
            decode_chance = dec["chance"]
        else:
            decode_mean, decode_se, decode_n, decode_chance = float("nan"), 0.0, 0, 1.0 / args.n_stimuli

        out_row = {
            "delay_ms": d,
            "decode_acc_mean": decode_mean,
            "decode_acc_sd": decode_se * np.sqrt(max(decode_n, 1)),
            "decode_acc_n": decode_n,
            "decode_chance": decode_chance,
        }
        # mean ± SEM across trials for the other metrics
        for k_ in ("gamma_coherence", "granger_F_sr", "transfer_entropy",
                   "sender_rate_hz", "receiver_rate_hz",
                   "sender_gamma_power", "receiver_gamma_power"):
            v = np.asarray([r[k_] for r in mrows], dtype=float)
            v = v[~np.isnan(v)]
            out_row[f"{k_}_mean"] = float(np.mean(v)) if len(v) else float("nan")
            out_row[f"{k_}_sd"] = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
            out_row[f"{k_}_n"] = int(len(v))
        summary.append(out_row)
    save_json(summary, os.path.join(args.out_dir, "summary.json"))

    # ---- figure ----
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    ds = np.array([r["delay_ms"] for r in summary])

    def plot_metric(ax, key, ylabel, color):
        m = np.array([r[f"{key}_mean"] for r in summary])
        sd = np.array([r[f"{key}_sd"] for r in summary])
        n = np.array([r[f"{key}_n"] for r in summary])
        se = sd / np.sqrt(np.maximum(n, 1))
        ax.errorbar(ds, m, yerr=1.96 * se, color=color, marker="o",
                    capsize=3, lw=1.5)
        ax.set_xlabel("Conduction delay (ms)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)

    plot_metric(axes[0], "decode_acc", "Decoding accuracy", "C0")
    axes[0].axhline(1.0 / args.n_stimuli, ls="--", color="gray", label="chance")
    axes[0].set_ylim(0, 1)
    axes[0].set_title("H1: stimulus decoding")
    axes[0].legend(loc="lower right")

    plot_metric(axes[1], "gamma_coherence", "γ-band coherence", "C2")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Sender → receiver γ coherence")

    plot_metric(axes[2], "granger_F_sr", "Granger F (sender → receiver)", "C3")
    axes[2].set_title("Directed influence")

    fig.suptitle(f"Experiment 1: phase tuning ({args.scale} scale, n={args.n_seeds} seeds)",
                 fontweight="bold")
    fig.tight_layout()
    fig_path = os.path.join(os.path.dirname(here), "figures", "fig_phase_tuning.png")
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    fig.savefig(fig_path, dpi=140)
    print(f"\nSaved {fig_path}")


if __name__ == "__main__":
    main()
