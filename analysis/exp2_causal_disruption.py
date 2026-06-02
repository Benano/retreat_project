"""
Experiment 2 (H2): the central causal test.

At the optimal conduction delay from Experiment 1, compare three channel
conditions, holding everything else identical (same sender, same stimuli,
same seeds where possible):

  - ``intact``                — coherence preserved
  - ``phase_scramble``        — block-shuffle (rate + power preserved,
                                 coherence destroyed)
  - ``rate_matched_poisson``  — fine temporal structure destroyed,
                                 smoothed rate preserved

For each condition: ≥ n_seeds × n_stimuli trials. Headline metric is
decoding accuracy; supplementary metrics are γ-band coherence, Granger
F, and the manipulation checks (rate / power across conditions).

Saves:
  /analysis/results/exp2/<condition>/...        (per-chunk pickles + metrics)
  /analysis/results/exp2/summary.json           (per-condition aggregates)
  /figures/fig_causal_test.png                  (the headline figure)
  /figures/fig_manipulation_check.png           (rate/power/coherence checks)
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
from network import StimulusBank, FeedforwardConfig, TrialConfig, run_trial
from channels import (
    IntactChannel, PhaseScrambleChannel, RateMatchedPoissonChannel,
)
from metrics import summarize_trial, build_decoder_features, decode_stimulus
from run_utils import save_pickle, save_json, trim_trial_for_disk, run_trials_parallel


CONDITION_BUILDERS = {
    "intact":   lambda delay_ms: IntactChannel(delay_ms=delay_ms),
    "scramble": lambda delay_ms: PhaseScrambleChannel(
        algorithm="block_shuffle", block_ms=16.0, delay_ms=delay_ms),
    "poisson":  lambda delay_ms: RateMatchedPoissonChannel(
        smooth_ms=5.0, delay_ms=delay_ms),
}


def _trial_worker(args: dict) -> tuple[dict, dict]:
    cfg = PINGConfig(**args["cfg"])
    cfg_recv = PINGConfig(**args["cfg_recv"])
    bank = StimulusBank(n_stimuli=args["n_stimuli"], n_cells=cfg.N_E,
                        seed=args["bank_seed"],
                        bump_amplitude=args.get("bump_amplitude", 30.0))
    ff = FeedforwardConfig(**args["ff"])
    cond = args["condition"]
    delay_ms = args["delay_ms"]
    ch = CONDITION_BUILDERS[cond](delay_ms)
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
    trimmed = trim_trial_for_disk(out)
    row = asdict(m)
    row["condition"] = cond
    row["seed"] = args["sender_seed"] // 100
    row["stim_id"] = args["stim_id"]
    return trimmed, row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", nargs="+",
                    default=["intact", "scramble", "poisson"])
    ap.add_argument("--delay-ms", type=float, default=8.0,
                    help="Conduction delay; default = best phase from Exp 1.")
    ap.add_argument("--n-seeds", type=int, default=8)
    ap.add_argument("--n-stimuli", type=int, default=4)
    ap.add_argument("--duration-ms", type=float, default=500.0)
    ap.add_argument("--transient-ms", type=float, default=150.0)
    ap.add_argument("--bump-amplitude", type=float, default=30.0)
    ap.add_argument("--n-workers", type=int, default=4)
    ap.add_argument("--scale", choices=["dev", "full"], default="dev")
    ap.add_argument("--out-dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "results", "exp2"))
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

    # Build all trials. Use IDENTICAL (sender_seed, stim_id) pairs across
    # conditions so the sender's spike train is the same — only the channel
    # differs. This is the paired comparison the design rests on.
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

    print(f"Experiment 2 (H2 causal disruption, {args.scale} scale)")
    print(f"  conditions: {args.conditions}")
    print(f"  delay={args.delay_ms} ms, n_seeds={args.n_seeds}, n_stim={args.n_stimuli}")
    print(f"  duration={args.duration_ms} ms (transient {args.transient_ms} ms)")
    print(f"  total trials: {len(work)}, workers={args.n_workers}")

    os.makedirs(args.out_dir, exist_ok=True)
    save_json(vars(args), os.path.join(args.out_dir, "run_config.json"))

    t0 = time.time()
    results = run_trials_parallel(work, _trial_worker, n_workers=args.n_workers,
                                  progress_every=max(5, len(work) // 20))
    print(f"Trials finished in {time.time() - t0:.0f} s")

    # Save trimmed trials and metrics
    metrics_rows = []
    by_cond: dict[str, list[dict]] = {c: [] for c in args.conditions}
    for k, (trimmed, m) in enumerate(results):
        cond = work[k]["condition"]
        if k % args.n_stimuli == 0:
            save_pickle(trimmed, os.path.join(args.out_dir, cond,
                                              f"trial_{k:05d}.pkl"))
        metrics_rows.append(m)
        by_cond[cond].append(trimmed)
    save_json(metrics_rows, os.path.join(args.out_dir, "metrics_rows.json"))

    # ---- per-condition aggregation: per-seed decoder + averaged metrics ----
    # Group trials by (condition, seed). For each seed we get n_stimuli trials,
    # which is the natural unit for the decoder. Then mean ± 95% CI across seeds.
    summary = []
    for cond in args.conditions:
        trials = by_cond[cond]
        cond_rows = [r for r in metrics_rows if r["condition"] == cond]
        n_recv = trials[0]["receiver"]["config_recv"]["N_E"]

        # Decoder strategy: pool across seeds, but use seed as the CV group so
        # train/test never share a seed. Reports a single test accuracy per
        # held-out seed → n_seeds independent measurements.
        seeds_arr = np.array([t["trial"]["sender_seed"] // 100 for t in trials])
        X, y = build_decoder_features(trials, n_recv, transient_ms=args.transient_ms)

        from sklearn.model_selection import LeaveOneGroupOut
        from sklearn.linear_model import LogisticRegression
        # Standardize per trial (rate-confound control, as already done in
        # build_decoder_features → decode_stimulus). Replicate here so we can
        # use LeaveOneGroupOut directly.
        Xs = X.astype(float)
        row_mean = Xs.mean(axis=1, keepdims=True)
        row_std = Xs.std(axis=1, keepdims=True) + 1e-6
        Xs = (Xs - row_mean) / row_std
        logo = LeaveOneGroupOut()
        per_seed_acc = []
        for tr, te in logo.split(Xs, y, groups=seeds_arr):
            if len(np.unique(y[tr])) < 2:
                continue
            clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")
            clf.fit(Xs[tr], y[tr])
            per_seed_acc.append(float(clf.score(Xs[te], y[te])))
        per_seed_acc = np.array(per_seed_acc)
        decode_mean = float(np.mean(per_seed_acc)) if len(per_seed_acc) else float("nan")
        decode_se = (float(np.std(per_seed_acc, ddof=1) / np.sqrt(len(per_seed_acc)))
                     if len(per_seed_acc) > 1 else 0.0)
        decode_sd = float(np.std(per_seed_acc, ddof=1)) if len(per_seed_acc) > 1 else 0.0

        out_row = {
            "condition": cond,
            "decode_acc_mean": decode_mean,
            "decode_acc_se": decode_se,
            "decode_acc_sd": decode_sd,
            "decode_acc_per_seed": per_seed_acc.tolist(),
            "decode_chance": 1.0 / args.n_stimuli,
            "n_trials": len(trials),
            "n_seeds_used": int(len(per_seed_acc)),
        }
        for k_ in ("gamma_coherence", "delivered_coherence",
                   "granger_F_sr", "granger_F_rs",
                   "transfer_entropy",
                   "sender_rate_hz", "receiver_rate_hz", "delivered_rate_hz",
                   "sender_gamma_power", "receiver_gamma_power",
                   "delivered_gamma_power"):
            v = np.asarray([r[k_] for r in cond_rows], dtype=float)
            v = v[~np.isnan(v)]
            out_row[f"{k_}_mean"] = float(np.mean(v)) if len(v) else float("nan")
            out_row[f"{k_}_sd"] = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
            out_row[f"{k_}_n"] = int(len(v))
        summary.append(out_row)

    # Paired Wilcoxon: intact vs scramble decode per seed
    try:
        from scipy.stats import wilcoxon
        if {"intact", "scramble"}.issubset(set(args.conditions)):
            row_i = [s for s in summary if s["condition"] == "intact"][0]
            row_s = [s for s in summary if s["condition"] == "scramble"][0]
            a = np.array(row_i["decode_acc_per_seed"])
            b = np.array(row_s["decode_acc_per_seed"])
            if len(a) == len(b) and len(a) >= 3:
                w_stat, w_p = wilcoxon(a, b)
                print(f"Paired Wilcoxon intact vs scramble (per seed, n={len(a)}): "
                      f"W={w_stat:.2f}, p={w_p:.4f}")
                save_json({"test": "wilcoxon", "intact_vs_scramble":
                           {"W": float(w_stat), "p": float(w_p), "n_seeds": len(a),
                            "intact_per_seed": a.tolist(),
                            "scramble_per_seed": b.tolist()}},
                          os.path.join(args.out_dir, "paired_stats.json"))
    except Exception as e:
        print(f"Wilcoxon failed: {e}")
    save_json(summary, os.path.join(args.out_dir, "summary.json"))

    # ---- figures ----
    out_fig_dir = os.path.join(os.path.dirname(here), "figures")
    os.makedirs(out_fig_dir, exist_ok=True)

    # Headline figure: decoding accuracy by condition
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    conds = [r["condition"] for r in summary]
    accs = [r["decode_acc_mean"] for r in summary]
    se = [r["decode_acc_se"] for r in summary]
    colors = {"intact": "C0", "scramble": "C3", "poisson": "C7"}
    xs = np.arange(len(conds))
    axes[0].bar(xs, accs, yerr=[1.96 * s for s in se], capsize=5,
                color=[colors.get(c, "C5") for c in conds])
    axes[0].axhline(summary[0]["decode_chance"], ls="--", color="gray", label="chance")
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels(conds)
    axes[0].set_ylabel("Decoding accuracy (mean ± 95% CI)")
    axes[0].set_ylim(0, 1)
    axes[0].set_title("H2: stimulus decoding by channel mode")
    axes[0].legend()

    # γ coherence by condition
    gc_m = [r["gamma_coherence_mean"] for r in summary]
    gc_sd = [r["gamma_coherence_sd"] for r in summary]
    gc_n = [r["gamma_coherence_n"] for r in summary]
    gc_se = [s / np.sqrt(max(n, 1)) for s, n in zip(gc_sd, gc_n)]
    axes[1].bar(xs, gc_m, yerr=[1.96 * s for s in gc_se], capsize=5,
                color=[colors.get(c, "C5") for c in conds])
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(conds)
    axes[1].set_ylabel("γ-band coherence (mean ± 95% CI)")
    axes[1].set_ylim(0, max(gc_m) * 1.3 + 0.05)
    axes[1].set_title("Sender → receiver γ coherence")

    fig.suptitle(f"Experiment 2 — H2 causal disruption ({args.scale} scale, "
                 f"n={args.n_seeds} seeds × {args.n_stimuli} stim)",
                 fontweight="bold")
    fig.tight_layout()
    fp = os.path.join(out_fig_dir, "fig_causal_test.png")
    fig.savefig(fp, dpi=140)
    print(f"Saved {fp}")

    # Manipulation-check figure: rate / power / coherence side by side
    fig2, axes2 = plt.subplots(1, 4, figsize=(15, 4))

    def bars(ax, key, label, ylim=None):
        m = [r[f"{key}_mean"] for r in summary]
        sd = [r[f"{key}_sd"] for r in summary]
        n = [r[f"{key}_n"] for r in summary]
        se = [s / np.sqrt(max(nn, 1)) for s, nn in zip(sd, n)]
        ax.bar(xs, m, yerr=[1.96 * s for s in se], capsize=5,
               color=[colors.get(c, "C5") for c in conds])
        ax.set_xticks(xs)
        ax.set_xticklabels(conds)
        ax.set_ylabel(label)
        if ylim is not None:
            ax.set_ylim(*ylim)

    bars(axes2[0], "sender_rate_hz", "Sender E rate (Hz)")
    axes2[0].set_title("Rate (matched across)")
    bars(axes2[1], "sender_gamma_power", "Sender γ power (a.u.)")
    axes2[1].set_title("Power (matched across)")
    bars(axes2[2], "gamma_coherence", "Sender→receiver γ coh")
    axes2[2].set_title("Coherence (manipulated)")
    bars(axes2[3], "granger_F_sr", "Granger F (S→R)")
    axes2[3].set_title("Directed influence")
    fig2.suptitle("Manipulation check (intact channel should differ only in coherence)",
                  fontweight="bold")
    fig2.tight_layout()
    fp2 = os.path.join(out_fig_dir, "fig_manipulation_check.png")
    fig2.savefig(fp2, dpi=140)
    print(f"Saved {fp2}")

    # Print summary table
    print("\n=== Exp 2 summary ===")
    print(f"{'condition':10s}  {'decode':>8s}  {'γcoh':>6s}  {'F_sr':>6s}  "
          f"{'TE':>6s}  {'srate':>5s}  {'rrate':>5s}  {'spow':>5s}  {'rpow':>5s}")
    for r in summary:
        print(f"{r['condition']:10s}  "
              f"{r['decode_acc_mean']:.2f}±{r['decode_acc_se']:.2f}  "
              f"{r['gamma_coherence_mean']:.3f}  "
              f"{r['granger_F_sr_mean']:6.1f}  "
              f"{r['transfer_entropy_mean']:.3f}  "
              f"{r['sender_rate_hz_mean']:5.1f}  "
              f"{r['receiver_rate_hz_mean']:5.1f}  "
              f"{r['sender_gamma_power_mean']:.2f}  "
              f"{r['receiver_gamma_power_mean']:.2f}")


if __name__ == "__main__":
    main()
