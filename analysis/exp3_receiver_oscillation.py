"""
Experiment 3 (H3): does the receiver need to oscillate for phase-gating?

Predictions (spec §3, Table H3):
  - CTC-causal: disabling the receiver's E↔I loop abolishes the phase-gating
    effect → intact and scramble should decode equally with a non-oscillating
    receiver.
  - Epiphenomenal: coherence and transfer persist even with a non-oscillating
    receiver → intact > scramble persists.

We run Exp 2 (intact vs scramble at delay 8 ms) with the receiver's
within-group E↔I coupling set to zero (PINGConfig.disable_oscillation=True).
Compare to the baseline (oscillating-receiver) Exp 2 result.

Saves to /analysis/results/exp3_disabled/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ping_group import PINGConfig
from network import StimulusBank, FeedforwardConfig, TrialConfig, run_trial
from channels import IntactChannel, PhaseScrambleChannel
from metrics import summarize_trial, build_decoder_features
from run_utils import save_pickle, save_json, trim_trial_for_disk, run_trials_parallel


def _trial_worker(args: dict) -> tuple[dict, dict]:
    cfg = PINGConfig(**args["cfg"])
    cfg_recv = PINGConfig(**args["cfg_recv"])
    bank = StimulusBank(n_stimuli=args["n_stimuli"], n_cells=cfg.N_E,
                        seed=args["bank_seed"],
                        bump_amplitude=args.get("bump_amplitude", 30.0))
    ff = FeedforwardConfig(**args["ff"])
    if args["condition"] == "intact":
        ch = IntactChannel(delay_ms=args["delay_ms"])
    elif args["condition"] == "scramble":
        ch = PhaseScrambleChannel(algorithm="block_shuffle", block_ms=16.0,
                                  delay_ms=args["delay_ms"])
    else:
        raise ValueError(args["condition"])
    trial_cfg = TrialConfig(
        stimulus_id=args["stim_id"],
        channel=ch,
        duration_ms=args["duration_ms"],
        transient_ms=args["transient_ms"],
        sender_seed=args["sender_seed"],
        receiver_seed=args["receiver_seed"],
        channel_seed=args["channel_seed"],
    )
    out = run_trial(cfg, cfg_recv, bank, trial_cfg, ff)
    m = summarize_trial(out, transient_ms=args["transient_ms"])
    row = asdict(m)
    row["condition"] = args["condition"]
    row["seed"] = args["sender_seed"] // 100
    row["stim_id"] = args["stim_id"]
    return trim_trial_for_disk(out), row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay-ms", type=float, default=8.0)
    ap.add_argument("--n-seeds", type=int, default=20)
    ap.add_argument("--n-stimuli", type=int, default=4)
    ap.add_argument("--duration-ms", type=float, default=500.0)
    ap.add_argument("--transient-ms", type=float, default=150.0)
    ap.add_argument("--bump-amplitude", type=float, default=30.0)
    ap.add_argument("--n-workers", type=int, default=4)
    ap.add_argument("--scale", choices=["dev", "full"], default="full")
    ap.add_argument("--conditions", nargs="+", default=["intact", "scramble"])
    ap.add_argument("--out-dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "results", "exp3_disabled"))
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "calibrated_ping.json")) as fh:
        cfg_dict = json.load(fh)
    cfg = PINGConfig(**cfg_dict)             # sender — normal PING
    if args.scale == "full":
        cfg.N_E, cfg.N_I = 800, 200

    # Receiver: same parameters but disable_oscillation = True
    cfg_recv = PINGConfig(**cfg.to_dict())
    cfg_recv.name = "R"
    cfg_recv.disable_oscillation = True

    ff = FeedforwardConfig()

    work = []
    for cond in args.conditions:
        for seed in range(args.n_seeds):
            for stim in range(args.n_stimuli):
                work.append({
                    "cfg": cfg.to_dict(),
                    "cfg_recv": cfg_recv.to_dict(),
                    "ff": asdict(ff),
                    "condition": cond,
                    "delay_ms": float(args.delay_ms),
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

    print(f"Experiment 3 (H3, receiver oscillation disabled, {args.scale})")
    print(f"  conditions: {args.conditions}; delay={args.delay_ms} ms")
    print(f"  n_seeds={args.n_seeds}, n_stim={args.n_stimuli}")
    print(f"  total trials: {len(work)}, workers={args.n_workers}")
    print(f"  receiver g_EI = {cfg_recv.g_EI if not cfg_recv.disable_oscillation else 0} "
          f"(effective; cfg flag = {cfg_recv.disable_oscillation})")

    os.makedirs(args.out_dir, exist_ok=True)
    save_json(vars(args), os.path.join(args.out_dir, "run_config.json"))

    t0 = time.time()
    results = run_trials_parallel(work, _trial_worker, n_workers=args.n_workers,
                                  progress_every=max(5, len(work) // 20))
    print(f"Trials finished in {time.time() - t0:.0f} s")

    metrics_rows = []
    by_cond: dict[str, list[dict]] = {c: [] for c in args.conditions}
    for k, (trimmed, m) in enumerate(results):
        cond = work[k]["condition"]
        save_pickle(trimmed, os.path.join(args.out_dir, cond, f"trial_{k:05d}.pkl"))
        metrics_rows.append(m)
        by_cond[cond].append(trimmed)
    save_json(metrics_rows, os.path.join(args.out_dir, "metrics_rows.json"))

    # Per-condition aggregation with leave-one-seed-out CV decoder
    from sklearn.model_selection import LeaveOneGroupOut
    from sklearn.linear_model import LogisticRegression
    summary = []
    for cond in args.conditions:
        trials = by_cond[cond]
        cond_rows = [r for r in metrics_rows if r["condition"] == cond]
        n_recv = trials[0]["receiver"]["config_recv"]["N_E"]
        seeds_arr = np.array([t["trial"]["sender_seed"] // 100 for t in trials])
        X, y = build_decoder_features(trials, n_recv, transient_ms=args.transient_ms)
        Xs = X.astype(float)
        Xs = (Xs - Xs.mean(1, keepdims=True)) / (Xs.std(1, keepdims=True) + 1e-6)
        logo = LeaveOneGroupOut()
        per_seed_acc = []
        for tr, te in logo.split(Xs, y, groups=seeds_arr):
            if len(np.unique(y[tr])) < 2:
                continue
            clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")
            clf.fit(Xs[tr], y[tr])
            per_seed_acc.append(float(clf.score(Xs[te], y[te])))
        per_seed_acc = np.array(per_seed_acc)
        out_row = {
            "condition": cond,
            "decode_acc_mean": float(np.mean(per_seed_acc)),
            "decode_acc_se": float(np.std(per_seed_acc, ddof=1) / np.sqrt(len(per_seed_acc))),
            "decode_acc_per_seed": per_seed_acc.tolist(),
            "decode_chance": 1.0 / args.n_stimuli,
            "n_trials": len(trials),
        }
        for k_ in ("gamma_coherence", "delivered_coherence",
                   "granger_F_sr", "transfer_entropy",
                   "sender_rate_hz", "receiver_rate_hz", "delivered_rate_hz",
                   "sender_gamma_power", "receiver_gamma_power",
                   "delivered_gamma_power"):
            v = np.asarray([r[k_] for r in cond_rows], dtype=float)
            v = v[~np.isnan(v)]
            out_row[f"{k_}_mean"] = float(np.mean(v)) if len(v) else float("nan")
            out_row[f"{k_}_sd"] = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
            out_row[f"{k_}_n"] = int(len(v))
        summary.append(out_row)
    save_json(summary, os.path.join(args.out_dir, "summary.json"))

    # Paired Wilcoxon
    try:
        from scipy.stats import wilcoxon
        if {"intact", "scramble"}.issubset(set(args.conditions)):
            row_i = next(s for s in summary if s["condition"] == "intact")
            row_s = next(s for s in summary if s["condition"] == "scramble")
            a = np.array(row_i["decode_acc_per_seed"])
            b = np.array(row_s["decode_acc_per_seed"])
            w_stat, w_p = wilcoxon(a, b)
            print(f"Paired Wilcoxon intact vs scramble (per seed, n={len(a)}): "
                  f"W={w_stat:.2f}, p={w_p:.4f}")
            save_json({"intact_vs_scramble":
                       {"W": float(w_stat), "p": float(w_p),
                        "n_seeds": len(a),
                        "intact_per_seed": a.tolist(),
                        "scramble_per_seed": b.tolist()}},
                      os.path.join(args.out_dir, "paired_stats.json"))
    except Exception as e:
        print(f"Wilcoxon failed: {e}")

    print(f"\n=== Exp 3 (receiver oscillation DISABLED) summary ===")
    print(f"{'condition':10s}  {'decode':>10s}  {'γcoh':>6s}  {'δcoh':>6s}  "
          f"{'F_sr':>6s}  {'r_rate':>6s}  {'r_pow':>6s}")
    for r in summary:
        print(f"{r['condition']:10s}  "
              f"{r['decode_acc_mean']:.2f}±{r['decode_acc_se']:.2f}  "
              f"{r['gamma_coherence_mean']:.3f}  "
              f"{r['delivered_coherence_mean']:.3f}  "
              f"{r['granger_F_sr_mean']:6.1f}  "
              f"{r['receiver_rate_hz_mean']:6.1f}  "
              f"{r['receiver_gamma_power_mean']:6.2f}")


if __name__ == "__main__":
    main()
